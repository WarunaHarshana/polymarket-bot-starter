"""Paper-path executor tests (offline)."""

import os
from types import SimpleNamespace

from clob_client import ClobWrapper
from executor import DemoExecutor
from market_discovery import MarketInfo
from risk_manager import RiskManager


def _cfg(**overrides):
    base = dict(
        ENTRY_WINDOW_START_SEC=90,
        ENTRY_WINDOW_END_SEC=15,
        MIN_BUY_PRICE=0.70,
        MAX_BUY_PRICE=0.90,
        TRADE_SIZE_USD=5.0,
        JOURNAL_PATH="data/test_journal.jsonl",
        POLYMARKET_MIN_SHARES=5.0,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _market(end_time: float) -> MarketInfo:
    return MarketInfo(
        slug="btc-updown-15m-1000",
        outcomes=["Up", "Down"],
        token_ids={"Up": "demo-up", "Down": "demo-down"},
        start_time=end_time - 900,
        end_time=end_time,
    )


def test_evaluate_emits_signal_in_window(tmp_path):
    journal = tmp_path / "journal.jsonl"
    cfg = _cfg(JOURNAL_PATH=str(journal))
    risk = RiskManager(max_trades_per_round=1, trade_size_usd=5.0, min_shares=5.0)
    clob = ClobWrapper(host="https://clob.polymarket.com", dry_run=True)
    ex = DemoExecutor(cfg, risk, clob, journal_path=str(journal))

    now = 1000.0
    market = _market(end_time=now + 60)  # 60s left -> inside [15, 90]
    asks = {"Up": 0.80, "Down": 0.25}
    # TWAP above strike -> Up lead
    sig = ex.evaluate(market, twap=101.0, spot=101.0, strike=100.0, asks=asks, now=now)
    assert sig is not None
    assert sig.side == "Up"
    assert sig.ask == 0.80

    fill = ex.execute_paper(sig)
    assert fill["dry_run"] is True
    assert fill["status"] == "simulated"
    assert journal.exists()
    assert "paper_fill" in journal.read_text(encoding="utf-8")
    assert risk.trades_this_round == 1


def test_evaluate_rejects_outside_window():
    cfg = _cfg()
    risk = RiskManager()
    clob = ClobWrapper(host="https://clob.polymarket.com", dry_run=True)
    ex = DemoExecutor(cfg, risk, clob)

    now = 1000.0
    market = _market(end_time=now + 200)  # 200s left > 90
    asks = {"Up": 0.80, "Down": 0.20}
    sig = ex.evaluate(market, twap=101.0, spot=101.0, strike=100.0, asks=asks, now=now)
    assert sig is None


def test_evaluate_rejects_ask_out_of_band():
    cfg = _cfg()
    risk = RiskManager()
    clob = ClobWrapper(host="https://clob.polymarket.com", dry_run=True)
    ex = DemoExecutor(cfg, risk, clob)

    now = 1000.0
    market = _market(end_time=now + 60)
    asks = {"Up": 0.95, "Down": 0.10}  # Up ask too high
    sig = ex.evaluate(market, twap=101.0, spot=101.0, strike=100.0, asks=asks, now=now)
    assert sig is None


def test_place_market_buy_never_live_in_dry_run():
    clob = ClobWrapper(host="https://clob.polymarket.com", dry_run=True)
    assert clob._client is None
    fill = clob.place_market_buy("demo-up", 6.25, 0.80)
    assert fill["dry_run"] is True
    assert fill["order_id"].startswith("paper-")

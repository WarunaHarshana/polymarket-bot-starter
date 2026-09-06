"""Demo signal evaluation and paper execution."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from journal import append_journal
from risk_manager import RiskManager
from twap_math import in_price_band, lead_vs_strike, seconds_to_expiry

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    side: str  # "Up" or "Down"
    token_id: str
    ask: float
    size_usd: float
    shares: float
    twap: float
    strike: float
    lead: float
    tau: float
    slug: str
    reason: str = ""


class DemoExecutor:
    """
    Educational demo rule:
      - tau in [ENTRY_WINDOW_END_SEC, ENTRY_WINDOW_START_SEC]
      - TWAP lead same side as candidate
      - ask in [MIN_BUY_PRICE, MAX_BUY_PRICE]
      - risk manager allows
    """

    def __init__(
        self,
        config: Any,
        risk: RiskManager,
        clob: Any,
        journal_path: Optional[str] = None,
    ) -> None:
        self.config = config
        self.risk = risk
        self.clob = clob
        self.journal_path = journal_path or getattr(config, "JOURNAL_PATH", "data/journal.jsonl")

    def evaluate(
        self,
        market: Any,
        twap: Optional[float],
        spot: Optional[float],
        strike: Optional[float],
        asks: Dict[str, Optional[float]],
        now: Optional[float] = None,
    ) -> Optional[Signal]:
        """Return a Signal if demo entry conditions hold, else None."""
        if market is None or twap is None or strike is None:
            return None

        now_ts = time.time() if now is None else float(now)
        end_time = getattr(market, "end_time", None)
        if end_time is None:
            return None

        tau = seconds_to_expiry(end_time, now_ts)
        start_w = float(self.config.ENTRY_WINDOW_START_SEC)
        end_w = float(self.config.ENTRY_WINDOW_END_SEC)
        # tau must be in [end_w, start_w]  (e.g. 15..90 seconds left)
        if not (end_w <= tau <= start_w):
            return None

        if not self.risk.can_trade(self.config.TRADE_SIZE_USD):
            return None

        candidates = []
        for side in ("Up", "Down"):
            ask = asks.get(side)
            if ask is None:
                continue
            if not in_price_band(ask, self.config.MIN_BUY_PRICE, self.config.MAX_BUY_PRICE):
                continue
            lead = lead_vs_strike(twap, strike, side)
            if lead <= 0:
                continue
            token_id = None
            token_ids = getattr(market, "token_ids", {}) or {}
            token_id = token_ids.get(side) or token_ids.get(side.lower())
            if not token_id:
                # Demo markets may lack real tokens
                token_id = f"demo-{side.lower()}"
            shares = self.risk.shares_for_usd(self.config.TRADE_SIZE_USD, ask)
            if shares <= 0:
                continue
            candidates.append(
                Signal(
                    side=side,
                    token_id=str(token_id),
                    ask=float(ask),
                    size_usd=float(self.config.TRADE_SIZE_USD),
                    shares=float(shares),
                    twap=float(twap),
                    strike=float(strike),
                    lead=float(lead),
                    tau=float(tau),
                    slug=getattr(market, "slug", ""),
                    reason=(
                        f"tau={tau:.1f}s lead={lead:.4f} ask={ask:.4f} "
                        f"spot={spot}"
                    ),
                )
            )

        if not candidates:
            return None

        # Prefer larger absolute lead
        candidates.sort(key=lambda s: s.lead, reverse=True)
        return candidates[0]

    def execute_paper(self, signal: Signal) -> Dict[str, Any]:
        """Simulate fill via ClobWrapper dry-run path and journal it."""
        fill = self.clob.place_market_buy(
            token_id=signal.token_id,
            size_shares=signal.shares,
            worst_price=signal.ask,
            metadata={
                "side": signal.side,
                "slug": signal.slug,
                "twap": signal.twap,
                "strike": signal.strike,
                "lead": signal.lead,
                "tau": signal.tau,
                "reason": signal.reason,
            },
        )
        self.risk.register_trade()
        # Paper PnL unknown until settlement; journal notional as risk exposure only
        record = {
            "event": "paper_fill",
            "signal": {
                "side": signal.side,
                "token_id": signal.token_id,
                "ask": signal.ask,
                "shares": signal.shares,
                "size_usd": signal.size_usd,
                "slug": signal.slug,
                "twap": signal.twap,
                "strike": signal.strike,
                "lead": signal.lead,
                "tau": signal.tau,
                "reason": signal.reason,
            },
            "fill": fill,
        }
        append_journal(self.journal_path, record)
        logger.info(
            "Paper fill journaled: %s %s @ %.4f (%s shares)",
            signal.side,
            signal.slug,
            signal.ask,
            signal.shares,
        )
        return fill

"""
Polymarket BTC 15-Minute Up/Down — educational paper-trade starter.

DRY_RUN by default. No profit promises. Not financial advice.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import time
from typing import Optional

from clob_client import ClobWrapper
from config import Config
from data_feeds import PriceFeed, TwapFeed, run_binance_ticker_feed, run_rtds_chainlink_twap_feed, stop_feed
from executor import DemoExecutor
from market_discovery import MarketDiscovery, MarketInfo
from risk_manager import RiskManager

BANNER = """
================================================================================
  Polymarket BTC 15m Starter Kit — EDUCATIONAL / PAPER-TRADE FIRST
  Mode: DRY_RUN={dry_run}
  Disclaimer: Not financial advice. Trading involves risk of loss.
  No profit guarantees. Use at your own risk. Dry-run by default.
================================================================================
"""


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def make_demo_market(discovery: MarketDiscovery, now: float) -> MarketInfo:
    """Offline-friendly market stub when Gamma is unreachable."""
    bucket = discovery.get_bucket_timestamp(now)
    slug = discovery.get_market_slug(bucket)
    return MarketInfo(
        slug=slug,
        question=f"Demo {slug}",
        outcomes=["Up", "Down"],
        token_ids={"Up": "demo-up", "Down": "demo-down"},
        start_time=float(bucket),
        end_time=float(bucket + discovery.window_seconds),
    )


async def run_loop(cfg: Config) -> None:
    logger = logging.getLogger("main")
    discovery = MarketDiscovery(
        gamma_host=cfg.GAMMA_HOST,
        asset=cfg.ASSET,
        window_seconds=cfg.WINDOW_SECONDS,
    )
    risk = RiskManager(
        max_daily_loss_usd=cfg.MAX_DAILY_LOSS_USD,
        max_trades_per_round=cfg.MAX_TRADES_PER_ROUND,
        trade_size_usd=cfg.TRADE_SIZE_USD,
        min_shares=cfg.POLYMARKET_MIN_SHARES,
    )
    clob = ClobWrapper(
        host=cfg.CLOB_HOST,
        chain_id=cfg.CHAIN_ID,
        private_key=cfg.POLYMARKET_PRIVATE_KEY,
        funder=cfg.POLYMARKET_FUNDER_ADDRESS,
        signature_type=cfg.POLYMARKET_SIGNATURE_TYPE,
        dry_run=cfg.DRY_RUN,
    )
    executor = DemoExecutor(cfg, risk, clob, journal_path=cfg.JOURNAL_PATH)

    spot_feed = PriceFeed("binance")
    twap_feed = TwapFeed("rtds_twap")

    # Demo feeds so the loop starts even without live WS
    feed_tasks = [
        asyncio.create_task(
            run_binance_ticker_feed(
                spot_feed, cfg.BINANCE_WS_URL, demo_mode=True
            )
        ),
        asyncio.create_task(
            run_rtds_chainlink_twap_feed(
                twap_feed, cfg.RTDS_WS_URL, demo_mode=True
            )
        ),
    ]

    current_bucket: Optional[int] = None
    strike: Optional[float] = None

    try:
        while True:
            now = time.time()
            bucket = discovery.get_bucket_timestamp(now)
            if current_bucket != bucket:
                current_bucket = bucket
                strike = None
                risk.reset_round()
                logger.info("New round bucket=%s slug=%s", bucket, discovery.get_market_slug(bucket))
                try:
                    discovery.prefetch_next_market(now)
                except Exception as exc:
                    logger.debug("prefetch_next_market: %s", exc)

            market = discovery.get_current_market(now)
            if market is None:
                market = make_demo_market(discovery, now)
                logger.debug("Using demo market %s", market.slug)

            twap = twap_feed.price
            spot = spot_feed.price

            # Strike = first TWAP sample observed in this round (demo-friendly)
            if strike is None and twap is not None:
                strike = float(twap)
                logger.info("Strike set from first TWAP sample: %.4f", strike)

            asks = {
                "Up": clob.get_best_ask(market.up_token or "demo-up"),
                "Down": clob.get_best_ask(market.down_token or "demo-down"),
            }

            signal = executor.evaluate(market, twap, spot, strike, asks, now=now)
            if signal is not None:
                logger.info("Signal: %s", signal)
                if cfg.DRY_RUN:
                    executor.execute_paper(signal)
                else:
                    # Live path still goes through ClobWrapper (not dry)
                    fill = clob.place_market_buy(
                        signal.token_id,
                        signal.shares,
                        signal.ask,
                        metadata={"side": signal.side, "slug": signal.slug},
                    )
                    risk.register_trade()
                    logger.info("Live submit result: %s", fill)

            await asyncio.sleep(1.0)
    finally:
        stop_feed(spot_feed)
        stop_feed(twap_feed)
        for t in feed_tasks:
            t.cancel()
        await asyncio.gather(*feed_tasks, return_exceptions=True)


def main() -> None:
    setup_logging()
    cfg = Config.from_env()
    print(BANNER.format(dry_run=cfg.DRY_RUN))
    try:
        cfg.validate()
    except ValueError as exc:
        logging.error("Config validation failed: %s", exc)
        sys.exit(1)

    logging.getLogger("main").info(
        "Starting bot asset=%s window=%ss dry_run=%s",
        cfg.ASSET,
        cfg.WINDOW_SECONDS,
        cfg.DRY_RUN,
    )
    try:
        asyncio.run(run_loop(cfg))
    except KeyboardInterrupt:
        print("\nShutting down gracefully (KeyboardInterrupt).")
        logging.getLogger("main").info("Interrupted by user; exit")


if __name__ == "__main__":
    main()

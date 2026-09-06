"""
Async price / TWAP feed abstractions.

Real WebSocket wiring is sketched in comments. In demo / dry-run mode the
feeds emit synthetic updates so main.py can start without live WS connectivity.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Optional

logger = logging.getLogger(__name__)


class PriceFeed:
    """Simple last-price holder with staleness checks."""

    def __init__(self, name: str = "price") -> None:
        self.name = name
        self.last_price: Optional[float] = None
        self.last_ts: Optional[float] = None
        self._running = False

    def update(self, price: float, ts: Optional[float] = None) -> None:
        self.last_price = float(price)
        self.last_ts = time.time() if ts is None else float(ts)

    def is_stale(self, timeout: float = 5.0) -> bool:
        if self.last_ts is None:
            return True
        return (time.time() - self.last_ts) > timeout

    @property
    def price(self) -> Optional[float]:
        return self.last_price


class TwapFeed(PriceFeed):
    """TWAP-style feed; last_price is the current TWAP estimate."""

    def __init__(self, name: str = "twap") -> None:
        super().__init__(name=name)


async def run_binance_ticker_feed(
    feed: PriceFeed,
    ws_url: str,
    demo_mode: bool = True,
    base_price: float = 95000.0,
) -> None:
    """
    Subscribe to Binance BTCUSDT ticker.

    Real WS structure (documented; not required for demo):
      # import websockets, json
      # async with websockets.connect(ws_url) as ws:
      #     async for raw in ws:
      #         msg = json.loads(raw)
      #         # Binance ticker: msg["c"] is last price
      #         feed.update(float(msg["c"]))

    Falls back to synthetic random-walk updates when demo_mode or WS fails.
    """
    feed._running = True
    if not demo_mode:
        try:
            import json
            import websockets

            logger.info("Connecting Binance WS: %s", ws_url)
            async with websockets.connect(ws_url) as ws:
                async for raw in ws:
                    if not feed._running:
                        break
                    msg = json.loads(raw)
                    px = msg.get("c") or msg.get("lastPrice")
                    if px is not None:
                        feed.update(float(px))
            return
        except Exception as exc:
            logger.warning("Binance WS failed (%s); switching to synthetic feed", exc)

    logger.info("Binance feed running in synthetic/demo mode")
    price = base_price
    while feed._running:
        price *= 1.0 + random.uniform(-0.0003, 0.0003)
        feed.update(price)
        await asyncio.sleep(0.5)


async def run_rtds_chainlink_twap_feed(
    feed: TwapFeed,
    ws_url: str,
    demo_mode: bool = True,
    base_twap: float = 95000.0,
) -> None:
    """
    Placeholder for Polymarket RTDS / Chainlink TWAP stream.

    Real WS structure (documented):
      # import websockets, json
      # async with websockets.connect(ws_url) as ws:
      #     await ws.send(json.dumps({
      #         "action": "subscribe",
      #         "subscriptions": [{"topic": "crypto_prices", "type": "update", ...}],
      #     }))
      #     async for raw in ws:
      #         msg = json.loads(raw)
      #         # Extract Chainlink / TWAP field from payload and feed.update(...)

    Demo mode emits a smooth synthetic TWAP near base_twap.
    """
    feed._running = True
    if not demo_mode:
        try:
            import json
            import websockets

            logger.info("Connecting RTDS WS: %s", ws_url)
            async with websockets.connect(ws_url) as ws:
                # Subscribe payload is market/version specific; keep as stub.
                sub = {
                    "action": "subscribe",
                    "subscriptions": [
                        {"topic": "crypto_prices", "type": "*"},
                    ],
                }
                await ws.send(json.dumps(sub))
                async for raw in ws:
                    if not feed._running:
                        break
                    msg = json.loads(raw)
                    # Best-effort field sniff; real schema may differ.
                    payload = msg.get("payload") or msg.get("data") or msg
                    px = None
                    if isinstance(payload, dict):
                        px = (
                            payload.get("twap")
                            or payload.get("value")
                            or payload.get("price")
                        )
                    if px is not None:
                        feed.update(float(px))
            return
        except Exception as exc:
            logger.warning("RTDS WS failed (%s); switching to synthetic TWAP", exc)

    logger.info("RTDS/Chainlink TWAP feed running in synthetic/demo mode")
    twap = base_twap
    while feed._running:
        twap *= 1.0 + random.uniform(-0.00015, 0.00015)
        feed.update(twap)
        await asyncio.sleep(1.0)


def stop_feed(feed: PriceFeed) -> None:
    feed._running = False

"""Thin CLOB wrapper: live client only when not DRY_RUN; paper fills otherwise."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ClobWrapper:
    """
    Wraps py-clob-client for buys / book reads.
    In DRY_RUN never constructs a signing client or places live orders.
    """

    def __init__(
        self,
        host: str,
        chain_id: int = 137,
        private_key: str = "",
        funder: str = "",
        signature_type: int = 1,
        dry_run: bool = True,
    ) -> None:
        self.host = host.rstrip("/")
        self.chain_id = chain_id
        self.dry_run = dry_run
        self._client = None

        if not dry_run and private_key and funder:
            try:
                from py_clob_client.client import ClobClient

                self._client = ClobClient(
                    host,
                    key=private_key,
                    chain_id=chain_id,
                    signature_type=signature_type,
                    funder=funder,
                )
                # Derive API creds if the installed client supports it
                if hasattr(self._client, "create_or_derive_api_creds"):
                    creds = self._client.create_or_derive_api_creds()
                    if hasattr(self._client, "set_api_creds"):
                        self._client.set_api_creds(creds)
                logger.info("Live CLOB client initialized")
            except Exception as exc:
                logger.error("Failed to init live CLOB client: %s", exc)
                raise
        else:
            logger.info("ClobWrapper in DRY_RUN / no-keys mode (no signing client)")

    def get_best_ask(self, token_id: str) -> Optional[float]:
        """
        Best ask for token_id.
        Dry-run: try a public book fetch; on failure return a mock mid-band ask.
        """
        if self.dry_run or self._client is None:
            ask = self._public_best_ask(token_id)
            if ask is not None:
                return ask
            # Mock ask inside a typical educational band
            mock = 0.80
            logger.debug("DRY_RUN mock best ask for %s -> %.2f", token_id, mock)
            return mock

        try:
            book = self._client.get_order_book(token_id)
            asks = getattr(book, "asks", None) or (book.get("asks") if isinstance(book, dict) else None)
            if not asks:
                return None
            first = asks[0]
            if isinstance(first, dict):
                return float(first.get("price"))
            return float(getattr(first, "price"))
        except Exception as exc:
            logger.warning("get_best_ask failed: %s", exc)
            return None

    def _public_best_ask(self, token_id: str) -> Optional[float]:
        """Optional unauthenticated book peek (best-effort)."""
        if not token_id or token_id.startswith("demo-"):
            return None
        try:
            import requests

            url = f"{self.host}/book"
            resp = requests.get(url, params={"token_id": token_id}, timeout=5)
            if resp.status_code != 200:
                return None
            data = resp.json()
            asks = data.get("asks") or []
            if not asks:
                return None
            return float(asks[0]["price"])
        except Exception:
            return None

    def place_market_buy(
        self,
        token_id: str,
        size_shares: float,
        worst_price: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Place a market-style buy (FOK/FAK style via limit at worst_price).
        DRY_RUN: never signs; returns a simulated fill dict.
        """
        meta = metadata or {}
        if self.dry_run or self._client is None:
            fill = {
                "status": "simulated",
                "dry_run": True,
                "order_id": f"paper-{uuid.uuid4().hex[:12]}",
                "token_id": token_id,
                "side": "BUY",
                "size": float(size_shares),
                "price": float(worst_price),
                "notional_usd": float(size_shares) * float(worst_price),
                "ts": time.time(),
                **meta,
            }
            logger.info("DRY_RUN simulated fill: %s", fill)
            return fill

        # Live path — educational starter; wire to your preferred order type
        try:
            from py_clob_client.clob_types import OrderArgs, OrderType
            from py_clob_client.order_builder.constants import BUY

            args = OrderArgs(
                token_id=token_id,
                price=float(worst_price),
                size=float(size_shares),
                side=BUY,
            )
            signed = self._client.create_order(args)
            result = self._client.post_order(signed, OrderType.FOK)
            return {
                "status": "submitted",
                "dry_run": False,
                "raw": result,
                "token_id": token_id,
                "size": float(size_shares),
                "price": float(worst_price),
                **meta,
            }
        except Exception as exc:
            logger.error("Live place_market_buy failed: %s", exc)
            return {"status": "error", "dry_run": False, "error": str(exc), **meta}

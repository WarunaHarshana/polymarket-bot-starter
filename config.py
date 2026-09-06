"""Configuration loaded from environment / .env for the Polymarket BTC 15m starter."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _float(value: Optional[str], default: float) -> float:
    if value is None or value.strip() == "":
        return default
    return float(value)


def _int(value: Optional[str], default: int) -> int:
    if value is None or value.strip() == "":
        return default
    return int(value)


@dataclass
class Config:
    """Runtime settings. Dry-run by default; live trading requires keys."""

    POLYMARKET_PRIVATE_KEY: str = ""
    POLYMARKET_FUNDER_ADDRESS: str = ""
    POLYMARKET_SIGNATURE_TYPE: int = 1

    CLOB_HOST: str = "https://clob.polymarket.com"
    GAMMA_HOST: str = "https://gamma-api.polymarket.com"
    RTDS_WS_URL: str = "wss://ws-live-data.polymarket.com"
    CLOB_WS_URL: str = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
    BINANCE_WS_URL: str = "wss://stream.binance.com:9443/ws/btcusdt@ticker"

    CHAIN_ID: int = 137
    DRY_RUN: bool = True

    ASSET: str = "BTC"
    WINDOW_SECONDS: int = 900
    SETTLEMENT_LOOKBACK_SEC: int = 60

    ENTRY_WINDOW_START_SEC: int = 90
    ENTRY_WINDOW_END_SEC: int = 15

    MIN_BUY_PRICE: float = 0.70
    MAX_BUY_PRICE: float = 0.90

    TRADE_SIZE_USD: float = 5.0
    MAX_DAILY_LOSS_USD: float = 25.0
    MAX_TRADES_PER_ROUND: int = 1
    POLYMARKET_MIN_SHARES: float = 5.0

    JOURNAL_PATH: str = "data/journal.jsonl"

    @classmethod
    def from_env(cls) -> "Config":
        sig = _int(os.getenv("POLYMARKET_SIGNATURE_TYPE"), 1)
        if sig not in (1, 3):
            sig = 1
        return cls(
            POLYMARKET_PRIVATE_KEY=os.getenv("POLYMARKET_PRIVATE_KEY", "") or "",
            POLYMARKET_FUNDER_ADDRESS=os.getenv("POLYMARKET_FUNDER_ADDRESS", "") or "",
            POLYMARKET_SIGNATURE_TYPE=sig,
            CLOB_HOST=os.getenv("CLOB_HOST", "https://clob.polymarket.com"),
            GAMMA_HOST=os.getenv("GAMMA_HOST", "https://gamma-api.polymarket.com"),
            RTDS_WS_URL=os.getenv("RTDS_WS_URL", "wss://ws-live-data.polymarket.com"),
            CLOB_WS_URL=os.getenv(
                "CLOB_WS_URL",
                "wss://ws-subscriptions-clob.polymarket.com/ws/market",
            ),
            BINANCE_WS_URL=os.getenv(
                "BINANCE_WS_URL",
                "wss://stream.binance.com:9443/ws/btcusdt@ticker",
            ),
            CHAIN_ID=_int(os.getenv("CHAIN_ID"), 137),
            DRY_RUN=_bool(os.getenv("DRY_RUN"), True),
            ASSET=(os.getenv("ASSET", "BTC") or "BTC").upper(),
            WINDOW_SECONDS=_int(os.getenv("WINDOW_SECONDS"), 900),
            SETTLEMENT_LOOKBACK_SEC=_int(os.getenv("SETTLEMENT_LOOKBACK_SEC"), 60),
            ENTRY_WINDOW_START_SEC=_int(os.getenv("ENTRY_WINDOW_START_SEC"), 90),
            ENTRY_WINDOW_END_SEC=_int(os.getenv("ENTRY_WINDOW_END_SEC"), 15),
            MIN_BUY_PRICE=_float(os.getenv("MIN_BUY_PRICE"), 0.70),
            MAX_BUY_PRICE=_float(os.getenv("MAX_BUY_PRICE"), 0.90),
            TRADE_SIZE_USD=_float(os.getenv("TRADE_SIZE_USD"), 5.0),
            MAX_DAILY_LOSS_USD=_float(os.getenv("MAX_DAILY_LOSS_USD"), 25.0),
            MAX_TRADES_PER_ROUND=_int(os.getenv("MAX_TRADES_PER_ROUND"), 1),
            POLYMARKET_MIN_SHARES=_float(os.getenv("POLYMARKET_MIN_SHARES"), 5.0),
            JOURNAL_PATH=os.getenv("JOURNAL_PATH", "data/journal.jsonl"),
        )

    def validate(self) -> None:
        """Raise ValueError if live mode is missing required credentials."""
        if not self.DRY_RUN:
            if not self.POLYMARKET_PRIVATE_KEY:
                raise ValueError(
                    "POLYMARKET_PRIVATE_KEY is required when DRY_RUN=false"
                )
            if not self.POLYMARKET_FUNDER_ADDRESS:
                raise ValueError(
                    "POLYMARKET_FUNDER_ADDRESS is required when DRY_RUN=false"
                )

"""Pure math helpers for TWAP lead, z-score, price band, and expiry timing."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Union


Number = Union[int, float]
TimeLike = Union[datetime, Number]


def lead_vs_strike(twap: float, strike: float, side: str) -> float:
    """
    Signed lead of TWAP vs strike for the given side.

    Up: positive when twap > strike.
    Down: positive when twap < strike.
    """
    side_l = side.strip().lower()
    if side_l in {"up", "yes", "long"}:
        return twap - strike
    if side_l in {"down", "no", "short"}:
        return strike - twap
    raise ValueError(f"Unknown side: {side}")


def simple_zscore(value: float, mean: float, std: float) -> float:
    """Return (value - mean) / std, or 0.0 if std is non-positive."""
    if std is None or std <= 0 or math.isnan(std):
        return 0.0
    return (value - mean) / std


def in_price_band(ask: float, min_p: float, max_p: float) -> bool:
    """True if ask is within [min_p, max_p] inclusive."""
    if ask is None:
        return False
    return min_p <= ask <= max_p


def _to_epoch(t: TimeLike) -> float:
    if isinstance(t, datetime):
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return t.timestamp()
    return float(t)


def seconds_to_expiry(end_time: TimeLike, now: TimeLike) -> float:
    """Seconds remaining until end_time from now (may be negative if past)."""
    return _to_epoch(end_time) - _to_epoch(now)

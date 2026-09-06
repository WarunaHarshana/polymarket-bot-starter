"""Discover Polymarket BTC (or other) 15-minute Up/Down markets by slug."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class MarketInfo:
    """Parsed market snapshot for one 15m up/down window."""

    slug: str
    event_id: Optional[str] = None
    market_id: Optional[str] = None
    question: str = ""
    outcomes: List[str] = field(default_factory=list)
    token_ids: Dict[str, str] = field(default_factory=dict)  # Up/Down -> token
    end_time: Optional[float] = None  # unix seconds
    start_time: Optional[float] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def up_token(self) -> Optional[str]:
        return self.token_ids.get("Up") or self.token_ids.get("up")

    @property
    def down_token(self) -> Optional[str]:
        return self.token_ids.get("Down") or self.token_ids.get("down")


class MarketDiscovery:
    """Resolve current / next 15m buckets and fetch Gamma event metadata."""

    def __init__(
        self,
        gamma_host: str = "https://gamma-api.polymarket.com",
        asset: str = "BTC",
        window_seconds: int = 900,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.gamma_host = gamma_host.rstrip("/")
        self.asset = asset.lower()
        self.window_seconds = int(window_seconds)
        self._session = session or requests.Session()
        self._cache: Dict[str, MarketInfo] = {}

    def get_bucket_timestamp(self, now: Optional[float] = None) -> int:
        """Floor unix time to the current WINDOW_SECONDS bucket start."""
        ts = time.time() if now is None else float(now)
        return int(ts) // self.window_seconds * self.window_seconds

    def get_market_slug(self, bucket: Optional[int] = None, asset: Optional[str] = None) -> str:
        """Build slug like btc-updown-15m-{unix_bucket}."""
        a = (asset or self.asset).lower()
        b = self.get_bucket_timestamp() if bucket is None else int(bucket)
        return f"{a}-updown-15m-{b}"

    def fetch_market_by_slug(self, slug: str, timeout: float = 15.0) -> Optional[MarketInfo]:
        """
        GET /events?slug=... from Gamma and parse clobTokenIds + outcomes.
        Returns None if not found or parse failure.
        """
        if slug in self._cache:
            return self._cache[slug]

        url = f"{self.gamma_host}/events"
        try:
            resp = self._session.get(url, params={"slug": slug}, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("Gamma fetch failed for slug=%s: %s", slug, exc)
            return None

        events = data if isinstance(data, list) else data.get("events") or data.get("data") or []
        if not events:
            logger.info("No event for slug=%s", slug)
            return None

        event = events[0]
        markets = event.get("markets") or []
        if not markets:
            logger.warning("Event %s has no markets", slug)
            return None

        m = markets[0]
        info = self._parse_market(slug, event, m)
        if info:
            self._cache[slug] = info
        return info

    def _parse_market(
        self,
        slug: str,
        event: Dict[str, Any],
        market: Dict[str, Any],
    ) -> Optional[MarketInfo]:
        outcomes_raw = market.get("outcomes") or event.get("outcomes")
        tokens_raw = market.get("clobTokenIds") or market.get("clob_token_ids")

        outcomes = self._maybe_json_list(outcomes_raw)
        token_ids_list = self._maybe_json_list(tokens_raw)

        token_map: Dict[str, str] = {}
        if outcomes and token_ids_list and len(outcomes) == len(token_ids_list):
            for name, tid in zip(outcomes, token_ids_list):
                key = str(name).strip()
                # Normalize common labels
                if key.lower() == "up":
                    token_map["Up"] = str(tid)
                elif key.lower() == "down":
                    token_map["Down"] = str(tid)
                else:
                    token_map[key] = str(tid)
        else:
            logger.warning(
                "Could not align outcomes/tokens for %s (outcomes=%s tokens=%s)",
                slug,
                outcomes_raw,
                tokens_raw,
            )

        end_time = self._parse_time(
            market.get("endDate")
            or market.get("end_date_iso")
            or event.get("endDate")
            or event.get("end_date_iso")
        )
        start_time = self._parse_time(
            market.get("startDate")
            or market.get("eventStartTime")
            or event.get("startDate")
        )

        # Infer from slug bucket if missing
        try:
            bucket = int(slug.rsplit("-", 1)[-1])
            if start_time is None:
                start_time = float(bucket)
            if end_time is None:
                end_time = float(bucket + self.window_seconds)
        except ValueError:
            pass

        return MarketInfo(
            slug=slug,
            event_id=str(event.get("id")) if event.get("id") is not None else None,
            market_id=str(market.get("id")) if market.get("id") is not None else None,
            question=str(market.get("question") or event.get("title") or ""),
            outcomes=[str(o) for o in (outcomes or [])],
            token_ids=token_map,
            end_time=end_time,
            start_time=start_time,
            raw={"event": event, "market": market},
        )

    @staticmethod
    def _maybe_json_list(value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                return [value]
        return []

    @staticmethod
    def _parse_time(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            # ms vs s heuristic
            v = float(value)
            return v / 1000.0 if v > 1e12 else v
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return None
            try:
                return float(s)
            except ValueError:
                pass
            # ISO-8601
            try:
                from datetime import datetime, timezone

                if s.endswith("Z"):
                    s = s[:-1] + "+00:00"
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except Exception:
                return None
        return None

    def get_current_market(self, now: Optional[float] = None) -> Optional[MarketInfo]:
        """Fetch (or cache-hit) the market for the current bucket."""
        bucket = self.get_bucket_timestamp(now)
        slug = self.get_market_slug(bucket)
        return self.fetch_market_by_slug(slug)

    def prefetch_next_market(self, now: Optional[float] = None) -> Optional[MarketInfo]:
        """Fetch the next window's market and cache it."""
        bucket = self.get_bucket_timestamp(now) + self.window_seconds
        slug = self.get_market_slug(bucket)
        return self.fetch_market_by_slug(slug)

    def clear_cache(self) -> None:
        self._cache.clear()

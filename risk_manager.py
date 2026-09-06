"""Daily loss breaker and per-round trade limits."""

from __future__ import annotations

import logging
import math
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)


class RiskManager:
    """Tracks daily PnL, round trade count, and share sizing guards."""

    def __init__(
        self,
        max_daily_loss_usd: float = 25.0,
        max_trades_per_round: int = 1,
        trade_size_usd: float = 5.0,
        min_shares: float = 5.0,
    ) -> None:
        self.max_daily_loss_usd = float(max_daily_loss_usd)
        self.max_trades_per_round = int(max_trades_per_round)
        self.trade_size_usd = float(trade_size_usd)
        self.min_shares = float(min_shares)

        self._day: date = date.today()
        self.daily_pnl: float = 0.0
        self.trades_this_round: int = 0
        self._tripped: bool = False

    def _roll_day_if_needed(self) -> None:
        today = date.today()
        if today != self._day:
            logger.info("New trading day; resetting daily PnL")
            self._day = today
            self.daily_pnl = 0.0
            self._tripped = False

    def can_trade(self, size_usd: Optional[float] = None) -> bool:
        """Return True if risk limits allow another trade of size_usd."""
        self._roll_day_if_needed()
        size = self.trade_size_usd if size_usd is None else float(size_usd)

        if self._tripped:
            logger.warning("Circuit breaker open; trading halted for the day")
            return False
        if self.daily_pnl <= -abs(self.max_daily_loss_usd):
            self._tripped = True
            logger.warning(
                "Daily loss limit hit (pnl=%.2f, max_loss=%.2f)",
                self.daily_pnl,
                self.max_daily_loss_usd,
            )
            return False
        if self.trades_this_round >= self.max_trades_per_round:
            logger.debug(
                "Max trades this round reached (%s)",
                self.max_trades_per_round,
            )
            return False
        if size <= 0:
            return False
        # Projected loss if this trade goes to zero should not exceed remaining budget
        remaining = abs(self.max_daily_loss_usd) + self.daily_pnl
        if size > remaining + 1e-9:
            logger.warning(
                "Size %.2f exceeds remaining daily budget %.2f",
                size,
                remaining,
            )
            return False
        return True

    def record_pnl(self, pnl_usd: float) -> None:
        """Accumulate realized/mark PnL and trip breaker if needed."""
        self._roll_day_if_needed()
        self.daily_pnl += float(pnl_usd)
        if self.daily_pnl <= -abs(self.max_daily_loss_usd):
            self._tripped = True
            logger.warning(
                "Daily loss breaker tripped after PnL update (pnl=%.2f)",
                self.daily_pnl,
            )

    def reset_round(self) -> None:
        """Reset per-round trade counter (call on new market bucket)."""
        self.trades_this_round = 0

    def register_trade(self) -> None:
        """Increment trades_this_round after a fill."""
        self.trades_this_round += 1

    def shares_for_usd(self, usd: float, price: float) -> float:
        """
        Convert USD notional to shares at price.
        Enforces Polymarket minimum share size.
        Returns 0.0 if price invalid or resulting size below min shares.
        """
        if price is None or price <= 0 or usd is None or usd <= 0:
            return 0.0
        shares = usd / price
        if shares + 1e-12 < self.min_shares:
            # Bump to min shares if buyer can afford; else reject
            needed = self.min_shares * price
            if needed <= usd * 1.0001 or math.isclose(needed, usd, rel_tol=1e-6):
                return self.min_shares
            logger.debug(
                "Shares %.4f below min %.2f for usd=%.2f price=%.4f",
                shares,
                self.min_shares,
                usd,
                price,
            )
            return 0.0
        return shares

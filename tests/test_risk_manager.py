"""Circuit breaker and sizing tests."""

from risk_manager import RiskManager


def test_can_trade_initially():
    rm = RiskManager(max_daily_loss_usd=25.0, max_trades_per_round=1, trade_size_usd=5.0)
    assert rm.can_trade(5.0) is True


def test_max_trades_per_round():
    rm = RiskManager(max_trades_per_round=1, trade_size_usd=5.0, max_daily_loss_usd=25.0)
    assert rm.can_trade() is True
    rm.register_trade()
    assert rm.can_trade() is False
    rm.reset_round()
    assert rm.can_trade() is True


def test_daily_loss_breaker():
    rm = RiskManager(max_daily_loss_usd=25.0, max_trades_per_round=10, trade_size_usd=5.0)
    rm.record_pnl(-10.0)
    assert rm.can_trade(5.0) is True
    rm.record_pnl(-15.0)  # total -25
    assert rm.can_trade(5.0) is False
    # Stays tripped
    assert rm.can_trade(1.0) is False


def test_size_exceeds_remaining_budget():
    rm = RiskManager(max_daily_loss_usd=10.0, max_trades_per_round=5, trade_size_usd=5.0)
    rm.record_pnl(-8.0)
    assert rm.can_trade(5.0) is False
    assert rm.can_trade(2.0) is True


def test_shares_for_usd_min_guard():
    rm = RiskManager(min_shares=5.0)
    # 5 usd at 0.80 = 6.25 shares OK
    assert rm.shares_for_usd(5.0, 0.80) == 6.25
    # 3 usd at 0.80 = 3.75 < 5 and cannot afford min -> 0
    assert rm.shares_for_usd(3.0, 0.80) == 0.0
    # Invalid price
    assert rm.shares_for_usd(5.0, 0.0) == 0.0

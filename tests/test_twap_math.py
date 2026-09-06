"""Tests for twap_math pure functions."""

from datetime import datetime, timezone

from twap_math import in_price_band, lead_vs_strike, seconds_to_expiry, simple_zscore


def test_lead_vs_strike_up():
    assert lead_vs_strike(101.0, 100.0, "Up") == 1.0
    assert lead_vs_strike(99.0, 100.0, "up") == -1.0


def test_lead_vs_strike_down():
    assert lead_vs_strike(99.0, 100.0, "Down") == 1.0
    assert lead_vs_strike(101.0, 100.0, "down") == -1.0


def test_simple_zscore():
    assert simple_zscore(12, 10, 2) == 1.0
    assert simple_zscore(10, 10, 0) == 0.0
    assert simple_zscore(10, 10, -1) == 0.0


def test_in_price_band():
    assert in_price_band(0.80, 0.70, 0.90) is True
    assert in_price_band(0.70, 0.70, 0.90) is True
    assert in_price_band(0.90, 0.70, 0.90) is True
    assert in_price_band(0.69, 0.70, 0.90) is False
    assert in_price_band(0.91, 0.70, 0.90) is False


def test_seconds_to_expiry_numeric():
    assert seconds_to_expiry(1000, 900) == 100.0
    assert seconds_to_expiry(900, 1000) == -100.0


def test_seconds_to_expiry_datetime():
    end = datetime(2024, 1, 1, 12, 15, tzinfo=timezone.utc)
    now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert seconds_to_expiry(end, now) == 900.0

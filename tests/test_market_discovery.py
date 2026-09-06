"""Offline tests for bucket / slug math (no network)."""

from market_discovery import MarketDiscovery


def test_get_bucket_timestamp_floors_to_window():
    md = MarketDiscovery(window_seconds=900)
    # 1700000000 // 900 * 900
    assert md.get_bucket_timestamp(1700000000) == 1699999200
    assert md.get_bucket_timestamp(1699999200) == 1699999200
    assert md.get_bucket_timestamp(1699999200 + 899) == 1699999200
    assert md.get_bucket_timestamp(1699999200 + 900) == 1699999200 + 900


def test_get_market_slug_format():
    md = MarketDiscovery(asset="BTC", window_seconds=900)
    slug = md.get_market_slug(1699999200)
    assert slug == "btc-updown-15m-1699999200"


def test_get_market_slug_uses_asset_lower():
    md = MarketDiscovery(asset="ETH", window_seconds=900)
    assert md.get_market_slug(100) == "eth-updown-15m-100"


def test_bucket_aligns_with_slug_roundtrip():
    md = MarketDiscovery(asset="BTC", window_seconds=900)
    now = 1_700_000_123.4
    bucket = md.get_bucket_timestamp(now)
    assert bucket % 900 == 0
    assert md.get_market_slug(bucket).endswith(str(bucket))

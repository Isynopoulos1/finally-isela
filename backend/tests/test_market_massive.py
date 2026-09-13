import httpx
import pytest

from market.interface import PriceUpdate
from market.massive import BASE_URL, RATE_LIMIT_BACKOFF, MassiveProvider

SNAPSHOT = {
    "ticker": "AAPL",
    "todaysChangePerc": 0.82,
    "updated": 1_720_000_000_000_000_000,
    "lastTrade": {"p": 190.05},
    "prevDay": {"c": 188.50},
}


def client_returning(response: httpx.Response) -> httpx.AsyncClient:
    # base_url is required so _poll_once can resolve the relative SNAPSHOT_PATH
    return httpx.AsyncClient(
        base_url=BASE_URL,
        transport=httpx.MockTransport(lambda _: response),
    )


# --- _parse (pure, no network) ---------------------------------------------


def test_parse_maps_snapshot_fields():
    update = MassiveProvider._parse(SNAPSHOT, cached=None)
    assert update == PriceUpdate("AAPL", 190.05, 188.50, 0.82, 1_720_000_000.0)


def test_parse_uses_cached_price_as_prev_price():
    cached = PriceUpdate("AAPL", 189.00, 188.00, 0.3, 1.0)
    assert MassiveProvider._parse(SNAPSHOT, cached).prev_price == 189.00


def test_parse_falls_back_to_previous_close_pre_market():
    snapshot = SNAPSHOT | {"lastTrade": {}}
    assert MassiveProvider._parse(snapshot, None).price == 188.50


def test_parse_skips_entries_with_no_price():
    assert MassiveProvider._parse({"ticker": "AAPL"}, None) is None


def test_parse_skips_entries_with_no_ticker():
    assert MassiveProvider._parse({"lastTrade": {"p": 1.0}}, None) is None


def test_parse_uses_wall_clock_when_no_updated_field(monkeypatch):
    import time

    monkeypatch.setattr(time, "time", lambda: 42.0)
    snapshot = SNAPSHOT | {"updated": None}
    assert MassiveProvider._parse(snapshot, None).timestamp == 42.0


# --- _poll_once / _poll_loop transport behaviour ----------------------------


@pytest.mark.asyncio
async def test_poll_once_caches_prices():
    body = {"tickers": [SNAPSHOT]}
    provider = MassiveProvider("key")
    provider._tickers = ["AAPL"]
    async with client_returning(httpx.Response(200, json=body)) as client:
        assert await provider._poll_once(client) == provider._interval
    assert provider.get_prices()["AAPL"].price == 190.05


@pytest.mark.asyncio
async def test_poll_once_ignores_untracked_tickers():
    body = {"tickers": [SNAPSHOT]}
    provider = MassiveProvider("key")
    provider._tickers = ["MSFT"]  # AAPL not tracked
    async with client_returning(httpx.Response(200, json=body)) as client:
        await provider._poll_once(client)
    assert "AAPL" not in provider.get_prices()


@pytest.mark.asyncio
async def test_poll_once_with_no_tickers_skips_the_request():
    provider = MassiveProvider("key")

    def fail(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not make a request with no tickers")

    async with httpx.AsyncClient(transport=httpx.MockTransport(fail)) as client:
        assert await provider._poll_once(client) == provider._interval


@pytest.mark.asyncio
async def test_rate_limit_backs_off():
    provider = MassiveProvider("key")
    provider._tickers = ["AAPL"]
    async with client_returning(httpx.Response(429)) as client:
        assert await provider._poll_once(client) == RATE_LIMIT_BACKOFF


@pytest.mark.asyncio
async def test_bad_key_stops_polling():
    provider = MassiveProvider("bad")
    provider._tickers = ["AAPL"]
    async with client_returning(httpx.Response(403)) as client:
        assert await provider._poll_once(client) is None


@pytest.mark.asyncio
async def test_unauthorized_stops_polling():
    provider = MassiveProvider("bad")
    provider._tickers = ["AAPL"]
    async with client_returning(httpx.Response(401)) as client:
        assert await provider._poll_once(client) is None


@pytest.mark.asyncio
async def test_server_error_retries_at_normal_interval():
    provider = MassiveProvider("key")
    provider._tickers = ["AAPL"]
    async with client_returning(httpx.Response(500)) as client:
        assert await provider._poll_once(client) == provider._interval


@pytest.mark.asyncio
async def test_network_error_retries_at_normal_interval():
    provider = MassiveProvider("key")
    provider._tickers = ["AAPL"]

    def raise_error(request):
        raise httpx.ConnectError("boom", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(raise_error)) as client:
        assert await provider._poll_once(client) == provider._interval


@pytest.mark.asyncio
async def test_poll_loop_stops_after_bad_key(monkeypatch):
    provider = MassiveProvider("bad", interval=0)
    provider._tickers = ["AAPL"]

    # Use a self-contained fake client to avoid infinite recursion that occurs
    # when monkeypatching httpx.AsyncClient globally (client_returning also calls it).
    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, *args, **kwargs):
            return httpx.Response(403)

    import market.massive as mm

    monkeypatch.setattr(mm.httpx, "AsyncClient", lambda *a, **k: FakeClient())
    await provider._poll_loop()
    assert provider._disabled is True


# --- lifecycle --------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_prices_returns_a_copy():
    provider = MassiveProvider("key")
    provider._cache = {"AAPL": PriceUpdate("AAPL", 1.0, 1.0, 0.0, 1.0)}
    prices = provider.get_prices()
    prices["AAPL"] = None
    assert provider.get_prices()["AAPL"] is not None


@pytest.mark.asyncio
async def test_update_tickers_prunes_cache_for_removed_tickers():
    provider = MassiveProvider("key")
    provider._cache = {
        "AAPL": PriceUpdate("AAPL", 1.0, 1.0, 0.0, 1.0),
        "MSFT": PriceUpdate("MSFT", 1.0, 1.0, 0.0, 1.0),
    }
    await provider.update_tickers(["AAPL"])
    assert set(provider.get_prices()) == {"AAPL"}


@pytest.mark.asyncio
async def test_stop_before_start_is_a_noop():
    provider = MassiveProvider("key")
    await provider.stop()  # must not raise


@pytest.mark.asyncio
async def test_stop_cancels_the_running_poll_task():
    provider = MassiveProvider("key", interval=1000)
    provider._tickers = []
    provider._task = None

    import asyncio

    async def loop_forever():
        await asyncio.sleep(1000)

    provider._task = asyncio.create_task(loop_forever())
    await provider.stop()
    assert provider._task.cancelled()


def test_poll_interval_reads_env_var(monkeypatch):
    from market.massive import poll_interval

    monkeypatch.setenv("MASSIVE_POLL_INTERVAL_SECONDS", "5")
    assert poll_interval() == 5.0


def test_poll_interval_defaults_to_fifteen(monkeypatch):
    from market.massive import poll_interval

    monkeypatch.delenv("MASSIVE_POLL_INTERVAL_SECONDS", raising=False)
    assert poll_interval() == 15.0

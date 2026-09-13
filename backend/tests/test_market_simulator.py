import math
import random
import statistics

import pytest

from market.simulator import (
    ANNUAL_VOL,
    DT,
    EVENT_MAX,
    EVENT_MIN,
    MARKET_CORRELATION,
    MIN_PRICE,
    SEED_PRICES,
    SimulatorProvider,
    gbm_step,
    maybe_event,
)


def _correlation(x: list[float], y: list[float]) -> float:
    mx, my = statistics.mean(x), statistics.mean(y)
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y)) / len(x)
    return cov / (statistics.pstdev(x) * statistics.pstdev(y))


# --- gbm_step -----------------------------------------------------------


def test_gbm_keeps_prices_positive():
    price = 100.0
    for _ in range(10_000):
        price = gbm_step(price, market_z=-4.0)  # sustained crash
    assert price > 0


def test_gbm_step_distribution():
    """Per-tick log return matches sigma*sqrt(dt) when the market draw is random.

    market_z must be drawn per call: pinning it to 0.0 strips out the market
    factor and damps the observed sd by sqrt(1 - rho**2) = 0.8.
    """
    returns = [
        math.log(gbm_step(100.0, random.gauss(0, 1)) / 100.0) for _ in range(50_000)
    ]
    expected_sd = ANNUAL_VOL * math.sqrt(DT)
    assert statistics.stdev(returns) == pytest.approx(expected_sd, rel=0.05)
    assert statistics.mean(returns) == pytest.approx(0.0, abs=expected_sd)


def test_tickers_are_correlated_at_rho_squared():
    """Two tickers sharing a market draw correlate at rho**2, not rho."""
    market = [random.gauss(0, 1) for _ in range(50_000)]
    a = [math.log(gbm_step(100.0, z) / 100.0) for z in market]
    b = [math.log(gbm_step(100.0, z) / 100.0) for z in market]
    assert _correlation(a, b) == pytest.approx(MARKET_CORRELATION**2, abs=0.03)


# --- maybe_event ----------------------------------------------------------


def test_maybe_event_never_triggers_returns_same_price(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 1.0)
    assert maybe_event(100.0) == 100.0


def test_maybe_event_always_triggers_applies_bounded_shock(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 0.0)
    monkeypatch.setattr(random, "uniform", lambda a, b: EVENT_MAX)
    monkeypatch.setattr(random, "choice", lambda seq: 1)
    assert maybe_event(100.0) == pytest.approx(100.0 * (1 + EVENT_MAX))


def test_maybe_event_shock_can_be_negative(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 0.0)
    monkeypatch.setattr(random, "uniform", lambda a, b: EVENT_MIN)
    monkeypatch.setattr(random, "choice", lambda seq: -1)
    assert maybe_event(100.0) == pytest.approx(100.0 * (1 - EVENT_MIN))


# --- SimulatorProvider ------------------------------------------------------


@pytest.mark.asyncio
async def test_start_populates_cache_immediately():
    provider = SimulatorProvider()
    await provider.start(["AAPL", "MSFT"])
    try:
        prices = provider.get_prices()
        assert set(prices) == {"AAPL", "MSFT"}
        assert prices["AAPL"].price == pytest.approx(SEED_PRICES["AAPL"], rel=0.01)
    finally:
        await provider.stop()


@pytest.mark.asyncio
async def test_start_seeds_unknown_ticker_with_default_price():
    provider = SimulatorProvider()
    await provider.start(["ZZZZ"])
    try:
        assert provider.get_prices()["ZZZZ"].price == pytest.approx(100.0, rel=0.01)
    finally:
        await provider.stop()


@pytest.mark.asyncio
async def test_get_prices_returns_a_copy():
    provider = SimulatorProvider()
    await provider.start(["AAPL"])
    try:
        prices = provider.get_prices()
        prices["AAPL"] = None
        assert provider.get_prices()["AAPL"] is not None
    finally:
        await provider.stop()


@pytest.mark.asyncio
async def test_update_tickers_adds_and_prunes():
    provider = SimulatorProvider()
    await provider.start(["AAPL"])
    try:
        await provider.update_tickers(["MSFT"])
        assert set(provider.get_prices()) == {"MSFT"}
    finally:
        await provider.stop()


@pytest.mark.asyncio
async def test_update_tickers_keeps_existing_price_for_retained_ticker():
    provider = SimulatorProvider()
    await provider.start(["AAPL"])
    try:
        before = provider.get_prices()["AAPL"].price
        await provider.update_tickers(["AAPL", "MSFT"])
        after = provider.get_prices()
        assert after["AAPL"].price == before
        assert "MSFT" in after
    finally:
        await provider.stop()


@pytest.mark.asyncio
async def test_stop_is_idempotent_and_cancels_the_task():
    provider = SimulatorProvider()
    await provider.start(["AAPL"])
    await provider.stop()
    await provider.stop()
    assert provider._task.cancelled()


@pytest.mark.asyncio
async def test_stop_before_start_is_a_noop():
    provider = SimulatorProvider()
    await provider.stop()  # must not raise


def test_tick_never_produces_a_price_below_the_floor(monkeypatch):
    provider = SimulatorProvider()
    provider._prices = {"AAPL": 0.02}
    provider._closes = {"AAPL": 0.02}
    monkeypatch.setattr(random, "gauss", lambda mu, sigma: -20.0)
    provider._tick()
    assert provider.get_prices()["AAPL"].price >= MIN_PRICE


def test_tick_sets_prev_price_to_last_cached_price():
    provider = SimulatorProvider()
    provider._prices = {"AAPL": 100.0}
    provider._closes = {"AAPL": 100.0}
    provider._tick()
    first = provider.get_prices()["AAPL"].price
    provider._tick()
    second = provider.get_prices()["AAPL"]
    assert second.prev_price == first


def test_tick_change_pct_is_relative_to_pinned_close():
    provider = SimulatorProvider()
    provider._prices = {"AAPL": 100.0}
    provider._closes = {"AAPL": 200.0}
    provider._tick()
    update = provider.get_prices()["AAPL"]
    # change_pct is computed from full-precision new_price before rounding to cents,
    # so it can differ from (update.price - close) / close * 100 by up to ~0.005.
    # Use abs=0.01 to verify the close used is 200.0 (giving ~-50%), not 100.0 (giving ~0%).
    assert update.change_pct == pytest.approx(
        (update.price - 200.0) / 200.0 * 100, abs=0.01
    )

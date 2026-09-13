import pytest

from market.factory import make_provider
from market.interface import MarketDataProvider, PriceUpdate
from market.massive import MassiveProvider
from market.simulator import SimulatorProvider


def test_price_update_is_frozen():
    update = PriceUpdate("AAPL", 190.0, 189.0, 0.5, 1000.0)
    with pytest.raises(AttributeError):
        update.price = 200.0


@pytest.mark.parametrize("cls", [SimulatorProvider, MassiveProvider])
def test_providers_implement_the_interface(cls):
    assert issubclass(cls, MarketDataProvider)
    assert not getattr(cls, "__abstractmethods__", None)
    assert cls.name in {"simulator", "massive"}


def test_market_data_provider_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        MarketDataProvider()


def test_factory_selects_simulator_without_a_key(monkeypatch):
    monkeypatch.delenv("MASSIVE_API_KEY", raising=False)
    assert isinstance(make_provider(), SimulatorProvider)


@pytest.mark.parametrize("value", ["", "   "])
def test_factory_treats_blank_keys_as_absent(monkeypatch, value):
    monkeypatch.setenv("MASSIVE_API_KEY", value)
    assert isinstance(make_provider(), SimulatorProvider)


def test_factory_selects_massive_with_a_key(monkeypatch):
    monkeypatch.setenv("MASSIVE_API_KEY", "abc123")
    provider = make_provider()
    assert isinstance(provider, MassiveProvider)
    assert provider._api_key == "abc123"

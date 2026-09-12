"""Provider selection: Massive when a key is configured, simulator otherwise."""

import logging
import os

from market.interface import MarketDataProvider
from market.massive import MassiveProvider
from market.simulator import SimulatorProvider

log = logging.getLogger(__name__)


def make_provider() -> MarketDataProvider:
    """Massive when a key is configured, simulator otherwise."""
    api_key = os.getenv("MASSIVE_API_KEY", "").strip()
    if api_key:
        log.info("MASSIVE_API_KEY present — using live market data")
        return MassiveProvider(api_key)
    log.info("No MASSIVE_API_KEY — using the price simulator")
    return SimulatorProvider()

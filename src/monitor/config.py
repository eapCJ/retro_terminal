from dataclasses import dataclass
from typing import Dict, List

@dataclass
class MarketSizeCategory:
    name: str
    min_size: float
    symbol: str
    color: str
    description: str

MARKET_CATEGORIES = {
    "aquaman": MarketSizeCategory(
        "Aquaman", 10_000_000, "👑", "bright_magenta", 
        "Legendary market mover"
    ),
    "whale": MarketSizeCategory(
        "Whale", 1_000_000, "🐋", "bright_blue",
        "Major institutional trade"
    ),
    "orca": MarketSizeCategory(
        "Orca", 500_000, "🦈", "bright_cyan",
        "Large institutional trade"
    ),
    "shark": MarketSizeCategory(
        "Shark", 250_000, "🐬", "bright_green",
        "Medium institutional trade"
    ),
    "dolphin": MarketSizeCategory(
        "Dolphin", 100_000, "🐠", "bright_yellow",
        "Small institutional trade"
    ),
    "fish": MarketSizeCategory(
        "Fish", 50_000, "🐟", "bright_white",
        "Large retail trade"
    ),
    "shrimp": MarketSizeCategory(
        "Shrimp", 10_000, "🦐", "white",
        "Medium retail trade"
    ),
    "plankton": MarketSizeCategory(
        "Plankton", 0, "🦠", "dim white",
        "Small retail trade"
    ),
}

# Default trading pairs to monitor
DEFAULT_PAIRS = [
    "btcusdt",
    "ethusdt",
    "bnbusdt",
    "solusdt",
    "dogeusdt",
    "xrpusdt",
]

# Binance WebSocket endpoints
WS_ENDPOINT = "wss://stream.binance.com:9443/ws"
WS_STREAM = "stream.binance.com:9443"

# Stream types
TRADE_STREAM = "@trade"
LIQUIDATION_STREAM = "@forceOrder"  # For futures liquidations

# Minimum trade values for filtering
MIN_TRADE_VALUE = 5  # $1,000
DEFAULT_MIN_VALUE = 0  # Show all trades by default
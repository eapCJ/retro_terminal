from dataclasses import dataclass
from typing import Dict, List

@dataclass
class MarketSizeCategory:
    name: str
    min_size: float
    symbol: str
    color: str

MARKET_CATEGORIES = {
    "whale": MarketSizeCategory("Whale", 1_000_000, "◆", "bright_magenta"),
    "shark": MarketSizeCategory("Shark", 500_000, "▲", "bright_blue"),
    "dolphin": MarketSizeCategory("Dolphin", 250_000, "♦", "bright_cyan"),
    "swordfish": MarketSizeCategory("Swordfish", 100_000, "⚔", "bright_green"),
    "plankton": MarketSizeCategory("Plankton", 0, "-", "white"),
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
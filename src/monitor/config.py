from dataclasses import dataclass
from typing import Dict, List, Optional
from colorama import Fore, Back, Style

@dataclass
class SoundConfig:
    frequency: int  # Hz
    duration: int   # ms
    volume: float   # 0.0 to 1.0

@dataclass
class StyleConfig:
    text_color: str
    background_color: Optional[str] = None
    style: Optional[str] = None

@dataclass
class MarketSizeCategory:
    name: str
    min_size: float
    symbol: str
    style: StyleConfig
    sound: SoundConfig
    description: str

MARKET_CATEGORIES = {
    "aquaman": MarketSizeCategory(
        "Aquaman", 10_000_000,
        "👑",
        StyleConfig(Fore.MAGENTA, Back.WHITE, Style.BRIGHT),
        SoundConfig(1500, 300, 1.0),
        "Legendary market mover"
    ),
    "whale": MarketSizeCategory(
        "Whale", 1_000_000,
        "🐋",
        StyleConfig(Fore.BLUE, None, Style.BRIGHT),
        SoundConfig(1200, 250, 0.9),
        "Major institutional trade"
    ),
    "orca": MarketSizeCategory(
        "Orca", 500_000,
        "🦈",
        StyleConfig(Fore.CYAN, None, Style.BRIGHT),
        SoundConfig(1000, 200, 0.8),
        "Large institutional trade"
    ),
    "shark": MarketSizeCategory(
        "Shark", 250_000,
        "🐬",
        StyleConfig(Fore.GREEN, None, Style.BRIGHT),
        SoundConfig(800, 150, 0.7),
        "Medium institutional trade"
    ),
    "dolphin": MarketSizeCategory(
        "Dolphin", 100_000,
        "🐠",
        StyleConfig(Fore.YELLOW, None, Style.BRIGHT),
        SoundConfig(600, 100, 0.6),
        "Small institutional trade"
    ),
    "fish": MarketSizeCategory(
        "Fish", 50_000,
        "🐟",
        StyleConfig(Fore.WHITE, None, Style.BRIGHT),
        None,
        "Large retail trade"
    ),
    "shrimp": MarketSizeCategory(
        "Shrimp", 10_000,
        "🦐",
        StyleConfig(Fore.WHITE, None, None),
        None,
        "Medium retail trade"
    ),
    "plankton": MarketSizeCategory(
        "Plankton", 0,
        "🦠",
        StyleConfig(Fore.WHITE, None, Style.DIM),
        None,
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
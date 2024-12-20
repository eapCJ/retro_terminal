from dataclasses import dataclass
from typing import Dict, List, Optional
from colorama import Fore, Back, Style

# Add this near the top with other constants
DEFAULT_MIN_TRADE_SIZE = 0  # Default to showing all trades (plankton level)

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
    trade_sound: Optional[SoundConfig]  # Sound for regular trades
    liquidation_sound: Optional[SoundConfig]  # Sound for liquidations

MARKET_CATEGORIES = {
    "aquaman": MarketSizeCategory(
        "Aquaman", 10_000_000,
        "👑",
        StyleConfig(Fore.MAGENTA, Back.WHITE, Style.BRIGHT),
        SoundConfig(1500, 300, 1.0),  # High pitch, long duration for trades
        SoundConfig(2000, 500, 1.0),  # Even higher pitch, longer duration for liquidations
    ),
    "whale": MarketSizeCategory(
        "Whale", 1_000_000,
        "🐋",
        StyleConfig(Fore.BLUE, Back.BLACK, Style.BRIGHT),
        SoundConfig(1200, 250, 0.9),
        SoundConfig(1800, 400, 1.0),
    ),
    "orca": MarketSizeCategory(
        "Orca", 500_000,
        "🦈",
        StyleConfig(Fore.CYAN, Back.BLACK, Style.BRIGHT),
        SoundConfig(1000, 200, 0.8),
        SoundConfig(1500, 300, 0.9),
    ),
    "shark": MarketSizeCategory(
        "Shark", 250_000,
        "🐬",
        StyleConfig(Fore.GREEN, Back.BLACK, Style.BRIGHT),
        SoundConfig(800, 150, 0.7),
        SoundConfig(1200, 250, 0.8),
    ),
    "dolphin": MarketSizeCategory(
        "Dolphin", 100_000,
        "🐠",
        StyleConfig(Fore.YELLOW, Back.BLACK, Style.BRIGHT),
        SoundConfig(600, 100, 0.6),
        SoundConfig(900, 200, 0.7),
    ),
    "fish": MarketSizeCategory(
        "Fish", 50_000,
        "🐟",
        StyleConfig(Fore.WHITE, Back.BLACK, Style.BRIGHT),
        None,  # No sound for regular trades
        SoundConfig(600, 150, 0.6),  # But still alert on liquidations
    ),
    "shrimp": MarketSizeCategory(
        "Shrimp", 10_000,
        "🦐",
        StyleConfig(Fore.WHITE, Back.BLACK, None),
        None,
        None,
    ),
    "plankton": MarketSizeCategory(
        "Plankton", 0,
        "🦠",
        StyleConfig(Fore.WHITE, Back.BLACK, None),
        None,
        None,
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
WS_ENDPOINT = "wss://fstream.binance.com/ws"
WS_STREAM = "fstream.binance.com/ws"

# Stream types
TRADE_STREAM = "@trade"
LIQUIDATION_STREAM = "@forceOrder"

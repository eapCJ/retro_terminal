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
    repeat_times: int = 1  # Number of times to repeat the print

MARKET_CATEGORIES = {
    "aquaman": MarketSizeCategory(
        "Aquaman", 10_000_000,
        "★★",  # Double star - massive trades
        StyleConfig(Fore.MAGENTA, Back.WHITE, Style.BRIGHT),
        SoundConfig(1500, 300, 1.0),
        SoundConfig(2000, 500, 1.0),
        repeat_times=5  # Print 5 times for massive trades
    ),
    "whale": MarketSizeCategory(
        "Whale", 1_000_000,
        "◈◈",  # Double diamond - very large trades
        StyleConfig(Fore.BLUE, Back.BLACK, Style.BRIGHT),
        SoundConfig(1200, 250, 0.9),
        SoundConfig(1800, 400, 1.0),
        repeat_times=4  # Print 4 times for whale trades
    ),
    "orca": MarketSizeCategory(
        "Orca", 500_000,
        "◆◆",  # Double filled diamond
        StyleConfig(Fore.CYAN, Back.BLACK, Style.BRIGHT),
        SoundConfig(1000, 200, 0.8),
        SoundConfig(1500, 300, 0.9),
        repeat_times=3  # Print 3 times for orca trades
    ),
    "shark": MarketSizeCategory(
        "Shark", 250_000,
        "▲▲",  # Double triangle
        StyleConfig(Fore.GREEN, Back.BLACK, Style.BRIGHT),
        SoundConfig(800, 150, 0.7),
        SoundConfig(1200, 250, 0.8),
        repeat_times=2  # Print 2 times for shark trades
    ),
    "dolphin": MarketSizeCategory(
        "Dolphin", 100_000,
        "■■",  # Double square
        StyleConfig(Fore.YELLOW, Back.BLACK, Style.BRIGHT),
        SoundConfig(600, 100, 0.6),
        SoundConfig(900, 200, 0.7),
        repeat_times=2  # Print 2 times for dolphin trades
    ),
    "fish": MarketSizeCategory(
        "Fish", 50_000,
        "►►",  # Double arrow
        StyleConfig(Fore.WHITE, Back.BLACK, Style.BRIGHT),
        None,
        SoundConfig(600, 150, 0.6),
        repeat_times=1  # Print once for fish trades
    ),
    "shrimp": MarketSizeCategory(
        "Shrimp", 10_000,
        "▪▪",  # Double small square
        StyleConfig(Fore.WHITE, Back.BLACK, None),
        None,
        None,
        repeat_times=10  # Print once for shrimp trades
    ),
    "plankton": MarketSizeCategory(
        "Plankton", 0,
        "··",  # Double dot
        StyleConfig(Fore.WHITE, Back.BLACK, None),
        None,
        None,
        repeat_times=1  # Print once for plankton trades
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

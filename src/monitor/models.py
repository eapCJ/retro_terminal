from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from .config import MARKET_CATEGORIES

class Column(Enum):
    TYPE = "TYPE"
    SIDE = "SIDE"
    PAIR = "PAIR"
    TIME = "TIME"
    PRICE = "PRICE"
    SIZE = "SIZE"
    VALUE = "VALUE"
    CATEGORY = "CATEGORY"
    INFO = "INFO"

@dataclass
class ColumnConfig:
    name: str
    width: int
    align: str  # "left" or "right"
    format_func: Optional[str] = None  # Name of the formatting function to use

TABLE_CONFIG = {
    Column.TYPE: ColumnConfig("Type", 12, "left"),
    Column.SIDE: ColumnConfig("Side", 6, "left"),
    Column.PAIR: ColumnConfig("Pair", 8, "left"),
    Column.TIME: ColumnConfig("Time", 10, "left"),
    Column.PRICE: ColumnConfig("Price", 14, "right", "format_price"),
    Column.SIZE: ColumnConfig("Size", 14, "right", "format_quantity"),
    Column.VALUE: ColumnConfig("Value", 14, "right", "format_value"),
    Column.CATEGORY: ColumnConfig("Category", 12, "left"),
    Column.INFO: ColumnConfig("Info", 30, "left"),
}

@dataclass
class DisplayConfig:
    max_rows: int = 20  # Number of rows to display (excluding headers)
    update_interval: float = 0.1  # Seconds between screen updates
    header_style: Dict[str, Any] = None
    border_style: Dict[str, Any] = None

    def __post_init__(self):
        if self.header_style is None:
            self.header_style = {"bold": True, "fg": "cyan"}
        if self.border_style is None:
            self.border_style = {"fg": "white"}

@dataclass
class BaseTrade:
    symbol: str
    price: float
    quantity: float
    timestamp: datetime
    side: str
    
    @property
    def usd_value(self) -> float:
        return self.price * self.quantity
    
    @property
    def category(self):
        value = self.usd_value
        for cat in sorted(MARKET_CATEGORIES.values(), key=lambda x: x.min_size, reverse=True):
            if value >= cat.min_size:
                return cat
        return MARKET_CATEGORIES["plankton"]

    def to_row(self) -> Dict[Column, Any]:
        """Convert trade to a row dictionary"""
        category = self.category
        return {
            Column.TYPE: self.get_type(),
            Column.SIDE: self.side,
            Column.PAIR: self.symbol,
            Column.TIME: self.timestamp.strftime("%H:%M:%S"),
            Column.PRICE: self.price,
            Column.SIZE: self.quantity,
            Column.VALUE: self.usd_value,
            Column.CATEGORY: category.name,
            Column.INFO: f"{category.symbol} {category.description}"
        }

    def get_type(self) -> str:
        """Get the type of trade - to be overridden by subclasses"""
        return "UNKNOWN"

@dataclass
class Trade(BaseTrade):
    trade_id: str

    def get_type(self) -> str:
        return "MARKET"

@dataclass
class Liquidation(BaseTrade):
    bankruptcy_price: Optional[float] = None
    position_size: Optional[float] = None

    def get_type(self) -> str:
        return "LIQUIDATION"
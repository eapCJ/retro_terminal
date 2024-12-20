from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .config import MARKET_CATEGORIES

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

@dataclass
class Trade(BaseTrade):
    trade_id: str

@dataclass
class Liquidation(BaseTrade):
    bankruptcy_price: Optional[float] = None
    position_size: Optional[float] = None
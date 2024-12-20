import asyncio
import json
from datetime import datetime
from typing import List, Optional
import logging

import click
from rich.console import Console
from rich.live import Live
from rich.table import Table
import websockets
from websockets.exceptions import ConnectionClosed

from .config import (
    DEFAULT_PAIRS, WS_ENDPOINT, TRADE_STREAM, 
    LIQUIDATION_STREAM, WS_STREAM
)
from .models import Trade, Liquidation

console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketFeed:
    def __init__(self, max_rows=15):
        self.max_rows = max_rows
        self.trades = []
    
    def add_trade(self, trade_data: dict):
        try:
            # Binance trade data format
            timestamp = datetime.fromtimestamp(trade_data['T'] / 1000)  # Trade time
            symbol = trade_data['s'].replace('USDT', '')  # Symbol
            side = "BUY" if trade_data['m'] else "SELL"  # Market maker side (reversed)
            price = float(trade_data['p'])  # Price
            size = float(trade_data['q'])  # Quantity
            
            trade = Trade(
                symbol=symbol,
                price=price,
                quantity=size,
                timestamp=timestamp,
                side=side,
                trade_id=trade_data['t']  # Trade ID
            )
            
            self.trades.append(trade)
            if len(self.trades) > self.max_rows:
                self.trades.pop(0)
            
            return trade
        except Exception as e:
            logger.error(f"Error processing trade data: {e}")
            return None
    
    def create_table(self) -> Table:
        table = Table(
            show_header=False,
            box=None,
            padding=(0, 1),
            collapse_padding=True,
            show_edge=False,
        )
        
        # Add columns without headers
        table.add_column("Side", style="", no_wrap=True)
        table.add_column("Symbol", style="", no_wrap=True)
        table.add_column("Time", style="", no_wrap=True)
        table.add_column("Value", style="", no_wrap=True)
        table.add_column("Category", style="", no_wrap=True)
        
        for trade in reversed(self.trades):  # Reverse to show newest at top
            side_color = "green" if trade.side == "BUY" else "red"
            category = trade.category
            
            # Format the value based on size
            value = trade.usd_value
            if value >= 1_000_000:
                formatted_value = f"${value/1_000_000:.2f}M"
            elif value >= 1_000:
                formatted_value = f"${value/1_000:.2f}K"
            else:
                formatted_value = f"${value:.2f}"
            
            table.add_row(
                f"[{side_color}]{trade.side}[/{side_color}]",
                trade.symbol,
                trade.timestamp.strftime("%H:%M:%S"),
                formatted_value,
                f"[{category.color}]{category.symbol}[/{category.color}]"
            )
        
        return table

def get_stream_name(pair: str, stream_type: str) -> str:
    """Generate Binance stream name for a trading pair"""
    return f"{pair.lower()}{stream_type}"

async def monitor_market(pairs: List[str], mode: str, min_value: float = 0):
    stream_type = TRADE_STREAM if mode == "trades" else LIQUIDATION_STREAM
    
    # Create stream names for each pair
    streams = [get_stream_name(pair, stream_type) for pair in pairs]
    
    # Create subscription message
    subscribe_message = {
        "method": "SUBSCRIBE",
        "params": streams,
        "id": 1
    }
    
    feed = MarketFeed()
    retry_delay = 1  # Start with 1 second delay
    max_retry_delay = 30  # Maximum delay between retries
    
    while True:  # Outer loop for connection retry
        try:
            async with websockets.connect(WS_ENDPOINT) as ws:
                logger.info(f"Connected to Binance WebSocket")
                
                # Subscribe to streams
                await ws.send(json.dumps(subscribe_message))
                logger.info(f"Subscribed to streams: {', '.join(streams)}")
                
                retry_delay = 1  # Reset delay on successful connection
                
                with Live(feed.create_table(), refresh_per_second=4, vertical_overflow="visible") as live:
                    while True:  # Inner loop for message processing
                        try:
                            msg = await ws.recv()
                            data = json.loads(msg)
                            
                            # Skip subscription confirmation messages
                            if 'result' in data:
                                continue
                                
                            # Process trade data
                            if 'e' in data and data['e'] == 'trade':
                                trade = feed.add_trade(data)
                                if trade and trade.usd_value >= min_value:
                                    live.update(feed.create_table())
                                    
                        except ConnectionClosed:
                            logger.warning("WebSocket connection closed")
                            raise  # Re-raise to trigger reconnection
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON received: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)  # Exponential backoff

def run_async_command(coro):
    loop = asyncio.get_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@click.group()
def main():
    """Crypto market monitoring tool"""
    pass

@main.command()
@click.option("--pairs", "-p", multiple=True, default=DEFAULT_PAIRS,
              help="Trading pairs to monitor (e.g., btcusdt)")
@click.option("--min-value", "-m", default=0, help="Minimum trade value in USD")
def trades(pairs: List[str], min_value: float):
    """Monitor live trades"""
    run_async_command(monitor_market(pairs, "trades", min_value))

@main.command()
@click.option("--pairs", "-p", multiple=True, default=DEFAULT_PAIRS,
              help="Trading pairs to monitor (e.g., btcusdt)")
def liquidations(pairs: List[str]):
    """Monitor liquidations"""
    run_async_command(monitor_market(pairs, "liquidations"))

if __name__ == "__main__":
    main() 
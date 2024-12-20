import asyncio
import json
from datetime import datetime
from typing import List, Optional
import logging
import signal

import click
from rich.console import Console
import websockets
from websockets.exceptions import ConnectionClosed

from .config import (
    DEFAULT_PAIRS, WS_ENDPOINT, TRADE_STREAM, 
    LIQUIDATION_STREAM, WS_STREAM
)
from .models import Trade, Liquidation
from .printer import TradePrinter

console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketFeed:
    def __init__(self):
        self.running = True
    
    def stop(self):
        self.running = False
    
    def process_trade_message(self, msg: dict) -> Optional[Trade]:
        """Process a trade message and return a Trade object if valid"""
        try:
            if not isinstance(msg, dict):
                logger.error(f"Invalid message format: {msg}")
                return None
                
            if 'e' not in msg or msg['e'] != 'trade':
                return None
                
            if not all(k in msg for k in ['T', 's', 'm', 'p', 'q', 't']):
                logger.error(f"Missing required fields in trade message: {msg}")
                return None
            
            timestamp = datetime.fromtimestamp(int(msg['T']) / 1000)
            symbol = str(msg['s']).replace('USDT', '')
            side = "BUY" if not msg['m'] else "SELL"  # Maker side is reversed
            price = float(msg['p'])
            size = float(msg['q'])
            
            return Trade(
                symbol=symbol,
                price=price,
                quantity=size,
                timestamp=timestamp,
                side=side,
                trade_id=str(msg['t'])
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error processing trade data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing trade: {e}")
            return None
    
    def print_trade(self, trade: Trade) -> None:
        """Safely print a trade"""
        try:
            if trade is None:
                return
                
            category = trade.category
            if category is None:
                logger.error("Trade category is None")
                return
                
            TradePrinter.print_trade(
                side=trade.side,
                symbol=trade.symbol,
                timestamp=trade.timestamp,
                value=trade.usd_value,
                category_symbol=category.symbol,
                category_color=category.color
            )
        except Exception as e:
            logger.error(f"Error printing trade: {e}")

async def monitor_market(pairs: List[str], mode: str, min_value: float = 0):
    stream_type = TRADE_STREAM if mode == "trades" else LIQUIDATION_STREAM
    streams = [get_stream_name(pair, stream_type) for pair in pairs]
    
    subscribe_message = {
        "method": "SUBSCRIBE",
        "params": streams,
        "id": 1
    }
    
    feed = MarketFeed()
    retry_delay = 1
    max_retry_delay = 30
    
    def handle_signal(signum, frame):
        feed.stop()
        raise KeyboardInterrupt()
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    TradePrinter.print_header()
    TradePrinter.print_subscription(pairs)
    
    while feed.running:
        try:
            async with websockets.connect(WS_ENDPOINT) as ws:
                TradePrinter.print_connection_status("Connected to Binance WebSocket")
                await ws.send(json.dumps(subscribe_message))
                TradePrinter.print_connection_status("Subscribed to streams", ", ".join(streams))
                
                retry_delay = 1
                
                while feed.running:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        
                        if 'result' in data:  # Subscription confirmation
                            continue
                            
                        trade = feed.process_trade_message(data)
                        if trade and trade.usd_value >= min_value:
                            feed.print_trade(trade)
                            
                    except ConnectionClosed:
                        TradePrinter.print_error("WebSocket connection closed")
                        raise
                    except json.JSONDecodeError as e:
                        TradePrinter.print_error(f"Invalid JSON received: {e}")
                        continue
                    except Exception as e:
                        TradePrinter.print_error(f"Error processing message: {e}")
                        continue
                        
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            TradePrinter.print_error(f"Connection error: {e}")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)

def get_stream_name(pair: str, stream_type: str) -> str:
    """Generate Binance stream name for a trading pair"""
    return f"{pair.lower()}{stream_type}"

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
import asyncio
import json
from datetime import datetime
from typing import List, Optional
import logging
import signal
import argparse
import sys
import time
import threading
import os

import click
import websockets
from websockets.exceptions import ConnectionClosed

from .config import (
    DEFAULT_PAIRS, WS_ENDPOINT, TRADE_STREAM, 
    LIQUIDATION_STREAM, WS_STREAM, DEFAULT_MIN_TRADE_SIZE, MARKET_CATEGORIES
)
from .models import Trade, Liquidation
from .display import display
from .sound import sound_player

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketFeed:
    def __init__(self, mode: str):
        self.running = True
        self.mode = mode
    
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

    def process_liquidation_message(self, msg: dict) -> Optional[Liquidation]:
        """Process a liquidation message and return a Liquidation object if valid"""
        try:
            logger.debug(f"Received raw liquidation message: {json.dumps(msg, indent=2)}")
            
            if not isinstance(msg, dict):
                logger.error(f"Invalid message format (not a dict): {type(msg)}")
                return None
            
            # Check event type
            event_type = msg.get('e')
            if event_type != 'forceOrder':
                logger.debug(f"Skipping non-liquidation event: {event_type}")
                return None
            
            # Extract order data
            order_data = msg.get('o', {})
            if not order_data:
                logger.error("Missing order data in liquidation message")
                return None
            
            try:
                # Use order time instead of event time
                timestamp = datetime.fromtimestamp(int(order_data['T']) / 1000)
                symbol = str(order_data['s']).replace('USDT', '')
                # Reverse the side since liquidation buy means someone's sell position was liquidated
                side = "BUY" if order_data['S'] == "SELL" else "SELL"
                price = float(order_data['p'])
                size = float(order_data['q'])
                
                liquidation = Liquidation(
                    symbol=symbol,
                    price=price,
                    quantity=size,
                    timestamp=timestamp,
                    side=side,
                    bankruptcy_price=float(order_data.get('ap', 0)),
                    position_size=float(order_data.get('z', 0))
                )
                
                logger.debug(f"Successfully created liquidation object: {liquidation}")
                return liquidation
                
            except (KeyError, ValueError) as e:
                logger.error(f"Error extracting liquidation fields: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing liquidation: {e}")
            logger.exception("Full traceback:")
            return None
    
    def print_trade(self, trade: Trade) -> None:
        """Safely print a trade"""
        try:
            if trade is None:
                logger.warning("Attempted to print None trade")
                return
            logger.debug(f"Printing trade: {trade}")
            display.add_trade(trade)
            
            # Play sound only if the category has trade sound configuration
            category = trade.category
            if hasattr(category, 'trade_sound') and category.trade_sound is not None:
                # Set priority based on category (e.g., whale = 5, fish = 1)
                priority = max(1, int(trade.usd_value / 100_000))  # 1 priority point per $100k
                sound_player.play_notification(
                    frequency=category.trade_sound.frequency,
                    duration=category.trade_sound.duration,
                    volume=category.trade_sound.volume,
                    priority=priority
                )
        except Exception as e:
            logger.error(f"Error printing trade: {e}")

    def print_liquidation(self, liquidation: Liquidation) -> None:
        """Safely print a liquidation"""
        try:
            if liquidation is None:
                logger.warning("Attempted to print None liquidation")
                return
            logger.debug(f"Printing liquidation: {liquidation}")
            display.add_trade(liquidation)
            
            # Play sound only if the category has liquidation sound configuration
            category = liquidation.category
            if hasattr(category, 'liquidation_sound') and category.liquidation_sound is not None:
                # Liquidations get higher priority
                priority = max(2, int(liquidation.usd_value / 50_000))  # 1 priority point per $50k
                sound_player.play_notification(
                    frequency=category.liquidation_sound.frequency,
                    duration=category.liquidation_sound.duration,
                    volume=category.liquidation_sound.volume,
                    priority=priority
                )
        except Exception as e:
            logger.error(f"Error printing liquidation: {e}")

def get_platform_quit_key():
    """Get platform-specific quit key combination"""
    import platform
    system = platform.system().lower()
    if system == 'darwin':
        return "Cmd+C"
    elif system == 'windows':
        return "Ctrl+C or Ctrl+Break"
    else:  # Linux and others
        return "Ctrl+C"

async def monitor_market(pairs: List[str], mode: str, min_value: float = 0):
    stream_type = TRADE_STREAM if mode == "trades" else LIQUIDATION_STREAM
    streams = [
        f"{pair.lower()}{stream_type}" if mode == "trades" 
        else f"{pair.lower()}@forceOrder"
        for pair in pairs
    ]
    
    subscribe_message = {
        "method": "SUBSCRIBE",
        "params": streams,
        "id": 1
    }
    
    logger.debug(f"Subscribe message: {json.dumps(subscribe_message, indent=2)}")
    
    feed = MarketFeed(mode)
    retry_delay = 1
    max_retry_delay = 30
    ws = None
    
    # Get platform-specific quit key
    quit_key = get_platform_quit_key()
    
    def handle_signal(signum, frame):
        """Handle interrupt signals aggressively"""
        display.print_status("Shutting down...")
        logger.info("Force shutdown initiated")
        os._exit(0)  # Immediate exit without cleanup
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    if hasattr(signal, 'SIGBREAK'):  # Windows Ctrl+Break
        signal.signal(signal.SIGBREAK, handle_signal)
    
    display.update_display()  # Initial display
    display.print_status(f"Monitoring pairs: {', '.join(str(pair).upper() for pair in pairs)}")
    display.print_status(f"Press {quit_key} to quit")
    
    try:
        while feed.running:
            try:
                ws = await websockets.connect(WS_ENDPOINT)
                display.print_status("Connected to Binance WebSocket")
                await ws.send(json.dumps(subscribe_message))
                display.print_status("Subscribed to streams", ", ".join(streams))
                display.print_status(f"Press {quit_key} to quit")
                
                retry_delay = 1
                
                while feed.running:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        logger.debug(f"Received message: {data}")

                        
                        if 'result' in data:  # Subscription confirmation
                            continue
                        
                        if mode == "trades":
                            trade = feed.process_trade_message(data)
                            if trade:
                                logger.debug(f"Processed trade: {trade}")
                                if trade.usd_value >= min_value:
                                    feed.print_trade(trade)
                                    # Force display update after each trade
                                    display.update_display()
                        else:
                            liquidation = feed.process_liquidation_message(data)
                            if liquidation:
                                logger.debug(f"Processed liquidation: {liquidation}")
                                if liquidation.usd_value >= min_value:
                                    feed.print_liquidation(liquidation)
                                    # Force display update after each liquidation
                                    display.update_display()
                            
                    except ConnectionClosed:
                        display.print_error("WebSocket connection closed")
                        raise
                    except json.JSONDecodeError as e:
                        display.print_error(f"Invalid JSON received: {e}")
                        continue
                    except Exception as e:
                        display.print_error(f"Error processing message: {e}")
                        logger.exception("Error in message processing loop")
                        continue
                        
            except KeyboardInterrupt:
                display.print_status("Shutting down...")
                logger.info("Force shutdown initiated")
                os._exit(0)  # Immediate exit
            except Exception as e:
                display.print_error(f"Connection error: {e}")
                logger.exception("Error in connection loop")
                if feed.running:
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)
    finally:
        try:
            if ws:
                await ws.close()
        except Exception as e:
            logger.error(f"Error closing websocket: {e}")
        
        display.print_status("Goodbye!")
        await asyncio.sleep(1)
        os._exit(0)  # Ensure exit

def get_stream_name(pair: str, stream_type: str) -> str:
    """Generate Binance stream name for a trading pair"""
    return f"{pair.lower()}{stream_type}"

def run_async_command(coro):
    loop = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except KeyboardInterrupt:
        display.print_status("Shutting down...")
        logger.info("Force shutdown initiated")
        os._exit(0)  # Immediate exit
    except Exception:
        os._exit(1)
    finally:
        if loop and not loop.is_closed():
            loop.close()

@click.group()
def main():
    """Crypto market monitoring tool"""
    pass

@main.command()
@click.option("--pairs", "-p", multiple=True, default=DEFAULT_PAIRS,
              help="Trading pairs to monitor (e.g., btcusdt)")
@click.option("--min-size", "-m", type=float, default=DEFAULT_MIN_TRADE_SIZE,
              help="Minimum trade value in USD")
@click.option("--min-category", type=click.Choice(list(MARKET_CATEGORIES.keys())),
              help="Minimum category to monitor (e.g., whale, shark, fish)")
@click.option("--debug/--no-debug", default=False, help="Enable debug logging")
@click.option("--log-file", default=None, help="Log file path (if not specified, logging to file is disabled)")
def trades(pairs: List[str], min_size: float, min_category: str, debug: bool, log_file: Optional[str]):
    """Monitor live trades. Use Ctrl+C (Windows/Linux) or Cmd+C (Mac) to quit."""
    # Configure logging
    log_level = logging.DEBUG if debug else logging.WARNING
    log_handlers = [logging.NullHandler()]
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        log_handlers.append(file_handler)
    
    logging.basicConfig(
        level=log_level,
        handlers=log_handlers
    )
    
    # Update display settings before starting
    if min_category:
        min_size = MARKET_CATEGORIES[min_category].min_size
        display.update_settings(min_category=min_category, min_size=min_size)
    else:
        display.update_settings(min_size=min_size)
    
    run_async_command(monitor_market(pairs, "trades", min_size))

@main.command()
@click.option("--pairs", "-p", multiple=True, default=DEFAULT_PAIRS,
              help="Trading pairs to monitor (e.g., btcusdt)")
@click.option("--min-size", "-m", type=float, default=DEFAULT_MIN_TRADE_SIZE,
              help="Minimum liquidation value in USD")
@click.option("--min-category", type=click.Choice(list(MARKET_CATEGORIES.keys())),
              help="Minimum category to monitor (e.g., whale, shark, fish)")
@click.option("--debug/--no-debug", default=False, help="Enable debug logging")
@click.option("--log-file", default=None, help="Log file path (if not specified, logging to file is disabled)")
def liquidations(pairs: List[str], min_size: float, min_category: str, debug: bool, log_file: Optional[str]):
    """Monitor liquidations. Use Ctrl+C (Windows/Linux) or Cmd+C (Mac) to quit."""
    # Configure logging
    log_level = logging.DEBUG if debug else logging.WARNING
    log_handlers = [logging.NullHandler()]
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        log_handlers.append(file_handler)
    
    logging.basicConfig(
        level=log_level,
        handlers=log_handlers
    )
    
    # Update display settings before starting
    if min_category:
        min_size = MARKET_CATEGORIES[min_category].min_size
        display.update_settings(min_category=min_category, min_size=min_size)
    else:
        display.update_settings(min_size=min_size)
    
    run_async_command(monitor_market(pairs, "liquidations", min_size))

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crypto trade monitor with size-based categorization"
    )
    
    parser.add_argument(
        "-p", "--pairs",
        nargs="+",
        default=DEFAULT_PAIRS,
        help="Trading pairs to monitor (e.g., btcusdt ethusdt)"
    )
    
    parser.add_argument(
        "-m", "--min-size",
        type=float,
        default=DEFAULT_MIN_TRADE_SIZE,
        help="Minimum trade size to monitor (in USDT)"
    )
    
    parser.add_argument(
        "--min-category",
        choices=list(MARKET_CATEGORIES.keys()),
        help="Minimum category to monitor (e.g., whale, shark, fish)"
    )
    
    args = parser.parse_args()
    
    # If min-category is specified, override min-size with the category's min_size
    if args.min_category:
        args.min_size = MARKET_CATEGORIES[args.min_category].min_size
    
    return args

def get_trading_pairs() -> List[str]:
    """Get the list of trading pairs from command line arguments"""
    args = parse_args()
    return [pair.lower() for pair in args.pairs]

def get_min_trade_size() -> float:
    """Get the minimum trade size from command line arguments"""
    args = parse_args()
    return args.min_size

if __name__ == "__main__":
    main() 
import asyncio
import json
from datetime import datetime
from typing import List, Optional
import logging
import signal

import click
import websockets
from websockets.exceptions import ConnectionClosed

from .config import (
    DEFAULT_PAIRS, WS_ENDPOINT, TRADE_STREAM, 
    LIQUIDATION_STREAM, WS_STREAM
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
            if not isinstance(msg, dict):
                logger.error(f"Invalid message format: {msg}")
                return None
                
            if 'e' not in msg or msg['e'] != 'forceOrder':
                return None
                
            if not all(k in msg for k in ['T', 's', 'S', 'p', 'q']):
                logger.error(f"Missing required fields in liquidation message: {msg}")
                return None
            
            timestamp = datetime.fromtimestamp(int(msg['T']) / 1000)
            symbol = str(msg['s']).replace('USDT', '')
            side = "BUY" if msg['S'] == 'BUY' else "SELL"
            price = float(msg['p'])
            size = float(msg['q'])
            
            return Liquidation(
                symbol=symbol,
                price=price,
                quantity=size,
                timestamp=timestamp,
                side=side,
                bankruptcy_price=float(msg.get('ap', 0)),
                position_size=float(msg.get('z', 0))
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error processing liquidation data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing liquidation: {e}")
            return None
    
    def print_trade(self, trade: Trade) -> None:
        """Safely print a trade"""
        try:
            if trade is None:
                logger.warning("Attempted to print None trade")
                return
            logger.debug(f"Printing trade: {trade}")
            display.add_trade(trade)
            
            # Play sound only if the category has sound configuration
            category = trade.category
            if hasattr(category, 'sound') and category.sound is not None:
                # Set priority based on category (e.g., whale = 5, fish = 1)
                priority = max(1, int(trade.usd_value / 100_000))  # 1 priority point per $100k
                sound_player.play_notification(
                    frequency=category.sound.frequency,
                    duration=category.sound.duration,
                    volume=category.sound.volume,
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
            
            # Play sound only if the category has sound configuration
            category = liquidation.category
            if hasattr(category, 'sound') and category.sound is not None:
                # Liquidations get higher priority
                priority = max(2, int(liquidation.usd_value / 50_000))  # 1 priority point per $50k
                sound_player.play_notification(
                    frequency=category.sound.frequency,
                    duration=category.sound.duration,
                    volume=category.sound.volume,
                    priority=priority
                )
        except Exception as e:
            logger.error(f"Error printing liquidation: {e}")

async def monitor_market(pairs: List[str], mode: str, min_value: float = 0):
    stream_type = TRADE_STREAM if mode == "trades" else LIQUIDATION_STREAM
    streams = [get_stream_name(pair, stream_type) for pair in pairs]
    
    subscribe_message = {
        "method": "SUBSCRIBE",
        "params": streams,
        "id": 1
    }
    
    feed = MarketFeed(mode)
    retry_delay = 1
    max_retry_delay = 30
    ws = None
    
    def handle_signal(signum, frame):
        feed.stop()
        raise KeyboardInterrupt()
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    display.update_display()  # Initial display
    display.print_status(f"Monitoring pairs: {', '.join(str(pair).upper() for pair in pairs)}")
    
    try:
        while feed.running:
            try:
                ws = await websockets.connect(WS_ENDPOINT)
                display.print_status("Connected to Binance WebSocket")
                await ws.send(json.dumps(subscribe_message))
                display.print_status("Subscribed to streams", ", ".join(streams))
                
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
                logger.info("Shutting down...")
                break
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
        pass
    finally:
        try:
            if loop:
                tasks = asyncio.all_tasks(loop)
                for task in tasks:
                    task.cancel()
                loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()
        except Exception as e:
            logger.error(f"Error cleaning up event loop: {e}")

@click.group()
def main():
    """Crypto market monitoring tool"""
    pass

@main.command()
@click.option("--pairs", "-p", multiple=True, default=DEFAULT_PAIRS,
              help="Trading pairs to monitor (e.g., btcusdt)")
@click.option("--min-value", "-m", default=0, help="Minimum trade value in USD")
@click.option("--debug/--no-debug", default=False, help="Enable debug logging")
@click.option("--log-file", default=None, help="Log file path (if not specified, logging to file is disabled)")
def trades(pairs: List[str], min_value: float, debug: bool, log_file: Optional[str]):
    """Monitor live trades"""
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
    
    run_async_command(monitor_market(pairs, "trades", min_value))

@main.command()
@click.option("--pairs", "-p", multiple=True, default=DEFAULT_PAIRS,
              help="Trading pairs to monitor (e.g., btcusdt)")
@click.option("--debug/--no-debug", default=False, help="Enable debug logging")
@click.option("--log-file", default=None, help="Log file path (if not specified, logging to file is disabled)")
def liquidations(pairs: List[str], debug: bool, log_file: Optional[str]):
    """Monitor liquidations"""
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
    
    run_async_command(monitor_market(pairs, "liquidations"))

if __name__ == "__main__":
    main() 
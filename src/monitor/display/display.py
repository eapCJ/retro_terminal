import os
import logging
import time
from collections import deque
from threading import Lock
from typing import Any, Dict, Optional, Tuple
from colorama import Fore, Back, Style

from ..models import BaseTrade, Column, TABLE_CONFIG, DisplayConfig, ColumnConfig
from .terminal import (
    stream, clear_screen, clear_line, move_cursor,
    hide_cursor, show_cursor
)
from .styles import setup_styles
from .formatters import format_value, format_price, format_quantity

logger = logging.getLogger(__name__)

class FixedHeightDisplay:
    def __init__(self, config: DisplayConfig):
        self.config = config
        self.lock = Lock()
        self.last_update = 0
        self._get_terminal_size()
        self.trades = deque(maxlen=self.max_visible_rows)
        self.styles = setup_styles()
        self.logger = logger
        self.blink_state = {}  # Track blink state for each trade
        self.last_blink_time = time.time()
        self.blink_interval = 0.5  # Blink every 0.5 seconds
        self.last_price = {}  # Track last price for each symbol
        self.initialize_display()

    @property
    def max_visible_rows(self):
        """Calculate maximum visible rows based on terminal height"""
        # Account for:
        # - header (2 lines)
        # - column headers (2 lines)
        # - status lines (2 lines)
        # - legend (2 lines)
        # - attribution (1 line)
        # - bottom padding (2 lines)
        return max(1, self.terminal_height - 11)

    def _get_terminal_size(self):
        """Get terminal size and calculate display dimensions"""
        try:
            size = os.get_terminal_size()
            new_width = size.columns
            new_height = size.lines
            
            # Only update if size actually changed
            if new_width != getattr(self, 'terminal_width', 0) or new_height != getattr(self, 'terminal_height', 0):
                self.terminal_width = new_width
                self.terminal_height = new_height
                
                # Update table column widths based on terminal width
                self._adjust_column_widths()
                
                # Update trade buffer size if needed
                if hasattr(self, 'trades'):
                    new_deque = deque(self.trades, maxlen=self.max_visible_rows)
                    new_deque.extend(self.trades)
                    self.trades = new_deque
                    
                return True  # Size changed
            return False  # Size unchanged
        except OSError:
            # Fallback sizes
            self.terminal_width = 120
            self.terminal_height = 30
            return False

    def _adjust_column_widths(self):
        """Adjust column widths based on terminal width"""
        # Calculate total current width
        total_width = sum(config.width for config in TABLE_CONFIG.values()) + len(TABLE_CONFIG) - 1  # -1 for spaces
        
        # If terminal is too narrow, reduce some column widths
        if total_width > self.terminal_width:
            # Columns that can be shortened
            flexible_columns = [Column.INFO, Column.CATEGORY, Column.TYPE]
            
            # Calculate how much we need to reduce
            to_reduce = total_width - self.terminal_width + 5  # +5 for safety margin
            
            for col in flexible_columns:
                if to_reduce <= 0:
                    break
                current_width = TABLE_CONFIG[col].width
                # Don't reduce below minimum widths
                min_width = 8 if col == Column.INFO else 6
                reduction = min(to_reduce, current_width - min_width)
                if reduction > 0:
                    TABLE_CONFIG[col] = ColumnConfig(
                        TABLE_CONFIG[col].name,
                        current_width - reduction,
                        TABLE_CONFIG[col].align,
                        TABLE_CONFIG[col].format_func
                    )
                    to_reduce -= reduction

    def _clear_screen(self):
        """Clear the screen and reset cursor"""
        clear_screen()

    def _format_cell(self, value: Any, config: Dict[str, Any]) -> str:
        """Format a cell value according to its configuration"""
        format_func = config.get("format_func")
        if format_func:
            if format_func == "format_value":
                value = format_value(value)
            elif format_func == "format_price":
                value = format_price(value)
            elif format_func == "format_quantity":
                value = format_quantity(value)
            else:
                value = str(value)
        else:
            value = str(value)

        if config.get("align") == "right":
            return value.rjust(config["width"])
        return value.ljust(config["width"])

    def _print_header(self):
        """Print the header with box drawing characters"""
        move_cursor(1, 1)
        title = "Coins Monitor"
        header = f"{self.styles['header']}╔{'═' * (self.terminal_width - 2)}╗{self.styles['normal']}"
        move_cursor(1, 1)
        stream.write(header)
        
        # Center the title
        title_pos = max(1, (self.terminal_width - len(title)) // 2)
        move_cursor(1, title_pos)
        stream.write(f"{self.styles['header']}{title}{self.styles['normal']}")

        # Add last prices line
        move_cursor(2, 1)
        prices_text = self._format_last_prices()
        stream.write(f"{self.styles['dim']}{prices_text}{self.styles['normal']}")
        
        # Print column headers
        move_cursor(3, 1)
        header_row = ""
        remaining_width = self.terminal_width - 2
        
        for col in Column:
            config = TABLE_CONFIG[col]
            header_config = {
                "width": config.width,
                "align": config.align,
                "format_func": None
            }
            cell = self._format_cell(config.name, header_config)
            if len(header_row) + len(cell) + 1 <= remaining_width:
                header_row += cell + " "
            else:
                break
        
        stream.write(f"{self.styles['header']}{header_row.rstrip()}{self.styles['normal']}")
        
        # Print separator line
        move_cursor(4, 1)
        stream.write(f"{self.styles['border']}{'─' * (self.terminal_width - 2)}{self.styles['normal']}")

    def _format_last_prices(self) -> str:
        """Format last prices for display"""
        prices = []
        for symbol, price in self.last_price.items():
            prices.append(f"{symbol}: {format_price(price)}")
        if not prices:
            return "Waiting for price data..."
        return " | ".join(prices)

    def _should_blink(self, trade: BaseTrade) -> Tuple[bool, str]:
        """Determine if a trade should blink and get its style"""
        trade_data = trade.to_row()
        is_buy = trade_data[Column.SIDE] == "BUY"
        category = trade.category
        
        # Base colors
        base_fg = Fore.GREEN if is_buy else Fore.RED
        base_bg = Back.BLACK
        
        # Get trade ID for tracking blink state
        trade_id = id(trade)
        current_time = time.time()
        
        # Initialize blink state if not exists
        if trade_id not in self.blink_state:
            self.blink_state[trade_id] = True
        
        # Update blink states every interval
        if current_time - self.last_blink_time >= self.blink_interval:
            self.last_blink_time = current_time
            # Update all blink states
            for tid in self.blink_state:
                self.blink_state[tid] = not self.blink_state[tid]
        
        # Determine style based on trade size
        if category.min_size >= 10_000_000:  # Aquaman
            # Always blink, alternating between inverted and normal
            if self.blink_state[trade_id]:
                return True, f"{Back.GREEN if is_buy else Back.RED}{Fore.BLACK}{Style.BRIGHT}"
            else:
                return True, f"{base_fg}{base_bg}{Style.BRIGHT}"
        elif category.min_size >= 1_000_000:  # Whale
            # Blink between inverted and normal
            if self.blink_state[trade_id]:
                return True, f"{Back.GREEN if is_buy else Back.RED}{Fore.BLACK}{Style.BRIGHT}"
            else:
                return True, f"{base_fg}{base_bg}{Style.BRIGHT}"
        elif category.min_size >= 250_000:  # Shark/Orca
            # Blink between bright and normal
            if self.blink_state[trade_id]:
                return True, f"{base_fg}{base_bg}{Style.BRIGHT}"
            else:
                return True, f"{base_fg}{base_bg}"
        else:  # Smaller trades
            # No blinking
            return False, f"{base_fg}{base_bg}"

    def _print_trade_row(self, row: int, trade: BaseTrade):
        """Print a single trade row"""
        try:
            move_cursor(row, 1)
            trade_data = trade.to_row()
            
            # Get blink state and style
            should_blink, style_str = self._should_blink(trade)
            
            row_text = ""
            for col in Column:
                config = TABLE_CONFIG[col]
                value = trade_data[col]
                cell_config = {
                    "width": config.width,
                    "align": config.align,
                    "format_func": config.format_func
                }
                row_text += self._format_cell(value, cell_config) + " "
            
            # Ensure we're writing to the correct position
            clear_line(row)
            move_cursor(row, 1)
            stream.write(f"{style_str}{row_text}{self.styles['normal']}")
            stream.flush()
        except Exception as e:
            self.logger.error(f"Error in _print_trade_row: {e}")
            raise

    def add_trade(self, trade: BaseTrade):
        """Add a trade to the display and update last price"""
        try:
            with self.lock:
                self.logger.debug(f"Adding trade: {trade}")
                # Add the trade multiple times based on category
                repeat_times = trade.category.repeat_times
                for _ in range(repeat_times):
                    self.trades.append(trade)
                # Update last price for the symbol
                self.last_price[trade.symbol] = trade.price
                self.logger.debug(f"Current trades count: {len(self.trades)}")
        except Exception as e:
            self.logger.error(f"Error adding trade: {e}", exc_info=True)

    def update_display(self):
        """Update the entire display"""
        if not hasattr(self, 'trades'):
            self.logger.debug("Display not initialized")
            return

        try:
            with self.lock:
                # Check if terminal size has changed
                try:
                    current_size = os.get_terminal_size()
                    if (current_size.columns != self.terminal_width or 
                        current_size.lines != self.terminal_height):
                        self._get_terminal_size()
                        self._clear_screen()
                        self._print_header()
                except OSError:
                    pass  # Ignore terminal size errors
                
                hide_cursor()
                
                # Print trades
                start_row = 5
                visible_rows = min(len(self.trades), self.max_visible_rows)
                
                for i in range(visible_rows):
                    try:
                        clear_line(start_row + i)
                        self._print_trade_row(start_row + i, list(self.trades)[i])
                    except Exception as e:
                        self.logger.error(f"Error printing trade row {i}: {e}")
                
                # Clear any remaining lines
                for i in range(visible_rows, self.max_visible_rows):
                    clear_line(start_row + i)
                
                # Update status lines
                self._print_status_line()
                
                # Print footer only once
                self._print_footer()
                
                stream.flush()
        except Exception as e:
            self.logger.error(f"Error updating display: {e}")
        finally:
            show_cursor()

    def _print_status_line(self):
        """Print a status line showing trade count"""
        total_trades = len(self.trades)
        visible_trades = min(total_trades, self.max_visible_rows)
        status = f"Showing {visible_trades} of {total_trades} trades"
        move_cursor(self.terminal_height - 4, 1)  # Moved up to make room for attribution
        stream.write(f"{self.styles['dim']}{status}{self.styles['normal']}")

    def print_error(self, error: str):
        """Print error message at the bottom of the screen"""
        try:
            with self.lock:
                self.logger.error(error)
                clear_line(self.terminal_height - 2)  # Moved up to make room for attribution
                move_cursor(self.terminal_height - 2, 1)
                stream.write(f"{self.styles['sell']}Error: {error}{self.styles['normal']}")
                stream.flush()
        except Exception as e:
            self.logger.error(f"Error printing error message: {e}", exc_info=True)

    def print_status(self, status: str, details: Optional[str] = None):
        """Print status message at the bottom of the screen"""
        try:
            with self.lock:
                self.logger.info(f"Status: {status} {details if details else ''}")
                clear_line(self.terminal_height - 3)  # Moved up to make room for attribution
                move_cursor(self.terminal_height - 3, 1)
                if details:
                    stream.write(f"{self.styles['header']}{status}{self.styles['normal']}: {self.styles['dim']}{details}{self.styles['normal']}")
                else:
                    stream.write(f"{self.styles['header']}{status}{self.styles['normal']}")
                stream.flush()
        except Exception as e:
            self.logger.error(f"Error printing status: {e}", exc_info=True)

    def initialize_display(self):
        """Initialize the display for first time setup"""
        with self.lock:
            self._clear_screen()
            self._print_header()
            stream.flush()

    def _print_footer(self):
        """Print footer with legend and attribution"""
        # Calculate rows from bottom (including padding)
        bottom_row = self.terminal_height - 2  # Add 2 lines padding at bottom
        
        # Draw separator line
        move_cursor(bottom_row - 3, 1)
        stream.write(f"{self.styles['border']}{'─' * (self.terminal_width - 2)}{self.styles['normal']}")
        
        # Print legend in Romanian
        legend_row1 = "Simboluri: ★★10M+(x5) | ◈◈1M+(x4) | ◆◆500K+(x3) | ▲▲250K+(x2) | ■■100K+(x2) | ►►50K+ | ▪▪10K+ | ··<10K (USD)"
        legend_row2 = "Sunete: Frecvență mai înaltă & durată mai lungă = tranzacție/lichidare mai mare"
        
        # Center the legend rows
        legend1_pos = max(1, (self.terminal_width - len(legend_row1)) // 2)
        legend2_pos = max(1, (self.terminal_width - len(legend_row2)) // 2)
        
        # Print legends
        move_cursor(bottom_row - 2, legend1_pos)
        stream.write(f"{self.styles['dim']}{legend_row1}{self.styles['normal']}")
        
        move_cursor(bottom_row - 1, legend2_pos)
        stream.write(f"{self.styles['dim']}{legend_row2}{self.styles['normal']}")
        
        # Draw bottom border and attribution
        move_cursor(bottom_row, 1)
        stream.write(f"{self.styles['border']}{'─' * (self.terminal_width - 2)}{self.styles['normal']}")
        
        # Always show attribution with heart
        attribution = "Made with ❤️  by eapcj.ro"
        attr_pos = max(1, (self.terminal_width - len(attribution)) // 2)
        move_cursor(bottom_row, attr_pos)
        stream.write(f"{self.styles['dim']}{attribution}{self.styles['normal']}")
        
        # Clear bottom padding lines
        clear_line(bottom_row + 1)
        clear_line(bottom_row + 2)
  
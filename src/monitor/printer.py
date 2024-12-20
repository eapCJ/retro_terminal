import os
import sys
import time
from collections import deque
from datetime import datetime
from typing import Optional, Dict, Any, Deque
import logging
from threading import Lock

from colorama import init, Fore, Back, Style, AnsiToWin32
from .models import (
    Trade, Liquidation, BaseTrade, Column, TABLE_CONFIG, 
    DisplayConfig, ColumnConfig
)
from .sound import sound_player

# Initialize colorama
init(wrap=False)
stream = AnsiToWin32(sys.stdout).stream

# Get logger but don't configure it (will be configured by CLI)
logger = logging.getLogger(__name__)

class FixedHeightDisplay:
    def __init__(self, config: DisplayConfig):
        self.config = config
        self.lock = Lock()
        self.last_update = 0
        self._get_terminal_size()  # Initial size
        self.trades = deque(maxlen=self.max_visible_rows)  # Dynamic maxlen based on terminal size
        self._setup_styles()
        self.logger = logger
        self._clear_screen()
        self._print_header()

    @property
    def max_visible_rows(self):
        """Calculate maximum visible rows based on terminal height"""
        # Account for header (2 lines), column headers (2 lines), 
        # status lines (3 lines), and a buffer (1 line)
        return max(1, self.terminal_height - 8)

    def _get_terminal_size(self):
        """Get terminal size and calculate display dimensions"""
        try:
            size = os.get_terminal_size()
            self.terminal_width = size.columns
            self.terminal_height = size.lines
            
            # Update table column widths based on terminal width
            self._adjust_column_widths()
            
            # Update trade buffer size if needed
            if hasattr(self, 'trades'):
                new_deque = deque(self.trades, maxlen=self.max_visible_rows)
                new_deque.extend(self.trades)
                self.trades = new_deque
        except OSError:
            self.terminal_width = 120
            self.terminal_height = 30

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

    def _setup_styles(self):
        """Setup color styles"""
        self.styles = {
            "header": Fore.CYAN + Style.BRIGHT,
            "border": Fore.WHITE,
            "normal": Style.RESET_ALL,
            "dim": Style.DIM,
        }

    def _clear_screen(self):
        """Clear the screen and reset cursor"""
        # Clear screen and scroll buffer
        stream.write("\033[2J\033[3J\033[H")
        stream.flush()

    def _clear_line(self, row: int):
        """Clear a specific line"""
        self._move_cursor(row, 1)
        stream.write("\033[2K")  # Clear entire line
        stream.flush()

    def _move_cursor(self, row: int, col: int):
        """Move cursor to specific position"""
        stream.write(f"\033[{row};{col}H")
        stream.flush()

    def _hide_cursor(self):
        """Hide the cursor"""
        stream.write("\033[?25l")
        stream.flush()

    def _show_cursor(self):
        """Show the cursor"""
        stream.write("\033[?25h")
        stream.flush()

    def _format_value(self, value: float) -> str:
        """Format trade value with K/M suffix using European format"""
        try:
            if value >= 1_000_000_000:
                return f"€{value/1_000_000_000:,.2f}B".replace(",", "X").replace(".", ",").replace("X", ".")
            elif value >= 1_000_000:
                return f"€{value/1_000_000:,.2f}M".replace(",", "X").replace(".", ",").replace("X", ".")
            elif value >= 1_000:
                return f"€{value/1_000:,.2f}K".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"€{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error formatting value {value}: {e}")
            return "€0,00"

    def _format_price(self, price: float) -> str:
        """Format price with appropriate precision using European format"""
        try:
            if price >= 1000:
                return f"€{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            elif price >= 1:
                return f"€{price:.4f}".replace(".", ",")
            else:
                return f"€{price:.8f}".replace(".", ",")
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error formatting price {price}: {e}")
            return "€0,00"

    def _format_quantity(self, quantity: float) -> str:
        """Format quantity with appropriate precision"""
        return f"{quantity:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _format_cell(self, value: Any, config: Dict[str, Any]) -> str:
        """Format a cell value according to its configuration"""
        format_func = config.get("format_func")
        if format_func:
            format_method = getattr(self, f"_{format_func}", None)
            if format_method:
                value = format_method(value)
            else:
                value = str(value)
        else:
            value = str(value)

        if config.get("align") == "right":
            return value.rjust(config["width"])
        return value.ljust(config["width"])

    def _print_header(self):
        """Print the header with box drawing characters"""
        self._move_cursor(1, 1)
        title = "Crypto Market Monitor"
        header = f"{self.styles['header']}╔{'═' * (self.terminal_width - 2)}╗{self.styles['normal']}"
        self._move_cursor(1, 1)
        stream.write(header)
        
        # Center the title
        title_pos = max(1, (self.terminal_width - len(title)) // 2)
        self._move_cursor(1, title_pos)
        stream.write(f"{self.styles['header']}{title}{self.styles['normal']}")
        
        # Print column headers
        self._move_cursor(3, 1)
        header_row = ""
        remaining_width = self.terminal_width - 2  # Account for margins
        
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
        self._move_cursor(4, 1)
        stream.write(f"{self.styles['border']}{'─' * (self.terminal_width - 2)}{self.styles['normal']}")

    def _print_trade_row(self, row: int, trade: BaseTrade):
        """Print a single trade row"""
        try:
            self._move_cursor(row, 1)
            trade_data = trade.to_row()
            category = trade.category
            style = category.style
            
            # Build style string
            style_str = style.text_color
            if style.background_color:
                style_str += style.background_color
            if style.style:
                style_str += style.style
            
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
            self._clear_line(row)
            self._move_cursor(row, 1)
            stream.write(f"{style_str}{row_text}{Style.RESET_ALL}")
            stream.flush()
            
            # Play notification sound based on trade type
            sound_config = None
            if isinstance(trade, Liquidation):
                sound_config = category.liquidation_sound
            else:
                sound_config = category.trade_sound
                
            if sound_config is not None:
                sound_player.play_notification(
                    frequency=sound_config.frequency,
                    duration=sound_config.duration,
                    volume=sound_config.volume
                )
        except Exception as e:
            self.logger.error(f"Error in _print_trade_row: {e}")
            raise

    def add_trade(self, trade: BaseTrade):
        """Add a trade to the display"""
        try:
            with self.lock:
                self.logger.debug(f"Adding trade: {trade}")
                self.trades.append(trade)
                self.logger.debug(f"Current trades count: {len(self.trades)}")
        except Exception as e:
            self.logger.error(f"Error adding trade: {e}", exc_info=True)

    def update_display(self):
        """Update the entire display"""
        if not self.trades:
            self.logger.debug("No trades to display")
            return

        try:
            with self.lock:
                # Check if terminal size has changed
                current_size = os.get_terminal_size()
                if (current_size.columns != self.terminal_width or 
                    current_size.lines != self.terminal_height):
                    self._get_terminal_size()
                
                self._hide_cursor()
                self._clear_screen()
                self._print_header()
                
                # Print trades
                start_row = 5
                visible_rows = min(len(self.trades), self.max_visible_rows)
                
                for i in range(visible_rows):
                    try:
                        self._clear_line(start_row + i)
                        self._print_trade_row(start_row + i, list(self.trades)[i])
                    except Exception as e:
                        self.logger.error(f"Error printing trade row {i}: {e}", exc_info=True)
                
                # Clear any remaining lines
                for i in range(visible_rows, self.max_visible_rows):
                    self._clear_line(start_row + i)
                
                # Always show status at the bottom
                self._print_status_line()
                
                stream.flush()
        except Exception as e:
            self.logger.error(f"Error updating display: {e}", exc_info=True)
        finally:
            self._show_cursor()

    def _print_status_line(self):
        """Print a status line showing trade count"""
        total_trades = len(self.trades)
        visible_trades = min(total_trades, self.max_visible_rows)
        status = f"Showing {visible_trades} of {total_trades} trades"
        self._move_cursor(self.terminal_height - 3, 1)
        stream.write(f"{self.styles['dim']}{status}{self.styles['normal']}")

    def print_error(self, error: str):
        """Print error message at the bottom of the screen"""
        try:
            with self.lock:
                self.logger.error(error)
                self._clear_line(self.terminal_height - 1)
                self._move_cursor(self.terminal_height - 1, 1)
                stream.write(f"{Fore.RED}Error: {error}{Style.RESET_ALL}")
                stream.flush()
        except Exception as e:
            self.logger.error(f"Error printing error message: {e}", exc_info=True)

    def print_status(self, status: str, details: Optional[str] = None):
        """Print status message at the bottom of the screen"""
        try:
            with self.lock:
                self.logger.info(f"Status: {status} {details if details else ''}")
                self._clear_line(self.terminal_height - 2)
                self._move_cursor(self.terminal_height - 2, 1)
                if details:
                    stream.write(f"{Fore.BLUE}{status}{Style.RESET_ALL}: {Style.DIM}{details}{Style.RESET_ALL}")
                else:
                    stream.write(f"{Fore.BLUE}{status}{Style.RESET_ALL}")
                stream.flush()
        except Exception as e:
            self.logger.error(f"Error printing status: {e}", exc_info=True)

# Create a global display instance
display = FixedHeightDisplay(DisplayConfig())
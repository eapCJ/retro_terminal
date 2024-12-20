import os
import logging
from collections import deque
from threading import Lock
from typing import Any, Dict, Optional

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
        self.initialize_display()

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
        title = "Crypto Market Monitor"
        header = f"{self.styles['header']}╔{'═' * (self.terminal_width - 2)}╗{self.styles['normal']}"
        move_cursor(1, 1)
        stream.write(header)
        
        # Center the title
        title_pos = max(1, (self.terminal_width - len(title)) // 2)
        move_cursor(1, title_pos)
        stream.write(f"{self.styles['header']}{title}{self.styles['normal']}")
        
        # Print column headers
        move_cursor(3, 1)
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
        move_cursor(4, 1)
        stream.write(f"{self.styles['border']}{'─' * (self.terminal_width - 2)}{self.styles['normal']}")

    def _print_trade_row(self, row: int, trade: BaseTrade):
        """Print a single trade row"""
        try:
            move_cursor(row, 1)
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
            clear_line(row)
            move_cursor(row, 1)
            stream.write(f"{style_str}{row_text}{self.styles['normal']}")
            stream.flush()
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
                    self._clear_screen()
                    self._print_header()
                
                hide_cursor()
                
                # Print trades without clearing the whole screen
                start_row = 5
                visible_rows = min(len(self.trades), self.max_visible_rows)
                
                for i in range(visible_rows):
                    try:
                        # Only clear the specific line we're about to update
                        clear_line(start_row + i)
                        self._print_trade_row(start_row + i, list(self.trades)[i])
                    except Exception as e:
                        self.logger.error(f"Error printing trade row {i}: {e}", exc_info=True)
                
                # Clear any remaining lines
                for i in range(visible_rows, self.max_visible_rows):
                    clear_line(start_row + i)
                
                # Update status lines
                self._print_status_line()
                
                stream.flush()
        except Exception as e:
            self.logger.error(f"Error updating display: {e}", exc_info=True)
        finally:
            show_cursor()

    def _print_status_line(self):
        """Print a status line showing trade count"""
        total_trades = len(self.trades)
        visible_trades = min(total_trades, self.max_visible_rows)
        status = f"Showing {visible_trades} of {total_trades} trades"
        move_cursor(self.terminal_height - 3, 1)
        stream.write(f"{self.styles['dim']}{status}{self.styles['normal']}")

    def print_error(self, error: str):
        """Print error message at the bottom of the screen"""
        try:
            with self.lock:
                self.logger.error(error)
                clear_line(self.terminal_height - 1)
                move_cursor(self.terminal_height - 1, 1)
                stream.write(f"{self.styles['sell']}Error: {error}{self.styles['normal']}")
                stream.flush()
        except Exception as e:
            self.logger.error(f"Error printing error message: {e}", exc_info=True)

    def print_status(self, status: str, details: Optional[str] = None):
        """Print status message at the bottom of the screen"""
        try:
            with self.lock:
                self.logger.info(f"Status: {status} {details if details else ''}")
                clear_line(self.terminal_height - 2)
                move_cursor(self.terminal_height - 2, 1)
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
  
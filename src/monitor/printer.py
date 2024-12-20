import os
import sys
import time
from collections import deque
from datetime import datetime
from typing import Optional, Dict, Any, Deque
import logging
from threading import Lock

from colorama import init, Fore, Back, Style, AnsiToWin32
from .models import Trade, Liquidation, BaseTrade, Column, TABLE_CONFIG, DisplayConfig

# Initialize colorama
init(wrap=False)
stream = AnsiToWin32(sys.stdout).stream

# Get logger but don't configure it (will be configured by CLI)
logger = logging.getLogger(__name__)

class FixedHeightDisplay:
    def __init__(self, config: DisplayConfig):
        self.config = config
        self.trades: Deque[BaseTrade] = deque(maxlen=config.max_rows)
        self.lock = Lock()
        self.last_update = 0
        self._get_terminal_size()
        self._setup_styles()
        # Initialize logging
        self.logger = logger  # Use the module-level logger
        # Ensure the screen is cleared on startup
        self._clear_screen()
        self._print_header()

    def _get_terminal_size(self):
        """Get terminal size and calculate display dimensions"""
        try:
            self.terminal_width = os.get_terminal_size().columns
            self.terminal_height = os.get_terminal_size().lines
        except OSError:
            self.terminal_width = 120
            self.terminal_height = 30

    def _setup_styles(self):
        """Setup color styles"""
        self.styles = {
            "header": Fore.CYAN + Style.BRIGHT,
            "border": Fore.WHITE,
            "buy": Fore.GREEN + Style.BRIGHT,
            "sell": Fore.RED + Style.BRIGHT,
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
        header = f"{self.styles['header']}╔══ Crypto Market Monitor ══╗{self.styles['normal']}"
        self._move_cursor(1, (self.terminal_width - len("Crypto Market Monitor") - 6) // 2)
        stream.write(header)
        
        # Print column headers
        self._move_cursor(3, 1)
        header_row = ""
        for col in Column:
            config = TABLE_CONFIG[col]
            header_config = {
                "width": config.width,
                "align": config.align,
                "format_func": None  # Headers don't need formatting
            }
            header_row += self._format_cell(config.name, header_config) + " "
        stream.write(f"{self.styles['header']}{header_row}{self.styles['normal']}")
        
        # Print separator line
        self._move_cursor(4, 1)
        stream.write(f"{self.styles['border']}{'─' * (self.terminal_width - 2)}{self.styles['normal']}")

    def _print_trade_row(self, row: int, trade: BaseTrade):
        """Print a single trade row"""
        try:
            self._move_cursor(row, 1)
            trade_data = trade.to_row()
            row_style = self.styles["buy"] if trade_data[Column.SIDE] == "BUY" else self.styles["sell"]
            
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
            stream.write(f"{row_style}{row_text}{self.styles['normal']}")
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
                self._hide_cursor()
                self._get_terminal_size()
                self._clear_screen()
                self._print_header()
                
                # Print trades
                start_row = 5
                self.logger.debug(f"Updating display with {len(self.trades)} trades")
                
                for i, trade in enumerate(list(self.trades)):
                    if i >= self.config.max_rows:
                        break
                    try:
                        # Clear the line before printing
                        self._clear_line(start_row + i)
                        self._print_trade_row(start_row + i, trade)
                    except Exception as e:
                        self.logger.error(f"Error printing trade row {i}: {e}", exc_info=True)
                
                # Clear any remaining lines
                for i in range(len(self.trades), self.config.max_rows):
                    self._clear_line(start_row + i)
                
                # Always show status at the bottom
                self._print_status_line()
                
                # Ensure everything is flushed to the terminal
                stream.flush()
        except Exception as e:
            self.logger.error(f"Error updating display: {e}", exc_info=True)
        finally:
            self._show_cursor()

    def _print_status_line(self):
        """Print a status line showing trade count"""
        status = f"Monitoring {len(self.trades)} trades"
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

# Create a global display instance with faster updates
display = FixedHeightDisplay(DisplayConfig(
    max_rows=20,
    update_interval=0.1  # 100ms update interval
))
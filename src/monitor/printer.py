from datetime import datetime
from typing import Optional
import logging

from rich.console import Console
from rich.style import Style

# Single console instance
console = Console()
logger = logging.getLogger(__name__)

class TradePrinter:
    @staticmethod
    def _format_value(value: float) -> str:
        """Format trade value with K/M suffix"""
        try:
            if value >= 1_000_000:
                return f"${value/1_000_000:.2f}M"
            elif value >= 1_000:
                return f"${value/1_000:.2f}K"
            return f"${value:.2f}"
        except (TypeError, ValueError) as e:
            logger.error(f"Error formatting value {value}: {e}")
            return "$0.00"

    @staticmethod
    def _get_side_style(side: str) -> Style:
        """Get style for trade side"""
        try:
            return Style(color="green" if side == "BUY" else "red", bold=True)
        except Exception as e:
            logger.error(f"Error creating style for side {side}: {e}")
            return Style()

    @staticmethod
    def print_trade(
        side: str,
        symbol: str,
        timestamp: datetime,
        value: float,
        category_symbol: str,
        category_color: str
    ) -> None:
        """Print a single trade with formatting on a single line"""
        try:
            # Validate inputs
            if not all([side, symbol, timestamp, category_symbol, category_color]):
                logger.error("Missing required trade information")
                return
            
            # Format components
            time_str = timestamp.strftime("%H:%M:%S")
            value_str = TradePrinter._format_value(value)
            side_style = TradePrinter._get_side_style(side)
            category_style = Style(color=category_color, bold=True)
            
            # Print everything on one line with end="\n"
            console.print(
                f"{side.ljust(4)} {symbol.ljust(5)} {time_str} {value_str.rjust(10)} {category_symbol}",
                style=side_style,
                highlight=False,
                end="\n"
            )
        except Exception as e:
            logger.error(f"Error printing trade: {e}")

    @staticmethod
    def print_header() -> None:
        """Print header information"""
        try:
            console.print("\n[bold]Crypto Market Monitor[/bold] - Press Ctrl+C to exit\n")
        except Exception as e:
            logger.error(f"Error printing header: {e}")

    @staticmethod
    def print_subscription(pairs: list) -> None:
        """Print subscription information"""
        try:
            if not pairs:
                return
            pairs_str = ", ".join(str(pair).upper() for pair in pairs)
            console.print(f"[dim]Monitoring pairs: {pairs_str}[/dim]\n")
        except Exception as e:
            logger.error(f"Error printing subscription info: {e}")

    @staticmethod
    def print_error(error: str) -> None:
        """Print error message"""
        try:
            console.print(f"[red]Error: {error}[/red]")
        except Exception as e:
            logger.error(f"Error printing error message: {e}")

    @staticmethod
    def print_connection_status(status: str, details: Optional[str] = None) -> None:
        """Print connection status"""
        try:
            if details:
                console.print(f"[blue]{status}[/blue]: [dim]{details}[/dim]")
            else:
                console.print(f"[blue]{status}[/blue]")
        except Exception as e:
            logger.error(f"Error printing connection status: {e}") 
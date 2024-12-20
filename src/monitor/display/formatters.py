import logging

logger = logging.getLogger(__name__)

def format_value(value: float) -> str:
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
        logger.error(f"Error formatting value {value}: {e}")
        return "€0,00"

def format_price(price: float) -> str:
    """Format price with appropriate precision using European format"""
    try:
        if price >= 1000:
            return f"€{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        elif price >= 1:
            return f"€{price:.4f}".replace(".", ",")
        else:
            return f"€{price:.8f}".replace(".", ",")
    except (TypeError, ValueError) as e:
        logger.error(f"Error formatting price {price}: {e}")
        return "€0,00"

def format_quantity(quantity: float) -> str:
    """Format quantity with appropriate precision"""
    return f"{quantity:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".") 
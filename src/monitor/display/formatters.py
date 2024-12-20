import logging

logger = logging.getLogger(__name__)

def format_value(value: float) -> str:
    """Format trade value using European format"""
    try:
        return f"€{int(value):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError) as e:
        logger.error(f"Error formatting value {value}: {e}")
        return "€0"

def format_price(price: float) -> str:
    """Format price with appropriate precision using European format"""
    try:
        return f"€{int(price):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError) as e:
        logger.error(f"Error formatting price {price}: {e}")
        return "€0"

def format_quantity(quantity: float) -> str:
    """Format quantity with appropriate precision"""
    return f"{int(quantity):,}".replace(",", "X").replace(".", ",").replace("X", ".")
from colorama import Fore, Style

def setup_styles():
    """Setup color styles"""
    return {
        "header": Fore.CYAN + Style.BRIGHT,
        "border": Fore.WHITE,
        "buy": Fore.GREEN + Style.BRIGHT,
        "sell": Fore.RED + Style.BRIGHT,
        "normal": Style.RESET_ALL,
        "dim": Style.DIM,
    } 
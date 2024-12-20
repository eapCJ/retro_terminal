from colorama import Fore, Back, Style

def setup_styles():
    """Setup color styles"""
    return {
        "header": Back.BLUE + Fore.WHITE + Style.BRIGHT,
        "border": Fore.BLUE,
        "buy": Back.GREEN + Fore.BLACK + Style.BRIGHT,
        "sell": Back.RED + Fore.WHITE + Style.BRIGHT,
        "normal": Style.RESET_ALL,
        "dim": Style.DIM + Fore.WHITE,
        "highlight": Fore.YELLOW + Style.BRIGHT,
    } 
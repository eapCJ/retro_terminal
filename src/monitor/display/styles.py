from colorama import Fore, Back, Style

def setup_styles():
    """Setup color styles"""
    return {
        "header": Back.BLUE + Fore.WHITE + Style.BRIGHT,
        "border": Fore.WHITE,
        "buy": Back.GREEN + Fore.BLACK + Style.BRIGHT,
        "sell": Back.RED + Fore.WHITE + Style.BRIGHT,
        "normal": Style.RESET_ALL,
        "dim": Style.DIM,
    } 
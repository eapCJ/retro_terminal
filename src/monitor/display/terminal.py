import sys
from colorama import init, AnsiToWin32

# Initialize colorama
init(wrap=False)
stream = AnsiToWin32(sys.stdout).stream

def clear_screen():
    """Clear the screen and reset cursor"""
    stream.write("\033[2J\033[3J\033[H")
    stream.flush()

def clear_line(row: int):
    """Clear a specific line"""
    move_cursor(row, 1)
    stream.write("\033[2K")  # Clear entire line
    stream.flush()

def move_cursor(row: int, col: int):
    """Move cursor to specific position"""
    stream.write(f"\033[{row};{col}H")
    stream.flush()

def hide_cursor():
    """Hide the cursor"""
    stream.write("\033[?25l")
    stream.flush()

def show_cursor():
    """Show the cursor"""
    stream.write("\033[?25h")
    stream.flush() 
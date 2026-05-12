"""
Terminal output formatting utilities for AISSM_BH
"""

import sys
import shutil
from typing import Optional

# 注意：MessageType 的导入已移至 print_message 函数内部，以解决循环导入问题

class Colors:
    """ANSI color codes for terminal output"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    GREEN = "\033[38;5;42m"
    YELLOW = "\033[38;5;214m"
    RED = "\033[38;5;203m"
    CYAN = "\033[38;5;141m"
    GRAY = "\033[38;5;103m"
    WARM_ORANGE = "\033[38;5;215;1m"
    BRIGHT_BLUE = "\033[38;5;75;1m"

    @classmethod
    def disable_colors(cls):
        """Disable all colors by setting them to empty strings"""
        for attr in dir(cls):
            if not attr.startswith('__') and not callable(getattr(cls, attr)):
                setattr(cls, attr, '')


def should_use_colors() -> bool:
    """
    Determine if colors should be used in terminal output.

    Returns
    -------
    bool
        True if colors should be used, False otherwise.
    """
    return sys.stdout.isatty()


def print_message(message: str, msg_type: "MessageType" = None,
                  style: Optional[str] = None, width: Optional[int] = None):
    """
    Print a formatted message to the console.

    Parameters
    ----------
    message : str
        The message to print.
    msg_type : MessageType, optional
        Type of message (info, success, warning, error, etc.).
    style : str, optional
        Optional additional styling (box, divider).
    width : int, optional
        Width of the message box (defaults to terminal width).
    """
    # 延迟导入打破循环依赖
    from AISSM_BH.core.enums import MessageType
    
    if msg_type is None:
        msg_type = MessageType.INFO
    
    # Get terminal width if not specified
    if not width:
        try:
            width = shutil.get_terminal_size().columns
        except:
            width = 80
    
    # Configure colors and prefixes based on message type
    if msg_type == MessageType.INFO:
        color = ""
        prefix = "🔹 [INFO]"
    elif msg_type == MessageType.SUCCESS:
        color = Colors.GREEN
        prefix = "✅ [SUCCESS]"
    elif msg_type == MessageType.WARNING:
        color = Colors.YELLOW
        prefix = "⚠ [WARN]"
    elif msg_type == MessageType.ERROR:
        color = Colors.RED
        prefix = "❌ [ERR]"
    elif msg_type == MessageType.TITLE:
        color = Colors.BRIGHT_BLUE
        prefix = "▸ "
    elif msg_type == MessageType.SYSTEM:
        color = ""
        prefix = "🤖 [SYS]"
    elif msg_type == MessageType.USER:
        color = ""
        prefix = "👤 [USR]"
    elif msg_type == MessageType.COMMAND:
        color = Colors.GRAY
        prefix = "$ "
    elif msg_type == MessageType.TOOL:
        color = Colors.CYAN
        prefix = "⚙ [TOOL]"
    elif msg_type == MessageType.FINAL:
        color = Colors.WARM_ORANGE
        prefix = "🏁 [DONE]"
    else:
        color = ""
        prefix = ""
    
    # Apply styling
    if style == "box":
        box_width = width - 4  # Account for side margins
        print(f"{color}┌{'─' * box_width}┐{Colors.RESET}")
        
        # Split message into lines that fit within the box
        lines = []
        curr_line = ""
        
        for word in message.split():
            if len(curr_line) + len(word) + 1 <= box_width - 4:  # -4 for margins
                curr_line += word + " "
            else:
                lines.append(curr_line)
                curr_line = word + " "
        if curr_line:
            lines.append(curr_line)
        
        # Print each line within the box
        for line in lines:
            padding = box_width - len(line) - 2
            print(f"{color}│ {line}{' ' * padding} │{Colors.RESET}")
        
        print(f"{color}└{'─' * box_width}┘{Colors.RESET}")
    
    elif style == "divider":
        print(f"{color}{'═' * width}{Colors.RESET}")
        print(f"{color}{prefix}{message}{Colors.RESET}")
        print(f"{color}{'═' * width}{Colors.RESET}")
    
    else:
        # Basic formatting with prefix
        print(f"{color}{prefix}{message}{Colors.RESET}")


def prompt_user(message: str, default: Optional[str] = None,
                choices: Optional[list] = None) -> str:
    """
    Prompt the user for input with optional default value and choices.

    Parameters
    ----------
    message : str
        The message to display to the user.
    default : str, optional
        Optional default value if user hits enter.
    choices : list, optional
        Optional list of valid choices.

    Returns
    -------
    str
        The user's response.
    """
    # Format message with default value if provided
    if default is not None:
        prompt = f"{Colors.CYAN}{message} [{default}]: {Colors.RESET}"
    else:
        prompt = f"{Colors.CYAN}{message}: {Colors.RESET}"
    
    # Print choices if provided
    if choices:
        for i, choice in enumerate(choices, 1):
            print(f"{Colors.CYAN}  {i}. {choice}{Colors.RESET}")
        
        while True:
            response = input(prompt)
            
            # Use default if empty response and default provided
            if not response and default is not None:
                return default
            
            # Try to interpret as a choice number
            try:
                choice_idx = int(response) - 1
                if 0 <= choice_idx < len(choices):
                    return choices[choice_idx]
                else:
                    print(f"{Colors.YELLOW}Please enter a number between 1 and {len(choices)}{Colors.RESET}")
            except ValueError:
                # If response matches a choice directly, return it
                if response in choices:
                    return response
                print(f"{Colors.YELLOW}Please enter a valid choice{Colors.RESET}")
    else:
        # Simple prompt without choices
        response = input(prompt)
        
        # Use default if empty response and default provided
        if not response and default is not None:
            return default
        
        return response

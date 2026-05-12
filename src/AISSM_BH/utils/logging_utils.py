"""
Logging utilities for GROMACS Copilot
"""

import logging
import sys
from typing import Optional

from AISSM_BH.utils.terminal import print_message

class ConsoleLogManual(logging.Handler):
    """Custom logging handler that formats log messages for terminal output"""
    
    def emit(self, record):
        from AISSM_BH.core.enums import MessageType
        msg = self.format(record)
        if record.levelno >= logging.ERROR:
            print_message(msg, MessageType.ERROR)
        elif record.levelno >= logging.WARNING:
            print_message(msg, MessageType.WARNING)
        else:
            print_message(msg, MessageType.INFO)


def setup_logging(log_file: Optional[str] = "md_agent.log", level: int = logging.INFO):
    """
    Set up logging for AISSM_BH.

    Parameters
    ----------
    log_file : str, optional
        Path to log file. Default is "md_agent.log".
    level : int, optional
        Logging level (e.g., logging.INFO). Default is logging.INFO.
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    terminal_formatter = logging.Formatter("%(message)s")
    
    # Set up file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Set up custom terminal handler
    terminal_handler = ConsoleLogManual()
    terminal_handler.setLevel(level)
    terminal_handler.setFormatter(terminal_formatter)
    root_logger.addHandler(terminal_handler)
    
    # Log setup completion
    logging.info(f"Logging initialized with level {logging.getLevelName(level)}")
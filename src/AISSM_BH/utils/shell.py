"""
Shell command execution utilities for GROMACS Copilot
"""

import subprocess
import logging
import shutil
from typing import Dict, Any, Optional

# 注意：print_message 和 MessageType 的导入已移至 run_shell_command 函数内部，以解决循环导入问题

def run_shell_command(command: str, capture_output: bool = True,
                     suppress_output: bool = False) -> Dict[str, Any]:
    """
    Run a shell command with proper error handling.

    Parameters
    ----------
    command : str
        Shell command to run.
    capture_output : bool, optional
        Whether to capture stdout/stderr. Default is True.
    suppress_output : bool, optional
        Whether to suppress terminal output. Default is False.

    Returns
    -------
    dict
        Dictionary with keys: ``success``, ``return_code``, ``stdout``, ``stderr``, ``command``.
    """
    # 延迟导入以打破循环依赖
    from AISSM_BH.utils.terminal import print_message
    from AISSM_BH.core.enums import MessageType

    logging.info(f"Running command: {command}")
    
    if not suppress_output:
        print_message(command, MessageType.COMMAND)
    
    try:
        if capture_output:
            result = subprocess.run(
                command, 
                shell=True, 
                check=False,
                text=True,
                capture_output=True
            )
            
            if result.returncode == 0:
                # Only show partial output if it's too long
                if not suppress_output:
                    if len(result.stdout) > 500:
                        trimmed_output = result.stdout[:500] + "...\n[Output trimmed for brevity]"
                        print_message(f"Command succeeded with output:\n{trimmed_output}", MessageType.SUCCESS)
                    elif result.stdout.strip():
                        print_message(f"Command succeeded with output:\n{result.stdout}", MessageType.SUCCESS)
                    else:
                        print_message("Command succeeded with no output", MessageType.SUCCESS)
            else:
                if not suppress_output:
                    print_message(f"Command failed with error:\n{result.stderr}", MessageType.ERROR)
            
            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
        else:
            result = subprocess.run(
                command, 
                shell=True, 
                check=False
            )
            
            if not suppress_output:
                if result.returncode == 0:
                    print_message("Command succeeded", MessageType.SUCCESS)
                else:
                    print_message("Command failed", MessageType.ERROR)
            
            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": "Output not captured",
                "stderr": "Error output not captured",
                "command": command
            }
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Command execution failed: {error_msg}")
        
        if not suppress_output:
            print_message(f"Command execution failed: {error_msg}", MessageType.ERROR)
        
        return {
            "success": False,
            "return_code": 1,
            "stdout": "",
            "stderr": error_msg,
            "command": command,
            "error": error_msg
        }


def check_command_exists(command: str) -> bool:
    """
    Check if a command exists in the system PATH.

    Parameters
    ----------
    command : str
        Command to check.

    Returns
    -------
    bool
        True if the command exists, False otherwise.
    """
    return shutil.which(command) is not None


def find_executable(executable_names: list) -> Optional[str]:
    """
    Find an executable from a list of possible names.

    Parameters
    ----------
    executable_names : list
        List of possible executable names.

    Returns
    -------
    str or None
        Path to the executable if found, else None.
    """
    for name in executable_names:
        path = shutil.which(name)
        if path:
            return path
    return None
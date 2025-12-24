from liangent.tools.registry import tool
from liangent.tools.shell_env import shell

@tool
def shell_execute(command: str) -> str:
    """
    Executes a shell command. 
    Use this to run python scripts (e.g., 'python3 search.py --arg val') or explore the file system.
    Security: Only allows specific commands (python3, ls, etc.) and blocks dangerous patterns.

    Args:
        command: The shell command to execute.
    """
    return shell.execute(command)

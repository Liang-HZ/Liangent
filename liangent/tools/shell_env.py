import subprocess
import shlex
import re
from typing import List

class SecurityViolation(Exception):
    pass

class ShellSandbox:
    def __init__(self, allowed_commands: List[str] = None):
        self.allowed_commands = set(allowed_commands or ["python3", "ls", "grep", "cat", "date", "find", "--match","--file","--limit"])
        self.blocked_patterns = [
            r";",  r"&", r"`", r"\$\(" # Prevent chaining/subshell attempts even if shell=False (defensive)
        ]
        
    def validate_command(self, command: str) -> List[str]:
        """
        Parses command and validates against whitelist/blacklist.
        Returns parsed parts list.
        """
        if not command or not command.strip():
            raise SecurityViolation("Empty command")
            
        # 1. Check Blocked Patterns (Text-based)
        for pattern in self.blocked_patterns:
            if re.search(pattern, command):
                raise SecurityViolation(f"Command contains forbidden pattern: {pattern}")
                
        # 2. Parse
        try:
            parts = shlex.split(command)
        except ValueError as e:
            raise SecurityViolation(f"Command parsing failed: {e}")
            
        if not parts:
            raise SecurityViolation("Empty command after parsing")
            
        executable = parts[0]
        
        # 3. Check Whitelist
        # Allow running local scripts directly if they are in whitelist or if python3 is used
        if executable not in self.allowed_commands:
             # Special case: If user tries "./script.sh", we block specific paths unless whitelisted.
             # Strict whitelist means ONLY these commands.
             raise SecurityViolation(f"Command '{executable}' is not in the allowed whitelist.")
             
        # 4. Path Traversal Checks (Basic)
        for part in parts:
            if ".." in part: # simplistic check
                 if part.startswith("/") and not part.startswith("/Users/simplelife/PycharmProjects/liangent"):
                     # Restrict absolute paths to project dir
                     raise SecurityViolation(f"Access to absolute path '{part}' outside project directory is forbidden.")
        
        return parts

    def execute(self, command: str, cwd: str = "/Users/simplelife/PycharmProjects/liangent", timeout: int = 60) -> str:
        try:
            parts = self.validate_command(command)
            
            result = subprocess.run(
                parts,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                # CRITICAL for security
                shell=False
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nStderr: {result.stderr}"
                
            return output.strip() if output else "Success (No Output)"
            
        except SecurityViolation as e:
            return f"Security Error: {str(e)}"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out."
        except Exception as e:
             return f"Execution Error: {str(e)}"

# Global instance
shell = ShellSandbox()

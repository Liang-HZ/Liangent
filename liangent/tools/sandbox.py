import ast
import subprocess
import sys
import json
import os
from typing import Any, Dict

# === Security Configuration ===
ALLOWED_MODULES = {
    "math", "datetime", "json", "random", "re", 
    "collections", "itertools", "functools", "statistics"
}

# Blacklisted built-in functions
BLACKLISTED_BUILTINS = {
    "open", "exec", "eval", "compile", "input", 
    "globals", "locals", "exit", "quit", "help"
}

class SecurityViolation(Exception):
    pass

class ExecutionTimeout(Exception):
    pass

class ASTValidator(ast.NodeVisitor):
    def __init__(self):
        self.errors = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split('.')[0] not in ALLOWED_MODULES:
                self.errors.append(f"Importing module '{alias.name}' is not allowed.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split('.')[0] not in ALLOWED_MODULES:
             self.errors.append(f"Importing from module '{node.module}' is not allowed.")
        self.generic_visit(node)
        
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in BLACKLISTED_BUILTINS:
                self.errors.append(f"Function '{node.func.id}' is blocked.")
        self.generic_visit(node)
        
    def visit_Attribute(self, node):
        # Prevent accessing some dangerous attributes directly if possible
        # This is hard to perfect safely with AST-only, but we catch __ stuff
        if node.attr.startswith("__"):
             self.errors.append(f"Accessing private/magic attribute '{node.attr}' is restricted.")
        self.generic_visit(node)

    def validate(self, code: str):
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise SecurityViolation(f"Syntax Error: {e}")
        
        self.visit(tree)
        if self.errors:
            raise SecurityViolation("\n".join(self.errors))


# Wrapper script template for subprocess execution
# This script is executed in a completely isolated Python process
_WRAPPER_SCRIPT = '''
import sys
import json
import builtins

# Security config (passed as JSON)
ALLOWED_MODULES = {allowed_modules}
BLACKLISTED_BUILTINS = {blacklisted_builtins}

# Secure globals
safe_globals = {{"__builtins__": {{}}}}

for name in dir(builtins):
    if name == "__import__":
        safe_globals["__builtins__"][name] = getattr(builtins, name)
        continue
    if name not in BLACKLISTED_BUILTINS and not name.startswith("_"):
        safe_globals["__builtins__"][name] = getattr(builtins, name)

# Pre-import allowed modules
for mod in ALLOWED_MODULES:
    try:
        safe_globals[mod] = __import__(mod)
    except ImportError:
        pass

# Execute user code
code = {code_json}

try:
    exec(code, safe_globals)
    result = {{"success": True, "output": "", "error": None}}
except Exception as e:
    result = {{"success": False, "output": "", "error": f"{{type(e).__name__}}: {{str(e)}}"}}

# Output result as JSON to stdout (for parent to parse)
# This is safe because we've redirected stdout in parent
print("__SANDBOX_RESULT__" + json.dumps(result))
'''


class SafeExecutor:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.validator = ASTValidator()

    def execute(self, code: str) -> Dict[str, Any]:
        """
        Execute python code safely using subprocess for cross-platform consistency.
        Works identically on Windows, macOS, and Linux.
        Returns: {"success": bool, "output": str, "error": str}
        """
        # 0. REPL-like behavior: Auto-print last expression
        try:
            tree = ast.parse(code)
            if tree.body and isinstance(tree.body[-1], ast.Expr):
                # Wrap the last expression in print()
                last_expr = tree.body[-1].value
                print_call = ast.Call(
                    func=ast.Name(id='print', ctx=ast.Load()),
                    args=[last_expr],
                    keywords=[]
                )
                tree.body[-1] = ast.Expr(value=print_call)
                ast.fix_missing_locations(tree)
                code = ast.unparse(tree)
        except Exception:
            # If parsing fails here, let validator catch it or exec fail
            pass

        # 1. AST Validation
        try:
            self.validator.validate(code)
        except SecurityViolation as e:
            return {"success": False, "output": "", "error": str(e)}

        # 2. Build wrapper script
        wrapper = _WRAPPER_SCRIPT.format(
            allowed_modules=repr(ALLOWED_MODULES),
            blacklisted_builtins=repr(BLACKLISTED_BUILTINS),
            code_json=json.dumps(code)
        )

        # 3. Execute in subprocess (cross-platform, completely isolated)
        try:
            result = subprocess.run(
                [sys.executable, "-c", wrapper],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            )
            
            # Parse stdout for our result marker
            stdout = result.stdout
            stderr = result.stderr
            
            # Find result JSON in output
            marker = "__SANDBOX_RESULT__"
            if marker in stdout:
                # Split to get user output and result
                parts = stdout.split(marker)
                user_output = parts[0]
                try:
                    result_json = json.loads(parts[1].strip())
                    if result_json.get("success"):
                        return {"success": True, "output": user_output, "error": None}
                    else:
                        return {"success": False, "output": user_output, "error": result_json.get("error", "Unknown error")}
                except json.JSONDecodeError:
                    return {"success": False, "output": user_output, "error": "Failed to parse execution result"}
            else:
                # No marker found - execution crashed before reaching result
                error_msg = stderr.strip() if stderr else "Process crashed with no output"
                return {"success": False, "output": stdout, "error": error_msg}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": "Execution timed out."}
        except Exception as e:
            return {"success": False, "output": "", "error": f"Subprocess error: {str(e)}"}


# Singleton instance
sandbox = SafeExecutor(timeout=5)

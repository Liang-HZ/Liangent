import inspect
import json
from functools import wraps
from typing import Callable, Dict, Any, List

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[Dict[str, Any]] = []

    def register(self, func: Callable):
        """
        Decorator to register a function as a tool.
        """
        name = func.__name__
        doc = func.__doc__ or "No description provided."
        sig = inspect.signature(func)
        
        # Parse Google-style docstring for parameter descriptions
        param_docs = {}
        clean_doc = doc
        if doc:
            lines = doc.split('\n')
            clean_lines = []
            in_args_section = False
            
            for line in lines:
                stripped = line.strip()
                
                # Detect start of Args section
                if stripped.lower() in ("args:", "arguments:", "parameters:"):
                    in_args_section = True
                    continue
                
                # Check for other sections which signal end of Args
                if stripped.endswith(":") and ':' not in stripped[:-1]:
                     if stripped.lower() in ("returns:", "raises:", "yields:", "example:", "examples:"):
                         in_args_section = False
                
                # Parse args
                if in_args_section:
                    # "param (type): desc" or "param: desc"
                    if ':' in stripped:
                        p_part, p_desc = stripped.split(':', 1)
                        p_name = p_part.strip()
                        if '(' in p_name:
                            p_name = p_name.split('(')[0].strip()
                        param_docs[p_name] = p_desc.strip()
                else:
                    clean_lines.append(line)
            
            clean_doc = "\n".join(clean_lines).strip()

        # Build JSON Schema for parameters
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            
            param_type = "string"  # Default
            if param.annotation is int:
                param_type = "integer"
            elif param.annotation is bool:
                param_type = "boolean"
            elif param.annotation is float:
                param_type = "number"
            elif param.annotation is dict:
                param_type = "object"
            elif param.annotation is list:
                param_type = "array"
            
            # Use extracted description or fallback
            param_description = param_docs.get(param_name, f"Parameter: {param_name}")
            
            parameters["properties"][param_name] = {
                "type": param_type,
                "description": param_description
            }
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)

        schema = {
            "name": name,
            "description": clean_doc,
            "parameters": parameters
        }
        
        self._tools[name] = func
        self._schemas.append(schema)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    def get_tool(self, name: str) -> Callable | None:
        return self._tools.get(name)

    def get_schemas(self) -> List[Dict[str, Any]]:
        return self._schemas
    
    def execute(self, name: str, args: dict | str) -> Any:
        func = self.get_tool(name)
        if not func:
            raise ValueError(f"Tool '{name}' not found.")
        
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except:
                pass # Might be raw string arg if tool expects it, but usually standard is dict
        
        if isinstance(args, dict):
            return func(**args)
        else:
            return func(args)

# Global Registry Instance
registry = ToolRegistry()
tool = registry.register

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from datetime import datetime

class PromptEngine:
    def __init__(self, prompt_dir: str = None):
        if not prompt_dir:
            # Default to liangent/prompts relative to this file (core/prompt_engine.py -> liangent/prompts)
            current_dir = Path(__file__).parent.parent
            prompt_dir = current_dir / "prompts"
        
        self.env = Environment(loader=FileSystemLoader(str(prompt_dir)))
        
    def render(self, template_name: str, **kwargs) -> str:
        template = self.env.get_template(template_name)
        # Inject standard context if needed
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return template.render(now=now, **kwargs)

import os
from typing import Any, Dict
from jinja2 import Environment, FileSystemLoader, BaseLoader, TemplateNotFound


_PROMPTS_DIR = os.path.dirname(os.path.abspath(__file__))


class PromptLoader:
    """Loads and renders Jinja2 prompt templates from the workflow prompts directory."""

    def __init__(self, prompts_dir: str = _PROMPTS_DIR):
        self.env = Environment(loader=FileSystemLoader(prompts_dir))

    def load(self, name: str) -> str:
        """Load a raw prompt template by name (with or without .j2 extension)."""
        if not name.endswith(".j2"):
            name = f"{name}.j2"
        try:
            return self.env.get_template(name).render()
        except TemplateNotFound as exc:
            raise FileNotFoundError(f"Prompt template not found: {name}") from exc

    def render(self, name: str, **kwargs: Any) -> str:
        """Render a prompt template with variables."""
        if not name.endswith(".j2"):
            name = f"{name}.j2"
        template = self.env.get_template(name)
        return template.render(**kwargs)

    def render_string(self, source: str, **kwargs: Any) -> str:
        """Render an in-memory Jinja2 template string."""
        template = self.env.from_string(source)
        return template.render(**kwargs)


def get_loader() -> PromptLoader:
    return PromptLoader()

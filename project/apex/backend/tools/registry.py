"""
APEX Tool Registry.

Unlike AEGIS Runtime's bare ToolManager (name -> callable, no
metadata, and not actually wired into RuntimeEngine), every APEX
tool declares:

    - name
    - description
    - input_schema   (JSON-schema-ish dict, for the UI/API to display)
    - output_schema  (same)
    - risk_level     (governance.RiskLevel)
    - handler        (callable(task, context) -> dict)

`context` is a mutable dict scoped to a single execution. It lets
tools like `simulate_failure` and `repair_service` coordinate through
shared state (e.g. "is the service currently broken?") without any
global variables, so two concurrent executions never interfere with
each other.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, Any, Optional

from apex.backend.governance.governance import RiskLevel


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    risk_level: RiskLevel
    handler: Callable[[Any, Dict[str, Any]], Dict[str, Any]]

    def as_public_dict(self) -> Dict[str, Any]:
        """Serializable view for GET /api/tools (no handler)."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "risk_level": self.risk_level.value,
        }


class ToolNotFoundError(Exception):
    pass


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if not tool.name:
            raise ValueError("Tool name cannot be empty.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' is not registered.")
        return self._tools[name]

    def has(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self):
        return [t.as_public_dict() for t in self._tools.values()]

    def execute(
        self,
        name: str,
        task: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        tool = self.get(name)
        return tool.handler(task, context if context is not None else {})

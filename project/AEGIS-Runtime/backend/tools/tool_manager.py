from typing import Callable, Dict, Any


class ToolManager:
    """
    Registry and execution layer for AEGIS tools.
    """

    def __init__(self):
        self.tools: Dict[str, Callable[..., Any]] = {}

    def register(
        self,
        name: str,
        tool: Callable[..., Any],
    ) -> None:
        """Register a tool by name."""

        if not name:
            raise ValueError("Tool name cannot be empty.")

        self.tools[name] = tool

    def execute(
        self,
        name: str,
        *args,
        **kwargs,
    ) -> Any:
        """Execute a registered tool."""

        if name not in self.tools:
            raise ValueError(
                f"Tool '{name}' is not registered."
            )

        return self.tools[name](*args, **kwargs)

    def list_tools(self):
        """Return the names of registered tools."""

        return list(self.tools.keys())

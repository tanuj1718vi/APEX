from typing import Callable, Dict, Any


class CapabilityRegistry:
    """
    Registry of capabilities that Workers can execute.

    A capability maps a capability name to a Python handler.
    """

    def __init__(self):
        self._capabilities: Dict[str, Callable[..., Any]] = {}

    def register(
        self,
        name: str,
        handler: Callable[..., Any],
    ) -> None:
        """
        Register a capability.
        """

        if not name or not name.strip():
            raise ValueError(
                "Capability name cannot be empty."
            )

        if not callable(handler):
            raise TypeError(
                "Capability handler must be callable."
            )

        self._capabilities[name] = handler

    def has(self, name: str) -> bool:
        """
        Check whether a capability exists.
        """

        return name in self._capabilities

    def get(
        self,
        name: str,
    ) -> Callable[..., Any]:
        """
        Retrieve a capability handler.
        """

        if name not in self._capabilities:
            raise KeyError(
                f"Capability '{name}' is not registered."
            )

        return self._capabilities[name]

    def list_capabilities(self):
        """
        Return all registered capabilities.
        """

        return list(self._capabilities.keys())

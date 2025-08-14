"""
Auto-registration handler system for DataLoader and other handler-based classes.

Handler classes auto-register themselves when imported, making the system
flexible and easy to extend.
"""

from typing import Any

from .main import get_retrieval_mode

# Global handler registry: handler_type -> mode -> handler_class
_handlers: dict[str, dict[str, type]] = {}


def register_handler(handler_type: str, mode: str, handler_class: type) -> None:
    """
    Register a handler class for a specific type and mode.

    This is typically called automatically when handler classes are imported.

    Args:
        handler_type: The type of handler (e.g., "dataloader", "pathfinder")
        mode: The mode this handler supports (e.g., "local", "cloud", "cluster")
        handler_class: The handler class to register
    """
    if handler_type not in _handlers:
        _handlers[handler_type] = {}
    _handlers[handler_type][mode] = handler_class


def get_handler(handler_type: str, *args: Any, **kwargs: Any) -> Any:
    """
    Get a handler instance for the specified type and current retrieval mode.

    Args:
        handler_type: The type of handler to get (e.g., "dataloader", "pathfinder")
        *args: Positional arguments to pass to the handler constructor
        **kwargs: Keyword arguments to pass to the handler constructor

    Returns:
        An instance of the appropriate handler class

    Raises:
        ValueError: If no handlers are registered for the type or mode is unsupported
    """
    if handler_type not in _handlers:
        raise ValueError()

    mode = get_retrieval_mode()
    handler_mapping = _handlers[handler_type]

    if mode not in handler_mapping:
        raise ValueError()

    handler_class = handler_mapping[mode]
    return handler_class(*args, **kwargs)


def get_registered_handlers() -> dict[str, dict[str, type]]:
    """
    Get all registered handlers (useful for debugging/inspection).

    Returns:
        Dictionary mapping handler types to their mode->class mappings
    """
    return _handlers.copy()

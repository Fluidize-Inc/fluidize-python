"""
Configurable retrieval mode system for DataLoader.

This module provides a global configuration system for determining
retrieval mode (local/cloud/cluster) that can be customized per application.
"""

from typing import Callable, Optional

# Global mode function - can be overridden by applications
_get_mode_function: Optional[Callable[[], str]] = None


def set_mode_function(func: Callable[[], str]) -> None:
    """
    Set the global function for determining retrieval mode.

    This should be called once at application startup to configure
    how the DataLoader determines whether to use local, cloud, or cluster storage.

    Args:
        func: Function that returns 'local', 'cloud', or 'cluster'

    Example:
        def my_mode_function():
            return "local" if some_condition else "cloud"

        set_mode_function(my_mode_function)
    """
    global _get_mode_function
    _get_mode_function = func


def get_retrieval_mode() -> str:
    """
    Get the current retrieval mode.

    Uses the configured mode function if available, otherwise falls back
    to default Python library logic.

    Returns:
        str: 'local', 'cloud', or 'cluster'
    """
    if _get_mode_function:
        return _get_mode_function()

    # Default fallback for Python library
    try:
        from fluidize.config import config

        return "local" if config.is_local_mode() else "api"
    except ImportError:
        # If config not available, default to local
        return "local"


def reset_mode_function() -> None:
    """
    Reset to default mode detection.

    Useful for testing or when switching between different configurations.
    """
    global _get_mode_function
    _get_mode_function = None

"""
Fluidize Python Client - High-level interface for the Fluidize Engine and API.
"""

from pathlib import Path
from typing import Any, Literal, Optional

from fluidize_sdk import FluidizeSDK

import fluidize.core.utils.dataloader.loader.loader_local
import fluidize.core.utils.dataloader.loader.writer_local

# Ensure handlers are registered (redundant safety check)
import fluidize.core.utils.pathfinder.methods.local  # noqa: F401

from .backends.local import LocalBackend
from .config import FluidizeConfig
from .managers.projects import Projects


class FluidizeClient:
    """
    High-level client for interacting with Fluidize.

    This client provides an intuitive interface for managing projects,
    nodes, and running simulation flows. It supports two modes:

    - API mode: Connects to the Fluidize cloud API
    - Local mode: Works with local Fluidize engine installation

    Configuration is handled automatically through environment variables
    and the FluidizeConfig class.
    """

    def __init__(self, mode: Literal["local", "api", "auto"] = "auto", base_path: Optional[Path] = None):
        """
        Initialize the Fluidize client.

        Args:
            mode: Operation mode - "local", "api", or "auto" for environment detection
            base_path: Optional custom base path for local mode. If None, uses ~/.fluidize
                 Config will handle all other settings via environment variables
        """
        # Config handles all configuration logic
        self.config = FluidizeConfig(mode, base_path)

        # Check Docker availability for local mode
        if self.config.is_local_mode():
            self.config.warn_if_docker_unavailable()

        # Initialize the appropriate backend based on mode
        self._backend = self._initialize_backend()

        # Initialize resource managers
        self.projects = Projects(self._backend)

    def _initialize_backend(self) -> Any:
        """Initialize the appropriate backend based on the mode."""
        if self.config.is_api_mode():
            return self._initialize_api_backend()
        else:
            return self._initialize_local_backend()

    def _initialize_api_backend(self) -> FluidizeSDK:
        """Initialize the API backend using FluidizeSDK."""
        if not self.config.api_key:
            msg = "API mode requires an API key. Set the FLUIDIZE_API_KEY environment variable."
            raise ValueError(msg)

        return FluidizeSDK(
            api_token=self.config.api_key,
        )

    def _initialize_local_backend(self) -> LocalBackend:
        """Initialize the local backend."""
        return LocalBackend(self.config)

    @property
    def mode(self) -> str:
        """Get the current operation mode."""
        return self.config.mode

    @property
    def backend(self) -> Any:
        """Access the underlying backend for advanced operations."""
        return self._backend

    def __repr__(self) -> str:
        return f"FluidizeClient(mode='{self.mode}')"

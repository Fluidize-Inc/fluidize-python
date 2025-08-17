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

from .adapters.local import LocalAdapter
from .config import FluidizeConfig
from .managers.registry import RegistryManager


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

        # Initialize the appropriate adapter based on mode
        self._adapter = self._initialize_adapter()

        # Initialize resource managers
        self.projects = RegistryManager(self._adapter)

    def _initialize_adapter(self) -> Any:
        """Initialize the appropriate adapter based on the mode.

        Returns:
            Any: The initialized adapter
        """
        if self.config.is_api_mode():
            return self._initialize_api_adapter()
        else:
            return self._initialize_local_adapter()

    def _initialize_api_adapter(self) -> FluidizeSDK:
        """Initialize the API adapter using FluidizeSDK.

        Returns:
            FluidizeSDK: The initialized API adapter
        """
        if not self.config.api_key:
            msg = "API mode requires an API key. Set the FLUIDIZE_API_KEY environment variable."
            raise ValueError(msg)

        return FluidizeSDK(
            api_token=self.config.api_key,
        )

    def _initialize_local_adapter(self) -> LocalAdapter:
        """Initialize the local adapter.

        Returns:
            LocalAdapter: The initialized local adapter
        """
        return LocalAdapter(self.config)

    @property
    def mode(self) -> str:
        """Get the current operation mode.

        Returns:
            str: The current operation mode
        """
        return self.config.mode

    @property
    def adapter(self) -> Any:
        """Access the underlying adapter for advanced operations.

        Returns:
            Any: The underlying adapter
        """
        return self._adapter

    @property
    def projects(self) -> RegistryManager:
        """Access the Client project registry manager.

        Returns:
            RegistryManager: The Client project registry manager
        """
        return self.projects

    def __repr__(self) -> str:
        """Return a string representation of the client.

        Returns:
            str: A string representation of the client
        """
        return f"FluidizeClient(mode='{self.mode}')"

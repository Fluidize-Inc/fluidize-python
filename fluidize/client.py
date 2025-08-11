"""
Fluidize Python Client - High-level interface for the Fluidize Engine and API.
"""

from typing import Any, Literal

from fluidize_sdk import FluidizeSDK

from .config import FluidizeConfig

# TODO: Import these when implemented
# from .managers.projects import Projects
# from .managers.runs import Runs
# from .backends.local import LocalBackend


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

    def __init__(self, mode: Literal["local", "api", "auto"] = "auto"):
        """
        Initialize the Fluidize client.

        Args:
            mode: Operation mode - "local", "api", or "auto" for environment detection
                 Config will handle all other settings via environment variables
        """
        # Config handles all configuration logic
        self.config = FluidizeConfig(mode)

        # Initialize the appropriate backend based on mode
        self._backend = self._initialize_backend()

        # TODO: Initialize resource managers when implemented
        # self.projects = ProjectManager(self._backend, self.config)
        # self.runs = RunManager(self._backend, self.config)

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

    def _initialize_local_backend(self) -> Any:
        """Initialize the local backend."""
        # TODO: Implement LocalBackend
        # return LocalBackend(self.config)
        raise NotImplementedError("Local backend not yet implemented")

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

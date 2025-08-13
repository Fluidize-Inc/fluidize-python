"""Configuration management for Fluidize Client"""

import os
import shutil
import subprocess
import warnings
from pathlib import Path
from typing import Literal


class FluidizeConfig:
    """Lightweight configuration for fluidize library.

    Handles mode switching between local and API operations,
    and manages paths and settings for both modes.
    """

    def __init__(self, mode: Literal["local", "api", "auto"] = "auto"):
        """Initialize configuration with specified mode.

        Args:
            mode: Operation mode - "local", "api", or "auto" for environment detection
        """
        self.mode = self._resolve_mode(mode)

        # Local paths (when mode="local")
        self.local_base_path = Path.home() / ".fluidize"
        self.local_projects_path = self.local_base_path / "projects"
        self.local_simulations_path = self.local_base_path / "simulations"

        # API configuration (when mode="api")
        self.api_key = os.getenv("FLUIDIZE_API_KEY")

        # Ensure local directories exist when in local mode
        if self.mode == "local":
            self._ensure_local_directories()

    def _resolve_mode(self, mode: Literal["local", "api", "auto"]) -> Literal["local", "api"]:
        """Resolve the actual mode from the given mode parameter.

        Args:
            mode: The requested mode

        Returns:
            The resolved mode (either "local" or "api")
        """
        if mode == "auto":
            # Auto-detect from environment variable
            env_mode = os.getenv("FLUIDIZE_MODE", "local").lower()
            return "api" if env_mode == "api" else "local"
        return mode

    def _ensure_local_directories(self) -> None:
        """Ensure local directories exist for local mode operations."""
        self.local_base_path.mkdir(parents=True, exist_ok=True)
        self.local_projects_path.mkdir(parents=True, exist_ok=True)
        self.local_simulations_path.mkdir(parents=True, exist_ok=True)

    def is_local_mode(self) -> bool:
        """Check if running in local mode."""
        return self.mode == "local"

    def is_api_mode(self) -> bool:
        """Check if running in API mode."""
        return self.mode == "api"

    def check_docker_available(self) -> bool:
        """Check if Docker is available and running.

        Returns:
            True if Docker is available, False otherwise
        """
        # First check if docker executable exists
        docker_path = shutil.which("docker")
        if not docker_path:
            return False

        try:
            # Run 'docker --version' to check if Docker is installed and accessible
            result = subprocess.run(  # noqa: S603
                [docker_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
        else:
            return result.returncode == 0

    def warn_if_docker_unavailable(self) -> None:
        """Issue a warning if Docker is not available for local runs."""
        if not self.check_docker_available():
            warnings.warn(
                "Docker is not available. Local simulation runs will not be possible. "
                "Please install and start Docker to enable local execution.",
                UserWarning,
                stacklevel=2,
            )


# Default global config instance
config = FluidizeConfig()

"""Shared fixtures and configuration for integration tests."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

# Import local handlers to ensure they auto-register
from fluidize.backends.local.backend import LocalBackend
from fluidize.client import FluidizeClient
from fluidize.config import FluidizeConfig
from fluidize.managers.projects import Projects


@pytest.fixture
def integration_temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for integration testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def integration_config(integration_temp_dir: Path) -> FluidizeConfig:
    """Create a configuration for integration testing with real filesystem operations."""
    config = FluidizeConfig(mode="local")
    config.local_base_path = integration_temp_dir
    config.local_projects_path = integration_temp_dir / "projects"
    config.local_simulations_path = integration_temp_dir / "simulations"

    # Ensure directories exist
    config.local_projects_path.mkdir(parents=True, exist_ok=True)
    config.local_simulations_path.mkdir(parents=True, exist_ok=True)

    return config


@pytest.fixture(autouse=True)
def setup_integration_config(integration_temp_dir: Path):
    """Set up configuration paths for integration tests."""
    # Create a real test config
    test_config = FluidizeConfig(mode="local")
    test_config.local_base_path = integration_temp_dir
    test_config.local_projects_path = integration_temp_dir / "projects"
    test_config.local_simulations_path = integration_temp_dir / "simulations"

    # Create directories
    test_config.local_projects_path.mkdir(parents=True, exist_ok=True)
    test_config.local_simulations_path.mkdir(parents=True, exist_ok=True)

    # Patch all the places where config is used
    patches = [
        patch("fluidize.config.config", test_config),
        patch("fluidize.core.utils.pathfinder.methods.local.config", test_config),
    ]

    # Start all patches
    for p in patches:
        p.start()

    try:
        yield test_config
    finally:
        # Stop all patches
        for p in patches:
            p.stop()


@pytest.fixture
def local_backend(integration_config: FluidizeConfig) -> LocalBackend:
    """Create a LocalBackend for integration testing."""
    return LocalBackend(integration_config)


@pytest.fixture
def client() -> FluidizeClient:
    """Create a full Client for end-to-end integration testing."""
    return FluidizeClient(mode="local")


@pytest.fixture
def projects_manager(local_backend: LocalBackend) -> Projects:
    """Create a Projects manager for integration testing."""
    return Projects(local_backend)


@pytest.fixture
def sample_projects_data() -> list[dict]:
    """Sample project data for integration testing."""
    return [
        {
            "id": "integration-project-1",
            "label": "Integration Test Project 1",
            "description": "First project for integration testing",
            "status": "active",
            "location": "/integration/test/1",
        },
        {
            "id": "integration-project-2",
            "label": "Integration Test Project 2",
            "description": "Second project for integration testing",
            "status": "pending",
            "location": "/integration/test/2",
        },
        {
            "id": "integration-project-minimal",
            "label": "",
            "description": "",
            "status": "",
            "location": "",
        },
    ]

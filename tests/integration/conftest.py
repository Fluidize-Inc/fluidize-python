"""Shared fixtures and configuration for integration tests."""

import tempfile
from collections.abc import Generator
from pathlib import Path

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
    from fluidize.config import config

    # Store original values to restore later
    original_mode = config.mode
    original_base_path = config.local_base_path
    original_projects_path = config.local_projects_path
    original_simulations_path = config.local_simulations_path

    # Configure the global config instance for testing
    config.mode = "local"
    config.local_base_path = integration_temp_dir
    config.local_projects_path = integration_temp_dir / "projects"
    config.local_simulations_path = integration_temp_dir / "simulations"

    # Create directories
    config.local_projects_path.mkdir(parents=True, exist_ok=True)
    config.local_simulations_path.mkdir(parents=True, exist_ok=True)

    try:
        yield config
    finally:
        # Restore original values
        config.mode = original_mode
        config.local_base_path = original_base_path
        config.local_projects_path = original_projects_path
        config.local_simulations_path = original_simulations_path


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

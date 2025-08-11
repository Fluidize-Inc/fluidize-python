"""Shared fixtures and configuration for unit tests."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from upath import UPath

# Import local handlers to ensure they auto-register
from fluidize.config import FluidizeConfig
from fluidize.core.types.project import ProjectSummary


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing filesystem operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config(temp_dir: Path) -> FluidizeConfig:
    """Create a mock configuration for local mode testing."""
    config = FluidizeConfig(mode="local")
    config.local_base_path = temp_dir
    config.local_projects_path = temp_dir / "projects"
    config.local_simulations_path = temp_dir / "simulations"

    # Ensure directories exist
    config.local_projects_path.mkdir(parents=True, exist_ok=True)
    config.local_simulations_path.mkdir(parents=True, exist_ok=True)

    return config


@pytest.fixture
def sample_project() -> ProjectSummary:
    """Create a sample project for testing."""
    return ProjectSummary(
        id="test-project-001",
        label="Test Project",
        description="A sample project for testing",
        status="active",
        location="/test/location",
        metadata_version="1.0",
    )


@pytest.fixture
def sample_project_minimal() -> ProjectSummary:
    """Create a minimal sample project for testing."""
    return ProjectSummary(id="minimal-project", metadata_version="1.0")


@pytest.fixture
def mock_path_finder() -> Generator[Mock, None, None]:
    """Mock PathFinder for consistent testing."""
    with patch("fluidize.core.utils.pathfinder.path_finder.PathFinder._get_handler") as mock_handler_getter:
        mock_handler = Mock()
        mock_handler_getter.return_value = mock_handler
        yield mock_handler


@pytest.fixture
def mock_data_loader() -> Generator[Mock, None, None]:
    """Mock DataLoader for filesystem operation testing."""
    with patch("fluidize.core.utils.dataloader.data_loader.DataLoader._get_handler") as mock_handler_getter:
        mock_handler = Mock()
        mock_handler_getter.return_value = mock_handler
        yield mock_handler


@pytest.fixture
def mock_data_writer() -> Generator[Mock, None, None]:
    """Mock DataWriter for filesystem write operation testing."""
    with patch("fluidize.core.utils.dataloader.data_writer.DataWriter") as mock_writer:
        yield mock_writer


@pytest.fixture
def setup_project_paths(temp_dir: Path, sample_project: ProjectSummary) -> dict[str, UPath]:
    """Set up project directory structure for testing."""
    projects_path = UPath(temp_dir / "projects")
    project_path = projects_path / sample_project.id
    metadata_path = project_path / "metadata.yaml"

    projects_path.mkdir(parents=True, exist_ok=True)
    project_path.mkdir(parents=True, exist_ok=True)

    return {"projects_path": projects_path, "project_path": project_path, "metadata_path": metadata_path}

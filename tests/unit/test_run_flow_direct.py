"""Direct unit tests for run_flow functionality.

Tests the complete run_flow workflow using the proper managers
and loading ProjectSummary from actual project directories.
"""

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from fluidize.backends.local.backend import LocalBackend
from fluidize.config import FluidizeConfig
from fluidize.core.types.project import ProjectSummary
from fluidize.core.types.runs import RunFlowPayload
from fluidize.managers.project import Project


@pytest.fixture
def test_config(tmp_path):
    """Create a test config for testing."""
    config = FluidizeConfig(mode="local")
    config.local_base_path = tmp_path
    config.local_projects_path = tmp_path / "projects"
    config.local_simulations_path = tmp_path / "simulations"

    # Create directories
    config.local_projects_path.mkdir(parents=True, exist_ok=True)
    config.local_simulations_path.mkdir(parents=True, exist_ok=True)

    return config


@pytest.fixture
def docker_project_path(test_config) -> Path:
    """Copy the Docker test project to the test config directory."""
    source_path = Path(__file__).parent.parent / "fixtures" / "docker_projects" / "project-1754038373536"
    destination_path = test_config.local_projects_path / "project-1754038373536"

    # Copy the entire project structure
    shutil.copytree(source_path, destination_path)

    return destination_path


@pytest.fixture
def project_from_file(docker_project_path, test_config):
    """Load ProjectSummary from the actual project directory using from_file."""
    with (
        patch("fluidize.config.config", test_config),
        patch("fluidize.core.utils.pathfinder.methods.local.config", test_config),
    ):
        return ProjectSummary.from_file(docker_project_path)


@pytest.fixture
def local_backend(test_config):
    """Create a LocalBackend instance for testing."""
    return LocalBackend(test_config)


@pytest.fixture
def project_manager(local_backend, project_from_file):
    """Create a Project manager instance for testing."""
    return Project(local_backend, project_from_file)


class TestRunFlowDirect:
    """Direct tests for run_flow functionality."""

    def test_run_flow_basic_functionality(self, project_manager, test_config):
        """Test basic run_flow functionality using proper managers."""

        # Patch the config to make DataLoader work
        with (
            patch("fluidize.config.config", test_config),
            patch("fluidize.core.utils.pathfinder.methods.local.config", test_config),
        ):
            # Create run payload
            payload = RunFlowPayload(
                name="test_run",
                description="Direct test run using ProjectRuns manager",
                tags=["test", "direct", "managers"],
            )

            # Execute run_flow using the ProjectRuns manager
            result = project_manager.runs.run_flow(payload)

            # Verify response structure
            assert "flow_status" in result
            assert "run_number" in result
            assert result["flow_status"] == "running"
            assert isinstance(result["run_number"], int)
            assert result["run_number"] > 0

    def test_run_flow_payload_variations(self, project_manager, test_config):
        """Test run_flow with different payload configurations."""

        # Patch the config to make DataLoader work
        with (
            patch("fluidize.config.config", test_config),
            patch("fluidize.core.utils.pathfinder.methods.local.config", test_config),
        ):
            # Test minimal payload
            minimal_payload = RunFlowPayload()
            result = project_manager.runs.run_flow(minimal_payload)
            assert result["flow_status"] == "running"

            # Test payload with all fields
            full_payload = RunFlowPayload(
                name="comprehensive_test",
                description="Test with all payload fields populated",
                tags=["comprehensive", "full-payload", "test"],
            )
            result = project_manager.runs.run_flow(full_payload)
            assert result["flow_status"] == "running"

    def test_run_flow_empty_graph(self, local_backend, test_config):
        """Test run_flow with a project that has an empty graph."""

        # Patch the config to make DataLoader work
        with (
            patch("fluidize.config.config", test_config),
            patch("fluidize.core.utils.pathfinder.methods.local.config", test_config),
        ):
            # Create a project with empty graph
            empty_project_id = "empty-graph-project"
            empty_project_dir = test_config.local_projects_path / empty_project_id
            empty_project_dir.mkdir(parents=True)

            # Create empty graph.json
            graph_file = empty_project_dir / "graph.json"
            graph_file.write_text('{"nodes": [], "edges": []}')

            # Create basic metadata
            metadata_file = empty_project_dir / "metadata.yaml"
            metadata_file.write_text(f"""project:
  id: {empty_project_id}
  label: Empty Graph Project
  description: Project with no nodes
  metadata_version: '1.0'
  status: active
""")

            # Create empty parameters
            params_file = empty_project_dir / "parameters.json"
            params_file.write_text('{"metadata": {}, "parameters": {}}')

            # Load project using from_file like the other tests
            project_summary = ProjectSummary.from_file(empty_project_dir)
            project_manager = Project(local_backend, project_summary)

            payload = RunFlowPayload(name="empty_graph_test")

            # Should raise ValueError for no nodes to run
            with pytest.raises(ValueError, match="No nodes to run"):
                project_manager.runs.run_flow(payload)

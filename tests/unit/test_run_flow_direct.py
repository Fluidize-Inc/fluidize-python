"""Direct unit tests for run_flow functionality.

Tests the complete run_flow workflow using the proper managers
and loading ProjectSummary from actual project directories.
"""

import shutil
from pathlib import Path

import pytest

from fluidize.adapters.local.adapter import LocalAdapter
from fluidize.config import FluidizeConfig
from fluidize.core.types.project import ProjectSummary
from fluidize.core.types.runs import RunFlowPayload
from fluidize.managers.project_manager import ProjectManager


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
    from fluidize.config import config

    # Store original values
    original_mode = config.mode
    original_base_path = config.local_base_path
    original_projects_path = config.local_projects_path
    original_simulations_path = config.local_simulations_path

    # Configure global config
    config.mode = test_config.mode
    config.local_base_path = test_config.local_base_path
    config.local_projects_path = test_config.local_projects_path
    config.local_simulations_path = test_config.local_simulations_path

    try:
        return ProjectSummary.from_file(docker_project_path)
    finally:
        # Restore original values
        config.mode = original_mode
        config.local_base_path = original_base_path
        config.local_projects_path = original_projects_path
        config.local_simulations_path = original_simulations_path


@pytest.fixture
def local_adapter(test_config):
    """Create a LocalAdapter instance for testing."""
    return LocalAdapter(test_config)


@pytest.fixture
def project_manager(local_adapter, project_from_file):
    """Create a Project manager instance for testing."""
    return ProjectManager(local_adapter, project_from_file)


class TestRunFlowDirect:
    """Direct tests for run_flow functionality."""

    def test_run_flow_basic_functionality(self, project_manager, test_config):
        """Test basic run_flow functionality using proper managers."""

        # Configure global config for DataLoader
        from fluidize.config import config

        # Store original values
        original_mode = config.mode
        original_base_path = config.local_base_path
        original_projects_path = config.local_projects_path
        original_simulations_path = config.local_simulations_path

        # Configure global config
        config.mode = test_config.mode
        config.local_base_path = test_config.local_base_path
        config.local_projects_path = test_config.local_projects_path
        config.local_simulations_path = test_config.local_simulations_path

        try:
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

            # Verify run outputs directory structure
            run_dir = test_config.local_projects_path / "project-1754038373536" / "runs" / f"run_{result['run_number']}"
            outputs_dir = run_dir / "outputs"

            # Check that outputs directory is created
            assert outputs_dir.exists(), f"Outputs directory not found at {outputs_dir}"

            # Wait a bit for async execution to complete (if needed)
            import time

            max_wait = 10  # seconds
            wait_interval = 0.5
            elapsed = 0

            # Check for output files from both nodes
            node1_output = outputs_dir / "node-1754038461760" / "output.txt"
            node2_output = outputs_dir / "node-1754038465820" / "output.txt"

            # Wait for outputs to be created
            while elapsed < max_wait:
                if node1_output.exists() and node2_output.exists():
                    break
                time.sleep(wait_interval)
                elapsed += wait_interval

            # Verify outputs exist and have correct content
            assert node1_output.exists(), f"Node 1 output not found at {node1_output}"
            assert node2_output.exists(), f"Node 2 output not found at {node2_output}"

            # Check output contents
            node1_content = node1_output.read_text().strip()
            node2_content = node2_output.read_text().strip()

            print("\n📁 Output verification:")
            print(f"  Node 1 output: '{node1_content}' (expected: 'CANDY')")
            print(f"  Node 2 output: '{node2_content}' (expected: 'CANDYCANDY')")

            assert node1_content == "CANDY", f"Node 1 should output 'CANDY', got '{node1_content}'"
            assert node2_content == "CANDYCANDY", f"Node 2 should output 'CANDYCANDY', got '{node2_content}'"
        finally:
            # Restore original values
            config.mode = original_mode
            config.local_base_path = original_base_path
            config.local_projects_path = original_projects_path
            config.local_simulations_path = original_simulations_path

    def test_list_node_outputs_and_get_output_path(self, project_manager, test_config):
        """Test listing node outputs and getting output paths."""
        from fluidize.config import config

        # Store original values
        original_mode = config.mode
        original_base_path = config.local_base_path
        original_projects_path = config.local_projects_path
        original_simulations_path = config.local_simulations_path

        # Configure global config
        config.mode = test_config.mode
        config.local_base_path = test_config.local_base_path
        config.local_projects_path = test_config.local_projects_path
        config.local_simulations_path = test_config.local_simulations_path

        try:
            # Create a fake output directory with some files
            run_dir = test_config.local_projects_path / "project-1754038373536" / "runs" / "run_1"
            outputs_dir = run_dir / "outputs" / "node-1754038461760"
            outputs_dir.mkdir(parents=True, exist_ok=True)

            # Create some test output files
            (outputs_dir / "output.txt").write_text("CANDY")
            (outputs_dir / "plot.png").write_bytes(b"fake image data")
            (outputs_dir / "results.json").write_text('{"result": "success"}')

            # Test listing node outputs
            files = project_manager.runs.list_node_outputs(1, "node-1754038461760")
            assert isinstance(files, list)
            assert "output.txt" in files
            assert "plot.png" in files
            assert "results.json" in files

            # Test getting output path
            output_path = project_manager.runs.get_output_path(1, "node-1754038461760")
            assert output_path.exists()
            assert (output_path / "output.txt").exists()

            # Test with non-existent node
            empty_files = project_manager.runs.list_node_outputs(1, "non-existent-node")
            assert empty_files == []

        finally:
            # Restore original values
            config.mode = original_mode
            config.local_base_path = original_base_path
            config.local_projects_path = original_projects_path
            config.local_simulations_path = original_simulations_path

    def test_run_flow_payload_variations(self, project_manager, test_config):
        """Test run_flow with different payload configurations."""

        # Configure global config for DataLoader
        from fluidize.config import config

        # Store original values
        original_mode = config.mode
        original_base_path = config.local_base_path
        original_projects_path = config.local_projects_path
        original_simulations_path = config.local_simulations_path

        # Configure global config
        config.mode = test_config.mode
        config.local_base_path = test_config.local_base_path
        config.local_projects_path = test_config.local_projects_path
        config.local_simulations_path = test_config.local_simulations_path

        try:
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
        finally:
            # Restore original values
            config.mode = original_mode
            config.local_base_path = original_base_path
            config.local_projects_path = original_projects_path
            config.local_simulations_path = original_simulations_path

    def test_run_flow_empty_graph(self, local_adapter, test_config):
        """Test run_flow with a project that has an empty graph."""

        # Configure global config for DataLoader
        from fluidize.config import config

        # Store original values
        original_mode = config.mode
        original_base_path = config.local_base_path
        original_projects_path = config.local_projects_path
        original_simulations_path = config.local_simulations_path

        # Configure global config
        config.mode = test_config.mode
        config.local_base_path = test_config.local_base_path
        config.local_projects_path = test_config.local_projects_path
        config.local_simulations_path = test_config.local_simulations_path

        try:
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
            project_manager = ProjectManager(local_adapter, project_summary)

            payload = RunFlowPayload(name="empty_graph_test")

            # Should raise ValueError for no nodes to run
            with pytest.raises(ValueError, match="No nodes to run"):
                project_manager.runs.run_flow(payload)
        finally:
            # Restore original values
            config.mode = original_mode
            config.local_base_path = original_base_path
            config.local_projects_path = original_projects_path
            config.local_simulations_path = original_simulations_path

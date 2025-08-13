"""Integration tests for run_flow functionality.

These tests verify that the run_flow workflow works with Docker projects,
focusing on the basic flow execution without complex execution dependencies.
"""

import shutil
from pathlib import Path

import pytest

from fluidize.adapters.local.runs import RunsHandler
from fluidize.core.types.project import ProjectSummary
from fluidize.core.types.runs import RunFlowPayload


@pytest.fixture
def docker_project_fixture() -> ProjectSummary:
    """Create a ProjectSummary from the Docker test project fixture."""
    return ProjectSummary(
        id="project-1754038373536",
        label="SIMPLETEST",
        description="Docker test project",
        location="",
        status="active",
        metadata_version="1.0",
    )


@pytest.fixture
def docker_project_path(integration_temp_dir) -> Path:
    """Copy the Docker test project to the integration temp directory."""
    source_path = Path(__file__).parent.parent / "fixtures" / "docker_projects" / "project-1754038373536"
    destination_path = integration_temp_dir / "projects" / "project-1754038373536"

    # Copy the entire project structure
    shutil.copytree(source_path, destination_path)

    return destination_path


@pytest.fixture
def runs_handler(local_adapter):
    """Create a RunsHandler instance for testing."""
    return RunsHandler(local_adapter.config)


class TestRunFlowIntegration:
    """Integration tests for run_flow functionality."""

    def test_run_flow_basic_functionality(self, runs_handler, docker_project_fixture, docker_project_path):
        """Test basic run_flow functionality without Docker execution."""

        # Create run payload
        payload = RunFlowPayload(name="test_run", description="Integration test run", tags=["test", "integration"])

        # Execute run_flow
        result = runs_handler.run_flow(docker_project_fixture, payload)

        # Verify response structure
        assert "flow_status" in result
        assert "run_number" in result
        assert result["flow_status"] == "running"
        assert isinstance(result["run_number"], int)
        assert result["run_number"] > 0

        # Verify run directory was created
        run_dir = docker_project_path / "runs" / f"run_{result['run_number']}"
        assert run_dir.exists()

        # Verify run metadata exists
        metadata_file = run_dir / "metadata.yaml"
        assert metadata_file.exists()

    def test_run_flow_graph_processing(self, runs_handler, docker_project_fixture, docker_project_path):
        """Test that run_flow properly processes the graph structure."""

        payload = RunFlowPayload(name="graph_processing_test")

        result = runs_handler.run_flow(docker_project_fixture, payload)

        # Verify basic response
        assert result["flow_status"] == "running"
        assert result["run_number"] > 0

        # Verify run environment setup
        run_dir = docker_project_path / "runs" / f"run_{result['run_number']}"
        assert run_dir.exists()

        # Check that node directories were created
        node_dirs = [d for d in run_dir.iterdir() if d.is_dir() and d.name.startswith("node-")]
        assert len(node_dirs) == 2  # Should have 2 nodes from the test project

    def test_run_flow_empty_graph(self, runs_handler, integration_temp_dir):
        """Test run_flow with a project that has an empty graph."""

        # Create a project with empty graph
        empty_project_id = "empty-graph-project"
        empty_project_dir = integration_temp_dir / "projects" / empty_project_id
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

        project = ProjectSummary(
            id=empty_project_id,
            label="Empty Graph Project",
            description="Project with no nodes",
            location="",
            status="active",
            metadata_version="1.0",
        )

        payload = RunFlowPayload(name="empty_graph_test")

        # Should raise ValueError for no nodes to run
        with pytest.raises(ValueError, match="No nodes to run"):
            runs_handler.run_flow(project, payload)

    def test_run_flow_payload_variations(self, runs_handler, docker_project_fixture, docker_project_path):
        """Test run_flow with different payload configurations."""

        # Test minimal payload
        minimal_payload = RunFlowPayload()
        result = runs_handler.run_flow(docker_project_fixture, minimal_payload)
        assert result["flow_status"] == "running"

        # Test payload with all fields
        full_payload = RunFlowPayload(
            name="comprehensive_test",
            description="Test with all payload fields populated",
            tags=["comprehensive", "full-payload", "test"],
        )
        result = runs_handler.run_flow(docker_project_fixture, full_payload)
        assert result["flow_status"] == "running"

        # Verify both runs created separate directories
        runs_dir = docker_project_path / "runs"
        run_dirs = [d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
        assert len(run_dirs) >= 2

    def test_docker_execution_log_saving(self, runs_handler, docker_project_fixture, docker_project_path):
        """Test that Docker execution logs are properly saved to files."""

        # Create run payload
        payload = RunFlowPayload(name="log_saving_test", description="Test Docker log file saving")

        # Execute run_flow - this will execute the Docker containers
        result = runs_handler.run_flow(docker_project_fixture, payload)

        # Verify run executed successfully
        assert result["flow_status"] == "running"
        run_number = result["run_number"]

        # Check log directory structure
        run_dir = docker_project_path / "runs" / f"run_{run_number}"
        logs_dir = run_dir / "logs"
        nodes_log_dir = logs_dir / "nodes"

        # Verify log directories were created
        assert logs_dir.exists(), "Logs directory should be created"
        assert nodes_log_dir.exists(), "Nodes log directory should be created"

        # Check for node log files
        # The test project should have 2 nodes that execute
        log_files = list(nodes_log_dir.glob("*.log"))
        assert len(log_files) > 0, "At least one log file should be created"

        # Verify stdout log files exist for executed nodes
        stdout_logs = list(nodes_log_dir.glob("*_stdout.log"))
        assert len(stdout_logs) > 0, "At least one stdout log should exist"

        # Check that log files have content
        for log_file in stdout_logs:
            content = log_file.read_text()
            assert len(content) > 0, f"Log file {log_file.name} should not be empty"

        # Look for specific node logs
        expected_nodes = ["node-1754038461760", "node-1754038465820"]
        for node_id in expected_nodes:
            stdout_log = nodes_log_dir / f"{node_id}_stdout.log"
            if stdout_log.exists():
                content = stdout_log.read_text()
                assert len(content.strip()) > 0, f"Node {node_id} stdout log should have content"

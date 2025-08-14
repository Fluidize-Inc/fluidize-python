"""Simplified unit tests for ExecutionManager."""

from unittest.mock import Mock, patch

import pytest

from fluidize.core.modules.execute.execution_manager import ExecutionManager
from fluidize.core.types.execution_models import ExecutionMode
from fluidize.core.types.project import ProjectSummary


class TestExecutionManagerSimple:
    """Test suite for ExecutionManager class with actual implementation."""

    @pytest.fixture
    def execution_manager(self):
        """Create ExecutionManager instance for testing."""
        return ExecutionManager()

    @pytest.fixture
    def sample_project(self):
        """Sample project for testing."""
        return ProjectSummary(id="test-project", label="Test Project", metadata_version="1.0")

    @pytest.fixture
    def sample_node(self):
        """Sample node properties for testing."""
        mock_node = Mock()
        mock_node.node_id = "test-node"
        mock_node.type = "simulation"
        mock_node.name = "Test Node"
        return mock_node

    def test_execution_manager_init(self, execution_manager):
        """Test ExecutionManager initialization."""
        assert execution_manager.docker_client is None
        assert execution_manager.k8s_client is None
        assert execution_manager.vm_client is None

    @patch("fluidize.core.modules.execute.execution_manager.logger")
    def test_logging_initialization(self, mock_logger):
        """Test that logger is properly initialized."""
        ExecutionManager()
        mock_logger.info.assert_called_with("ExecutionManager initialized")

    @patch("fluidize.core.modules.execute.execution_manager.create_execution_context")
    @patch("fluidize.core.modules.execute.execution_manager.UniversalContainerBuilder")
    def test_execute_node_context_creation_error(
        self, mock_builder, mock_create_context, execution_manager, sample_project, sample_node
    ):
        """Test error handling during context creation."""
        # Simulate error in context creation
        mock_create_context.side_effect = Exception("Context creation failed")

        result = execution_manager.execute_node(
            project=sample_project, node=sample_node, execution_mode=ExecutionMode.LOCAL_DOCKER
        )

        assert "error" in result
        assert result["success"] is False
        assert "Context creation failed" in str(result["error"])
        assert result["node_id"] == "test-node"

    @patch("fluidize.core.modules.execute.execution_manager.create_execution_context")
    @patch("fluidize.core.modules.execute.execution_manager.UniversalContainerBuilder")
    def test_execute_node_validation_errors(
        self, mock_builder_class, mock_create_context, execution_manager, sample_project, sample_node
    ):
        """Test handling of specification validation errors."""
        # Setup mocks
        mock_context = Mock()
        mock_context.execution_mode = ExecutionMode.LOCAL_DOCKER
        mock_create_context.return_value = mock_context

        mock_spec = Mock()
        mock_builder_class.build_container_spec.return_value = mock_spec
        mock_builder_class.validate_spec.return_value = {
            "errors": ["Invalid image name", "Missing required field"],
            "warnings": [],
        }

        result = execution_manager.execute_node(
            project=sample_project, node=sample_node, execution_mode=ExecutionMode.LOCAL_DOCKER
        )

        assert result["success"] is False
        assert "error" in result
        assert "validation failed" in result["error"].lower()
        assert "validation" in result

    @patch("fluidize.core.modules.execute.execution_manager.create_execution_context")
    @patch("fluidize.core.modules.execute.execution_manager.UniversalContainerBuilder")
    def test_execute_with_mode_kubernetes_not_implemented(
        self, mock_builder_class, mock_create_context, execution_manager, sample_project, sample_node
    ):
        """Test Kubernetes execution mode (not implemented)."""
        # Setup mocks
        mock_context = Mock()
        mock_context.execution_mode = ExecutionMode.KUBERNETES
        mock_create_context.return_value = mock_context

        mock_spec = Mock()
        mock_builder_class.build_container_spec.return_value = mock_spec
        mock_builder_class.validate_spec.return_value = {"errors": [], "warnings": []}

        result = execution_manager.execute_node(
            project=sample_project, node=sample_node, execution_mode=ExecutionMode.KUBERNETES
        )

        assert result["success"] is False
        assert "not yet implemented" in result["error"].lower()

    def test_execute_with_mode_direct(self, execution_manager):
        """Test _execute_with_mode method directly."""
        # Test Kubernetes mode
        result = execution_manager._execute_with_mode(ExecutionMode.KUBERNETES, Mock())
        assert result["success"] is False
        assert "not yet implemented" in result["error"].lower()

        # Test unsupported mode (if any)
        mock_unsupported = Mock()
        mock_unsupported.value = "UNSUPPORTED_MODE"
        result = execution_manager._execute_with_mode(mock_unsupported, Mock())
        assert result["success"] is False
        assert "unsupported" in result["error"].lower()

    @patch("fluidize.core.modules.execute.execution_manager.DockerExecutionClient")
    def test_execute_docker_client_creation(self, mock_docker_client_class, execution_manager):
        """Test Docker client creation in _execute_docker."""
        mock_client = Mock()
        mock_client.pull_image.return_value = True
        mock_result = Mock()
        mock_result.success = True
        mock_result.exit_code = 0
        mock_result.stdout = "success"
        mock_result.stderr = ""
        mock_result.container_id = "container123"
        mock_client.run_container.return_value = mock_result
        mock_docker_client_class.return_value = mock_client

        mock_spec = Mock()
        mock_spec.container_spec.image = "test:latest"
        mock_spec.volume_spec.volumes = []

        result = execution_manager._execute_docker(mock_spec)

        assert execution_manager.docker_client is not None
        assert result["success"] is True
        assert result["execution_mode"] == "local_docker"

        # Test reuse of existing client
        result2 = execution_manager._execute_docker(mock_spec)
        assert result2["success"] is True
        # Client should only be created once
        assert mock_docker_client_class.call_count == 1

    @patch("fluidize.core.modules.execute.execution_manager.DockerExecutionClient")
    def test_execute_docker_pull_failure(self, mock_docker_client_class, execution_manager):
        """Test Docker execution with image pull failure."""
        mock_client = Mock()
        mock_client.pull_image.return_value = False  # Pull fails
        mock_docker_client_class.return_value = mock_client

        mock_spec = Mock()
        mock_spec.container_spec.image = "nonexistent:latest"

        result = execution_manager._execute_docker(mock_spec)

        assert result["success"] is False
        assert "failed to pull image" in result["error"].lower()

    @patch("fluidize.core.modules.execute.execution_manager.VMExecutionClient")
    def test_execute_vm_client_creation(self, mock_vm_client_class, execution_manager):
        """Test VM client creation in _execute_vm."""
        mock_client = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.exit_code = 0
        mock_result.stdout = "success"
        mock_result.stderr = ""
        mock_result.command = "docker run test"
        mock_client.run_container.return_value = mock_result
        mock_vm_client_class.return_value = mock_client

        mock_spec = Mock()
        mock_spec.container_spec = Mock()
        mock_spec.volume_spec.volumes = []

        result = execution_manager._execute_vm(mock_spec)

        assert execution_manager.vm_client is not None
        assert result["success"] is True
        assert result["execution_mode"] == "vm_docker"
        assert "command" in result

    @patch("fluidize.core.modules.execute.execution_manager.DockerExecutionClient")
    def test_execute_docker_exception_handling(self, mock_docker_client_class, execution_manager):
        """Test exception handling in _execute_docker."""
        mock_client = Mock()
        mock_client.pull_image.side_effect = Exception("Docker daemon not running")
        mock_docker_client_class.return_value = mock_client

        mock_spec = Mock()
        mock_spec.container_spec.image = "test:latest"

        result = execution_manager._execute_docker(mock_spec)

        assert result["success"] is False
        assert "docker daemon not running" in result["error"].lower()
        assert result["execution_mode"] == "local_docker"

    @patch("fluidize.core.modules.execute.execution_manager.VMExecutionClient")
    def test_execute_vm_exception_handling(self, mock_vm_client_class, execution_manager):
        """Test exception handling in _execute_vm."""
        mock_client = Mock()
        mock_client.run_container.side_effect = Exception("SSH connection failed")
        mock_vm_client_class.return_value = mock_client

        mock_spec = Mock()

        result = execution_manager._execute_vm(mock_spec)

        assert result["success"] is False
        assert "ssh connection failed" in result["error"].lower()
        assert result["execution_mode"] == "vm_docker"

    def test_execute_node_with_optional_parameters(self, execution_manager, sample_project, sample_node):
        """Test execute_node with optional parameters."""
        with patch("fluidize.core.modules.execute.execution_manager.create_execution_context") as mock_create_context:
            # Simulate error to test parameter passing
            mock_create_context.side_effect = Exception("Test error")

            result = execution_manager.execute_node(
                project=sample_project,
                node=sample_node,
                prev_node=Mock(),
                execution_mode=ExecutionMode.LOCAL_DOCKER,
                run_number=5,
                run_id="test-run-123",
                custom_param="test_value",
            )

            assert result["success"] is False
            assert result["node_id"] == "test-node"

            # Verify create_execution_context was called with all parameters
            mock_create_context.assert_called_once()
            call_args = mock_create_context.call_args
            assert call_args.kwargs["run_number"] == 5
            assert call_args.kwargs["run_id"] == "test-run-123"
            assert call_args.kwargs["custom_param"] == "test_value"

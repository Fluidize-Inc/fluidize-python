"""Simplified unit tests for VMExecutionClient based on actual implementation."""

from unittest.mock import Mock

import pytest

from fluidize.core.modules.execute.vm_client import SSHClientError, VMExecutionClient, VMExecutionResult
from fluidize.core.types.execution_models import ContainerSpec, Volume, VolumeMount


class TestVMExecutionResultSimple:
    """Test suite for VMExecutionResult dataclass."""

    def test_vm_execution_result_success(self):
        """Test VMExecutionResult with successful execution."""
        result = VMExecutionResult(exit_code=0, stdout="Success output", stderr="", command="docker run test")

        assert result.exit_code == 0
        assert result.stdout == "Success output"
        assert result.stderr == ""
        assert result.command == "docker run test"
        assert result.success is True

    def test_vm_execution_result_failure(self):
        """Test VMExecutionResult with failed execution."""
        result = VMExecutionResult(exit_code=1, stdout="", stderr="Error occurred", command="docker run test")

        assert result.exit_code == 1
        assert result.success is False
        assert result.stderr == "Error occurred"

    def test_vm_execution_result_defaults(self):
        """Test VMExecutionResult with default values."""
        result = VMExecutionResult(exit_code=0)

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.command == ""
        assert result.success is True


class TestVMExecutionClientSimple:
    """Test suite for VMExecutionClient class with actual methods."""

    @pytest.fixture
    def mock_ssh_client(self):
        """Mock SSH client for testing."""
        return Mock()

    @pytest.fixture
    def vm_client(self, mock_ssh_client):
        """Create VMExecutionClient instance for testing."""
        return VMExecutionClient(ssh_client=mock_ssh_client)

    @pytest.fixture
    def vm_client_no_ssh(self):
        """Create VMExecutionClient without SSH client."""
        return VMExecutionClient()

    @pytest.fixture
    def sample_container_spec(self):
        """Sample container spec for testing."""
        return ContainerSpec(
            name="test-container",
            image="test/image:latest",
            command=["python", "script.py"],
            env_vars={"VAR1": "value1", "VAR2": "value2"},
        )

    def test_vm_client_init_with_ssh(self, mock_ssh_client):
        """Test VMExecutionClient initialization with SSH client."""
        client = VMExecutionClient(ssh_client=mock_ssh_client)
        assert client.ssh_client == mock_ssh_client

    def test_vm_client_init_without_ssh(self):
        """Test VMExecutionClient initialization without SSH client."""
        client = VMExecutionClient()
        assert client.ssh_client is None

    def test_ensure_ssh_client_raises_error_when_none(self, vm_client_no_ssh):
        """Test that _ensure_ssh_client raises error when SSH client is None."""
        with pytest.raises(SSHClientError):
            vm_client_no_ssh._ensure_ssh_client()

    def test_ensure_ssh_client_passes_when_present(self, vm_client):
        """Test that _ensure_ssh_client passes when SSH client exists."""
        # Should not raise an exception
        vm_client._ensure_ssh_client()

    def test_build_safe_docker_args(self, vm_client, sample_container_spec):
        """Test building safe Docker arguments."""
        volumes = []
        args = vm_client._build_safe_docker_args(sample_container_spec, volumes)

        # Should be a list of strings
        assert isinstance(args, list)
        assert all(isinstance(arg, str) for arg in args)

        # Should contain basic docker command structure
        assert "sudo" in args
        assert "docker" in args
        assert "run" in args
        assert sample_container_spec.image in args

    def test_build_safe_docker_args_with_detach(self, vm_client, sample_container_spec):
        """Test building Docker arguments with detach flag."""
        volumes = []
        args = vm_client._build_safe_docker_args(sample_container_spec, volumes, detach=True)

        assert "-d" in args  # Detached mode
        assert "--rm" not in args  # Remove flag not used in detached mode

    def test_build_safe_docker_args_without_detach(self, vm_client, sample_container_spec):
        """Test building Docker arguments without detach flag."""
        volumes = []
        args = vm_client._build_safe_docker_args(sample_container_spec, volumes, detach=False)

        assert "--rm" in args  # Remove flag used in interactive mode
        assert "-d" not in args  # Detached mode not used

    def test_add_runtime_flags(self, vm_client):
        """Test adding runtime flags."""
        args = []

        # Test non-detached mode
        vm_client._add_runtime_flags(args, detach=False, platform="linux/amd64")
        assert "--rm" in args
        assert "--platform" in args
        assert "linux/amd64" in args

        # Test detached mode
        args = []
        vm_client._add_runtime_flags(args, detach=True, platform="linux/arm64")
        assert "-d" in args
        assert "--platform" in args
        assert "linux/arm64" in args

    def test_add_container_config_environment(self, vm_client, sample_container_spec):
        """Test adding container configuration for environment variables."""
        args = []
        volumes = []

        vm_client._add_container_config(args, sample_container_spec, volumes)

        # Should contain environment variable flags
        assert "-e" in args
        env_args = " ".join(args)
        assert "VAR1=value1" in env_args
        assert "VAR2=value2" in env_args

    def test_add_container_config_working_dir(self, vm_client):
        """Test adding working directory to container config."""
        spec = ContainerSpec(name="test", image="nginx:latest", working_dir="/app")

        args = []
        vm_client._add_container_config(args, spec, [])

        assert "--workdir" in args
        assert "/app" in args

    def test_convert_volumes_for_vm(self, vm_client):
        """Test converting volumes for VM execution."""
        volumes = [
            Volume(name="data", volume_type="hostPath", source={"path": "/host/data"}),
            Volume(name="gcs", volume_type="gcsFuse", source={}),
        ]

        mounts = [
            VolumeMount(name="data", mount_path="/container/data"),
            VolumeMount(name="gcs", mount_path="/container/gcs"),
        ]

        mappings = vm_client._convert_volumes_for_vm(volumes, mounts)

        assert "/host/data" in mappings
        assert mappings["/host/data"] == "/container/data"
        assert "/mnt/fluidize_users" in mappings
        assert mappings["/mnt/fluidize_users"] == "/container/gcs"

    def test_add_security_config(self, vm_client):
        """Test adding security configuration."""
        spec = ContainerSpec(
            name="test", image="nginx:latest", security_context={"runAsUser": 1000, "privileged": True}
        )

        args = []
        vm_client._add_security_config(args, spec)

        assert "--user" in args
        assert "1000" in args
        assert "--privileged" in args

    def test_add_network_config(self, vm_client):
        """Test adding network configuration."""
        args = []
        kwargs = {"network_mode": "host"}

        vm_client._add_network_config(args, kwargs)

        assert "--network" in args
        assert "host" in args

    def test_add_resource_config(self, vm_client):
        """Test adding resource configuration."""
        spec = ContainerSpec(name="test", image="nginx:latest", resources={"limits": {"memory": "1Gi", "cpu": "500m"}})

        args = []
        vm_client._add_resource_config(args, spec)

        assert "--memory" in args
        assert "1Gi" in args
        assert "--cpus" in args
        assert "500m" in args

    def test_add_labels(self, vm_client):
        """Test adding labels to Docker args."""
        spec = ContainerSpec(name="test", image="nginx:latest", labels={"app": "test", "version": "1.0"})

        args = []
        vm_client._add_labels(args, spec)

        assert "--label" in args
        label_args = " ".join(args)
        assert "app=test" in label_args
        assert "version=1.0" in label_args

    def test_ssh_client_error_exception(self):
        """Test SSHClientError exception."""
        error = SSHClientError("SSH not configured")
        assert str(error) == "SSH not configured"
        assert isinstance(error, RuntimeError)

    def test_pull_image_method_exists(self, vm_client):
        """Test that pull_image method exists and is callable."""
        assert hasattr(vm_client, "pull_image")
        assert callable(vm_client.pull_image)

    def test_get_container_logs_method_exists(self, vm_client):
        """Test that get_container_logs method exists and is callable."""
        assert hasattr(vm_client, "get_container_logs")
        assert callable(vm_client.get_container_logs)

    def test_run_container_method_exists(self, vm_client):
        """Test that run_container method exists and is callable."""
        assert hasattr(vm_client, "run_container")
        assert callable(vm_client.run_container)

    def test_execute_methods_exist(self, vm_client):
        """Test that execution-related methods exist."""
        # Test methods that actually exist based on the implementation
        assert hasattr(vm_client, "_execute_via_ssh")
        assert hasattr(vm_client, "_execute_locally")
        assert callable(vm_client._execute_via_ssh)
        assert callable(vm_client._execute_locally)

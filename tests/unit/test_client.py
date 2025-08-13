"""Unit tests for FluidizeClient and FluidizeConfig classes."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from fluidize.client import FluidizeClient
from fluidize.config import FluidizeConfig


class TestFluidizeConfig:
    """Test suite for FluidizeConfig class."""

    def test_default_base_path(self):
        """Test that default base path is set to ~/.fluidize when no base_path is provided."""
        config = FluidizeConfig(mode="local")

        expected_base_path = Path.home() / ".fluidize"
        assert config.local_base_path == expected_base_path
        assert config.local_projects_path == expected_base_path / "projects"
        assert config.local_simulations_path == expected_base_path / "simulations"

    def test_custom_base_path(self):
        """Test that custom base path is used when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "custom" / "test" / "path"
            config = FluidizeConfig(mode="local", base_path=custom_path)

            assert config.local_base_path == custom_path
            assert config.local_projects_path == custom_path / "projects"
            assert config.local_simulations_path == custom_path / "simulations"

    def test_custom_base_path_with_temp_dir(self):
        """Test custom base path with a real temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "fluidize_test"
            config = FluidizeConfig(mode="local", base_path=custom_path)

            assert config.local_base_path == custom_path
            assert config.local_projects_path == custom_path / "projects"
            assert config.local_simulations_path == custom_path / "simulations"

    def test_base_path_none_uses_default(self):
        """Test that passing None for base_path uses the default."""
        config = FluidizeConfig(mode="local", base_path=None)

        expected_base_path = Path.home() / ".fluidize"
        assert config.local_base_path == expected_base_path

    def test_api_mode_ignores_base_path(self):
        """Test that API mode still works with base_path parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "custom" / "test" / "path"
            config = FluidizeConfig(mode="api", base_path=custom_path)

            # In API mode, local paths should still be set but not used
            assert config.local_base_path == custom_path
            assert config.is_api_mode()

    @patch.dict("os.environ", {"FLUIDIZE_MODE": "local"})
    def test_auto_mode_with_custom_base_path(self):
        """Test auto mode with custom base path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "auto" / "test" / "path"
            config = FluidizeConfig(mode="auto", base_path=custom_path)

            assert config.mode == "local"
            assert config.local_base_path == custom_path


class TestFluidizeClient:
    """Test suite for FluidizeClient class."""

    @patch("fluidize.client.LocalBackend")
    def test_default_initialization(self, mock_local_backend):
        """Test FluidizeClient default initialization."""
        client = FluidizeClient()

        assert client.config.local_base_path == Path.home() / ".fluidize"
        assert client.mode in ["local", "api"]

    @patch("fluidize.client.LocalBackend")
    def test_custom_base_path_initialization(self, mock_local_backend):
        """Test FluidizeClient with custom base path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "custom" / "client" / "path"
            client = FluidizeClient(mode="local", base_path=custom_path)

            assert client.config.local_base_path == custom_path
            assert client.config.local_projects_path == custom_path / "projects"
            assert client.config.local_simulations_path == custom_path / "simulations"
            assert client.mode == "local"

    @patch("fluidize.client.LocalBackend")
    def test_base_path_none_uses_default(self, mock_local_backend):
        """Test that passing None for base_path uses the default."""
        client = FluidizeClient(mode="local", base_path=None)

        assert client.config.local_base_path == Path.home() / ".fluidize"

    @patch("fluidize.client.LocalBackend")
    def test_projects_manager_initialized(self, mock_local_backend):
        """Test that projects manager is properly initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "test" / "projects" / "path"
            client = FluidizeClient(mode="local", base_path=custom_path)

            assert hasattr(client, "projects")

    @patch("fluidize.client.FluidizeSDK")
    @patch.dict("os.environ", {"FLUIDIZE_API_KEY": "test-api-key"})
    def test_api_mode_with_base_path(self, mock_sdk):
        """Test API mode still works when base_path is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "api" / "test" / "path"
            client = FluidizeClient(mode="api", base_path=custom_path)

            assert client.mode == "api"
            # base_path should still be set in config even for API mode
            assert client.config.local_base_path == custom_path

    @patch("fluidize.client.LocalBackend")
    def test_backend_receives_config(self, mock_local_backend):
        """Test that backend receives the config with custom base path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "backend" / "config" / "path"
            client = FluidizeClient(mode="local", base_path=custom_path)

            # Verify LocalBackend was called with the config
            mock_local_backend.assert_called_once_with(client.config)

            # Verify the config has the right base path
            passed_config = mock_local_backend.call_args[0][0]
            assert passed_config.local_base_path == custom_path

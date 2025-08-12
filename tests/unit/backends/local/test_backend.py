"""Unit tests for LocalBackend - the main local backend coordinator."""

from unittest.mock import Mock, patch

from fluidize.backends.local.backend import LocalBackend
from fluidize.backends.local.projects import ProjectsHandler


class TestLocalBackend:
    """Test suite for LocalBackend class."""

    def test_init_creates_projects_handler(self, mock_config):
        """Test LocalBackend initializes with ProjectsHandler."""
        with patch("fluidize.backends.local.backend.ProjectsHandler") as mock_projects_handler_class:
            mock_projects_handler = Mock()
            mock_projects_handler_class.return_value = mock_projects_handler

            backend = LocalBackend(mock_config)

            assert backend.config == mock_config
            assert backend.projects == mock_projects_handler
            mock_projects_handler_class.assert_called_once_with(mock_config)

    def test_config_stored(self, mock_config):
        """Test that configuration is properly stored."""
        with patch("fluidize.backends.local.backend.ProjectsHandler"):
            backend = LocalBackend(mock_config)

            assert backend.config is mock_config

    def test_projects_handler_attribute(self, mock_config):
        """Test that projects handler is accessible as attribute."""
        with patch("fluidize.backends.local.backend.ProjectsHandler") as mock_projects_handler_class:
            mock_projects_handler = Mock(spec=ProjectsHandler)
            mock_projects_handler_class.return_value = mock_projects_handler

            backend = LocalBackend(mock_config)

            # Test that we can access projects handler methods
            assert hasattr(backend.projects, "list")
            assert hasattr(backend.projects, "retrieve")
            assert hasattr(backend.projects, "upsert")
            assert hasattr(backend.projects, "delete")

    def test_backend_interface_compatibility(self, mock_config):
        """Test that LocalBackend provides SDK-compatible interface."""
        with patch("fluidize.backends.local.backend.ProjectsHandler") as mock_projects_handler_class:
            mock_projects_handler = Mock()
            mock_projects_handler_class.return_value = mock_projects_handler

            backend = LocalBackend(mock_config)

            # Test SDK-like interface structure
            assert hasattr(backend, "projects")
            assert backend.projects is not None

            # Test that projects handler is properly initialized
            mock_projects_handler_class.assert_called_once_with(mock_config)

    def test_future_extensibility_structure(self, mock_config):
        """Test that backend structure supports future handlers."""
        with patch("fluidize.backends.local.backend.ProjectsHandler"):
            backend = LocalBackend(mock_config)

            # Current structure should support future additions
            assert hasattr(backend, "config")
            assert hasattr(backend, "projects")

            # These have been implemented
            assert hasattr(backend, "graph")  # ✅ Now implemented
            assert hasattr(backend, "runs")  # ✅ Now implemented

    def test_multiple_backend_instances(self, mock_config):
        """Test that multiple backend instances can be created independently."""
        with patch("fluidize.backends.local.backend.ProjectsHandler") as mock_projects_handler_class:
            mock_handler_1 = Mock()
            mock_handler_2 = Mock()
            mock_projects_handler_class.side_effect = [mock_handler_1, mock_handler_2]

            backend_1 = LocalBackend(mock_config)
            backend_2 = LocalBackend(mock_config)

            assert backend_1.projects is mock_handler_1
            assert backend_2.projects is mock_handler_2
            assert backend_1.projects is not backend_2.projects

            # Both should be called with the same config
            assert mock_projects_handler_class.call_count == 2
            mock_projects_handler_class.assert_any_call(mock_config)

    def test_projects_delegation(self, mock_config):
        """Test that backend properly delegates to projects handler."""
        with patch("fluidize.backends.local.backend.ProjectsHandler") as mock_projects_handler_class:
            mock_projects_handler = Mock()
            mock_projects_handler_class.return_value = mock_projects_handler

            backend = LocalBackend(mock_config)

            # Test that we can call methods on the projects handler
            backend.projects.list()
            backend.projects.retrieve("test-id")
            backend.projects.upsert(id="test-upsert")
            backend.projects.delete("test-delete")

            # Verify the calls were made to the handler
            mock_projects_handler.list.assert_called_once()
            mock_projects_handler.retrieve.assert_called_once_with("test-id")
            mock_projects_handler.upsert.assert_called_once_with(id="test-upsert")
            mock_projects_handler.delete.assert_called_once_with("test-delete")

    def test_config_type_flexibility(self):
        """Test that backend accepts different config types."""
        # Test with None config (should not raise)
        with patch("fluidize.backends.local.backend.ProjectsHandler") as mock_projects_handler_class:
            mock_projects_handler_class.return_value = Mock()

            backend = LocalBackend(None)
            assert backend.config is None
            mock_projects_handler_class.assert_called_once_with(None)

        # Test with mock config object
        mock_config = Mock()
        with patch("fluidize.backends.local.backend.ProjectsHandler") as mock_projects_handler_class:
            mock_projects_handler_class.return_value = Mock()

            backend = LocalBackend(mock_config)
            assert backend.config is mock_config
            mock_projects_handler_class.assert_called_once_with(mock_config)

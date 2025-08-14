"""Unit tests for LocalAdapter - the main local adapter coordinator."""

from unittest.mock import Mock, patch

from fluidize.adapters.local.adapter import LocalAdapter
from fluidize.adapters.local.projects import ProjectsHandler


class TestLocalAdapter:
    """Test suite for LocalAdapter class."""

    def test_init_creates_projects_handler(self, mock_config):
        """Test LocalAdapter initializes with ProjectsHandler."""
        with patch("fluidize.adapters.local.adapter.ProjectsHandler") as mock_projects_handler_class:
            mock_projects_handler = Mock()
            mock_projects_handler_class.return_value = mock_projects_handler

            adapter = LocalAdapter(mock_config)

            assert adapter.config == mock_config
            assert adapter.projects == mock_projects_handler
            mock_projects_handler_class.assert_called_once_with(mock_config)

    def test_config_stored(self, mock_config):
        """Test that configuration is properly stored."""
        with patch("fluidize.adapters.local.adapter.ProjectsHandler"):
            adapter = LocalAdapter(mock_config)

            assert adapter.config is mock_config

    def test_projects_handler_attribute(self, mock_config):
        """Test that projects handler is accessible as attribute."""
        with patch("fluidize.adapters.local.adapter.ProjectsHandler") as mock_projects_handler_class:
            mock_projects_handler = Mock(spec=ProjectsHandler)
            mock_projects_handler_class.return_value = mock_projects_handler

            adapter = LocalAdapter(mock_config)

            # Test that we can access projects handler methods
            assert hasattr(adapter.projects, "list")
            assert hasattr(adapter.projects, "retrieve")
            assert hasattr(adapter.projects, "upsert")
            assert hasattr(adapter.projects, "delete")

    def test_adapter_interface_compatibility(self, mock_config):
        """Test that LocalAdapter provides SDK-compatible interface."""
        with patch("fluidize.adapters.local.adapter.ProjectsHandler") as mock_projects_handler_class:
            mock_projects_handler = Mock()
            mock_projects_handler_class.return_value = mock_projects_handler

            adapter = LocalAdapter(mock_config)

            # Test SDK-like interface structure
            assert hasattr(adapter, "projects")
            assert adapter.projects is not None

            # Test that projects handler is properly initialized
            mock_projects_handler_class.assert_called_once_with(mock_config)

    def test_future_extensibility_structure(self, mock_config):
        """Test that adapter structure supports future handlers."""
        with patch("fluidize.adapters.local.adapter.ProjectsHandler"):
            adapter = LocalAdapter(mock_config)

            # Current structure should support future additions
            assert hasattr(adapter, "config")
            assert hasattr(adapter, "projects")

            # These have been implemented
            assert hasattr(adapter, "graph")  # ✅ Now implemented
            assert hasattr(adapter, "runs")  # ✅ Now implemented

    def test_multiple_adapter_instances(self, mock_config):
        """Test that multiple adapter instances can be created independently."""
        with patch("fluidize.adapters.local.adapter.ProjectsHandler") as mock_projects_handler_class:
            mock_handler_1 = Mock()
            mock_handler_2 = Mock()
            mock_projects_handler_class.side_effect = [mock_handler_1, mock_handler_2]

            adapter_1 = LocalAdapter(mock_config)
            adapter_2 = LocalAdapter(mock_config)

            assert adapter_1.projects is mock_handler_1
            assert adapter_2.projects is mock_handler_2
            assert adapter_1.projects is not adapter_2.projects

            # Both should be called with the same config
            assert mock_projects_handler_class.call_count == 2
            mock_projects_handler_class.assert_any_call(mock_config)

    def test_projects_delegation(self, mock_config):
        """Test that adapter properly delegates to projects handler."""
        with patch("fluidize.adapters.local.adapter.ProjectsHandler") as mock_projects_handler_class:
            mock_projects_handler = Mock()
            mock_projects_handler_class.return_value = mock_projects_handler

            adapter = LocalAdapter(mock_config)

            # Test that we can call methods on the projects handler
            adapter.projects.list()
            adapter.projects.retrieve("test-id")
            adapter.projects.upsert(id="test-upsert")
            adapter.projects.delete("test-delete")

            # Verify the calls were made to the handler
            mock_projects_handler.list.assert_called_once()
            mock_projects_handler.retrieve.assert_called_once_with("test-id")
            mock_projects_handler.upsert.assert_called_once_with(id="test-upsert")
            mock_projects_handler.delete.assert_called_once_with("test-delete")

    def test_config_type_flexibility(self):
        """Test that adapter accepts different config types."""
        # Test with None config (should not raise)
        with patch("fluidize.adapters.local.adapter.ProjectsHandler") as mock_projects_handler_class:
            mock_projects_handler_class.return_value = Mock()

            adapter = LocalAdapter(None)
            assert adapter.config is None
            mock_projects_handler_class.assert_called_once_with(None)

        # Test with mock config object
        mock_config = Mock()
        with patch("fluidize.adapters.local.adapter.ProjectsHandler") as mock_projects_handler_class:
            mock_projects_handler_class.return_value = Mock()

            adapter = LocalAdapter(mock_config)
            assert adapter.config is mock_config
            mock_projects_handler_class.assert_called_once_with(mock_config)

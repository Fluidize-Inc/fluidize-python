"""Unit tests for Simulations Manager - high-level simulation library interface."""

from unittest.mock import Mock, patch

import pytest

from fluidize.managers.simulations import SimulationsManager


class TestSimulationsManager:
    """Test suite for SimulationsManager class."""

    @pytest.fixture
    def mock_adapter(self):
        """Create a mock adapter for testing."""
        adapter = Mock()
        return adapter

    @pytest.fixture
    def simulations_manager(self, mock_adapter):
        """Create a SimulationsManager instance for testing."""
        with patch("fluidize.managers.simulations.FluidizeSDK"):
            return SimulationsManager(mock_adapter)

    @patch("fluidize.managers.simulations.FluidizeSDK")
    def test_init(self, mock_sdk_class, mock_adapter):
        """Test SimulationsManager initialization."""
        manager = SimulationsManager(mock_adapter)

        assert manager._adapter is mock_adapter
        assert manager.fluidize_sdk is not None
        mock_sdk_class.assert_called_once()

    @patch("fluidize.managers.simulations.FluidizeSDK")
    def test_list_simulations_returns_list(self, mock_sdk_class, simulations_manager):
        """Test that list_simulations returns a list."""
        # Arrange
        mock_sdk_instance = mock_sdk_class.return_value
        simulations_manager.fluidize_sdk = mock_sdk_instance
        # Create a mock simulation object with model_dump method
        mock_simulation = Mock()
        mock_simulation.model_dump.return_value = {
            "name": "Test Simulation",
            "id": "sim_001",
            "description": "A test simulation",
            "date": "2024-01-01",
            "version": "1.0.0",
            "authors": [],
            "tags": [],
        }
        mock_sdk_instance.simulation.list_simulations.return_value = [mock_simulation]

        # Act
        result = simulations_manager.list_simulations()

        # Assert
        assert isinstance(result, list)
        mock_sdk_instance.simulation.list_simulations.assert_called_once_with(sim_global=True)

    @patch("fluidize.managers.simulations.FluidizeSDK")
    def test_list_simulations_empty_list(self, mock_sdk_class, simulations_manager):
        """Test that list_simulations handles empty results."""
        # Arrange
        mock_sdk_instance = mock_sdk_class.return_value
        simulations_manager.fluidize_sdk = mock_sdk_instance
        mock_sdk_instance.simulation.list_simulations.return_value = []

        # Act
        result = simulations_manager.list_simulations()

        # Assert
        assert result == []
        mock_sdk_instance.simulation.list_simulations.assert_called_once_with(sim_global=True)

    @patch("fluidize.managers.simulations.FluidizeSDK")
    def test_list_simulations_sdk_delegation(self, mock_sdk_class, simulations_manager):
        """Test that list_simulations properly delegates to SDK."""
        # Arrange
        mock_sdk_instance = mock_sdk_class.return_value
        simulations_manager.fluidize_sdk = mock_sdk_instance
        mock_sdk_instance.simulation.list_simulations.return_value = []

        # Act
        simulations_manager.list_simulations()

        # Assert
        mock_sdk_instance.simulation.list_simulations.assert_called_once_with(sim_global=True)

"""Integration tests for SimulationsManager - tests real API connectivity."""

import os
from unittest.mock import Mock, patch

import pytest

from fluidize.managers.simulations import SimulationsManager


class TestSimulationsManagerIntegration:
    """Integration test suite for SimulationsManager class."""

    @pytest.fixture
    def mock_adapter(self):
        """Create a mock adapter for testing."""
        adapter = Mock()
        return adapter

    @pytest.mark.skipif(not os.getenv("FLUIDIZE_API_KEY"), reason="FLUIDIZE_API_KEY environment variable not set")
    def test_list_simulations_integration(self, mock_adapter):
        """Integration test that actually calls the API and prints output."""

        # Create manager without mocking SDK
        manager = SimulationsManager(mock_adapter)

        # Act - make real API call
        result = manager.list_simulations()

        # Assert basic functionality
        assert isinstance(result, list)

        # Print results for manual verification
        print("\n=== Integration Test Results ===")
        print(f"Number of simulations found: {len(result)}")
        for sim in result:
            print("Simulation details:")
            print(f"  Name: {sim.name}")
            print(f"  ID: {sim.id}")
            print(f"  Description: {sim.description}")
            print(f"  Version: {sim.version}")
            print("\n")

    def test_list_simulations_without_api_key(self, mock_adapter):
        """Test behavior when no API key is available."""
        # Ensure mock_adapter doesn't have SDK attributes so new SDK creation is attempted
        mock_adapter.api_token = None
        mock_adapter.simulation = None

        with patch("fluidize.managers.simulations.config") as mock_config:
            mock_config.api_key = None

            with pytest.raises(ValueError, match="API key is required"):
                SimulationsManager(mock_adapter)

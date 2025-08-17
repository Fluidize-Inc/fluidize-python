"""Integration tests for SimulationsManager - tests real API connectivity."""

import pytest

from fluidize.managers.simulations import SimulationsManager


class TestSimulationsManagerIntegration:
    """Integration test suite for SimulationsManager class."""

    @pytest.fixture
    def mock_adapter(self):
        """Create a mock adapter for testing."""
        from unittest.mock import Mock

        adapter = Mock()
        return adapter

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

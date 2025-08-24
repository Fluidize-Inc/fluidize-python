from typing import Any

from fluidize_sdk import FluidizeSDK

from fluidize.config import config
from fluidize.core.types.node import nodeMetadata_simulation


class SimulationsManager:
    """
    Simulations manager that provides access to the Fluidize simulation library.
    """

    def __init__(self, adapter: Any) -> None:
        """
        Args:
            adapter: adapter (FluidizeSDK or LocalAdapter)
        """
        self._adapter = adapter

        # Use the adapter if it's already a FluidizeSDK instance, otherwise create one
        if (
            hasattr(adapter, "api_token")
            and hasattr(adapter, "simulation")
            and adapter.api_token is not None
            and adapter.simulation is not None
        ):
            # Assume it's already a FluidizeSDK instance
            self.fluidize_sdk = adapter
        else:
            # Create FluidizeSDK with proper API key from config
            if not config.api_key:
                msg = "API key is required. Set the FLUIDIZE_API_KEY environment variable."
                raise ValueError(msg)
            self.fluidize_sdk = FluidizeSDK(api_token=config.api_key)

    def list_simulations(self) -> list[Any]:
        """
        List all simulations available in the Fluidize simulation library.

        Returns:
            List of simulation metadata
        """
        simulations = self.fluidize_sdk.simulation.list_simulations(sim_global=True)
        return [
            nodeMetadata_simulation.from_dict_and_path(data=simulation.model_dump(), path=None)
            for simulation in simulations
        ]

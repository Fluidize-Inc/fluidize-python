from typing import Any

from fluidize_sdk import FluidizeSDK

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
        # TODO: Fix hardcoding of api_token and remove type ignore
        self.fluidize_sdk = FluidizeSDK(api_token="placeholder")  # noqa: S106

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

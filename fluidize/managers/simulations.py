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
        self.fluidize_sdk = FluidizeSDK()

    def list_simulations(self) -> list[Any]:
        """
        List all simulations available in the Fluidize simulation library.

        Returns:
            List of simulation metadata
        """
        simulations = self.fluidize_sdk.graph.list_simulations(sim_global=True)
        return [nodeMetadata_simulation.from_dict_and_path(data=simulation, path=None) for simulation in simulations]

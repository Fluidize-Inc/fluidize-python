import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from fluidize.core.types.node import nodeProperties_simulation
from fluidize.core.types.project import ProjectSummary


class BaseExecutionStrategy(ABC):
    def __init__(
        self,
        node: nodeProperties_simulation,
        prev_node: Optional[nodeProperties_simulation],
        project: ProjectSummary,
        mlflow_tracker: Any = None,
        run_id: Optional[str] = None,
        run_metadata: Any = None,
    ) -> None:
        self.node = node
        self.prev_node = prev_node
        self.project = project
        self.mlflow_tracker = mlflow_tracker
        self.run_id = run_id
        self.run_metadata = run_metadata

    def set_context(
        self,
        nodeProperties_simulation: nodeProperties_simulation,
        prev_nodeProperties_simulation: Optional[nodeProperties_simulation],
        project: ProjectSummary,
    ) -> None:
        """Update the context for reusing the strategy instance"""
        self.node = nodeProperties_simulation
        self.prev_node = prev_nodeProperties_simulation
        self.project = project

    @abstractmethod
    def _set_environment(self) -> Any:
        """Load the environment for the node execution"""
        pass

    @abstractmethod
    def _load_execution_manager(self) -> Any:
        """Load the execution manager for the node"""
        pass

    def prepare_environment(self) -> None:
        self.env_manager = self._set_environment()

        # Load the parameters
        simulation_params, properties_params = self.env_manager.load_node_parameters()

        # Process the parameters with the environment manager
        self.env_manager.process_parameters(simulation_params, properties_params)

    def execute_simulation(self) -> Any:
        # Track execution time
        start_time = time.time()

        self.env_manager = self._load_execution_manager()
        result = self.env_manager.execute()

        # Log execution metrics to MLFlow
        if self.mlflow_tracker:
            try:
                execution_time = time.time() - start_time
                self.mlflow_tracker.log_metrics({
                    "execution_time_seconds": execution_time,
                })

                # Log execution mode
                execution_mode = self.__class__.__name__.replace("ExecutionStrategy", "").lower()
                self.mlflow_tracker.log_tag("execution_mode", execution_mode)

                # Log result status
                if isinstance(result, str):
                    success = "success" in result.lower()
                    self.mlflow_tracker.log_tag("execution_result", "success" if success else "failure")
                elif isinstance(result, bool):
                    self.mlflow_tracker.log_tag("execution_result", "success" if result else "failure")

            except Exception as e:
                # Don't fail the execution if MLFlow logging fails
                print(f"MLFlow logging failed: {e}")

        return result

    @abstractmethod
    def handle_files(self) -> None:
        """Handle file operations for the execution."""
        pass

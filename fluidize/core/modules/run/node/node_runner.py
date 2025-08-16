from typing import Optional

from fluidize.core.modules.run.node.methods.base.execstrat import BaseExecutionStrategy
from fluidize.core.modules.tracking.mlflow_tracker import MLFlowTracker
from fluidize.core.types import node
from fluidize.core.types.project import ProjectSummary


# RunJob now uses a strategy instance to dynamically choose behavior.
class RunJob:
    """
    A job that runs for a single node.
    """

    def __init__(
        self,
        project: ProjectSummary,
        strategyClass: type[BaseExecutionStrategy],
        nodeProperties_simulation: node.nodeProperties_simulation,
        prev_nodeProperties_simulation: Optional[node.nodeProperties_simulation] = None,
        mlflow_tracker: Optional[MLFlowTracker] = None,
        run_id: Optional[str] = None,
        run_metadata: Optional[object] = None,  # Add run metadata
    ):
        """
        Args:
            project: The project this node belongs to
            strategyClass: The strategy class to use for execution
            nodeProperties_simulation: The node properties to run
            prev_nodeProperties_simulation: The previous node properties (optional)
            mlflow_tracker: The MLflow tracker (optional)
            run_id: The run ID (optional)
            run_metadata: The run metadata (optional)
        """
        self.project = project
        self.nodeProperties_simulation = nodeProperties_simulation
        self.prev_nodeProperties_simulation = prev_nodeProperties_simulation
        self.mlflow_tracker = mlflow_tracker
        self.run_id = run_id
        self.run_metadata = run_metadata

        self.strategy = strategyClass(
            node=self.nodeProperties_simulation,
            prev_node=self.prev_nodeProperties_simulation,
            project=self.project,
            mlflow_tracker=self.mlflow_tracker,
            run_id=self.run_id,
            run_metadata=self.run_metadata,  # Pass metadata to strategy
        )

    def run(self) -> None:
        print(f"\n=== Starting run for node: {self.nodeProperties_simulation.node_id} ===")
        try:
            # Set context once at the beginning of the run
            # self.strategy.set_context(self.nodeProperties_simulation, self.prev_nodeProperties_simulation, self.project)

            print("1. Preparing environment...")
            self.strategy.prepare_environment()

            print("2. Executing simulation...")
            result = self.strategy.execute_simulation()

            print("3. Handling files...")
            self.strategy.handle_files()

            print(f"=== Run completed for node: {self.nodeProperties_simulation.node_id} with result: {result} ===\n")
        except Exception as e:
            print(f"ERROR during run execution: {e!s}")
            raise

from abc import ABC, abstractmethod
from pathlib import PurePosixPath
from typing import Any, Optional

from fluidize.core.types.node import nodeProperties_simulation
from fluidize.core.types.project import ProjectSummary
from fluidize.core.types.runs import ContainerPaths, NodePaths, RunStatus
from fluidize.core.utils.dataloader.data_loader import DataLoader


class BaseExecutionManager(ABC):
    def __init__(
        self, node: nodeProperties_simulation, prev_node: Optional[nodeProperties_simulation], project: ProjectSummary
    ) -> None:
        self.node = node
        self.prev_node = prev_node
        self.project = project
        self.node_paths, self.container_paths = self._get_paths_for_run()

    def _get_paths_for_run(self) -> tuple[NodePaths, ContainerPaths]:
        """Get all paths required for single-container execution. Returns NodePaths and ContainerPaths with all necessary paths."""
        node_path = self.node.directory
        prev_node_path = self.prev_node.directory if self.prev_node else None

        container_node_path = PurePosixPath(f"/mnt/{self.node.node_id!s}")
        # container_prev_node_path = PurePosixPath(f"/mnt/{self.prev_node.node_id}") if self.prev_node else None

        # This is run path -> outputs / previous node_id
        node_input_path = (
            prev_node_path.parent / "outputs" / f"{self.prev_node.node_id!s}"
            if self.prev_node and prev_node_path
            else None
        )
        container_node_input_path = PurePosixPath("/mnt/inputs") if self.prev_node else None

        # This is the output path setup
        node_output_path = node_path.parent / "outputs" / f"{self.node.node_id!s}"
        container_node_output_path = container_node_path / self.node.source_output_folder

        node_paths = NodePaths(
            node_path=node_path,
            simulation_path=node_path / self.node.simulation_mount_path,
            input_path=node_input_path,
            output_path=node_output_path,
        )

        container_paths = ContainerPaths(
            node_path=container_node_path,
            simulation_path=container_node_path / self.node.simulation_mount_path,
            input_path=container_node_input_path,
            output_path=container_node_output_path,
        )

        return node_paths, container_paths

    def _check_main_script_exists(self) -> bool:
        """Check if the main.sh script exists in the node's simulation path."""
        main_script_path = self.node.directory / "main.sh"
        return DataLoader.check_file_exists(main_script_path)

    def _initialize_run(self) -> bool:
        """Initialize the run by setting up paths and checking prerequisites."""
        # Check if main.sh exists
        if not self._check_main_script_exists():
            return False

        # Create output directory if it doesn't exist
        try:
            self.node_paths.output_path.mkdir(parents=True, exist_ok=True)
        except Exception:
            return False

        return True

    @abstractmethod
    def _execute_node(self) -> Any:
        """Abstract method to execute the node's main script. Should be implemented in subclasses."""
        pass

    def execute(self) -> bool:
        """Execute the simulation and return True only if successful."""
        if not self._initialize_run():
            self.node.edit(run_status=RunStatus.FAILED)
            return False

        # Execute the node's main script
        try:
            self.node.edit(run_status=RunStatus.RUNNING)
            result = self._execute_node()

            # Check if execution was successful
            if result == "success":
                self.node.edit(run_status=RunStatus.SUCCESS)
                return True
            else:
                print(f"❌ [BaseExecutionManager] Execution failed: {result}")
                self.node.edit(run_status=RunStatus.FAILED)
                return False

        except Exception as e:
            print(f"💥 [BaseExecutionManager] Exception during execution: {e!s}")
            self.node.edit(run_status=RunStatus.FAILED)
            return False

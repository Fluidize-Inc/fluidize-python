from typing import Optional

import fluidize.core.modules.run.node.methods.local.Environment as LocalEnvironment
from fluidize.core.modules.run.node.methods.base.execstrat import BaseExecutionStrategy
from fluidize.core.modules.run.node.methods.local.ExecuteNew import LocalExecutionManagerNew


class LocalExecutionStrategy(BaseExecutionStrategy):
    def __init__(  # type: ignore[no-untyped-def]
        self,
        node,
        prev_node,
        project,
        mlflow_tracker=None,
        run_id: Optional[str] = None,
        run_metadata=None,
    ) -> None:
        super().__init__(node, prev_node, project, mlflow_tracker, run_id, run_metadata)

    def _set_environment(self):  # type: ignore[no-untyped-def]
        return LocalEnvironment.LocalEnvironmentManager(
            node=self.node,
            prev_node=self.prev_node,
            project=self.project,
        )

    def _load_execution_manager(self):  # type: ignore[no-untyped-def]
        return LocalExecutionManagerNew(
            self.node,
            self.prev_node,
            self.project,
            self.run_id,
            self.run_metadata,
        )

    def handle_files(self) -> None:
        """Handle file operations for local execution."""
        # For local execution, file handling is done by the environment manager
        # This method can be extended in the future for specific file operations
        pass

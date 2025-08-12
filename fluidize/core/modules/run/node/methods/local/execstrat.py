from typing import Optional

import fluidize.core.modules.run.node.methods.local.Environment as LocalEnvironment
from fluidize.core.modules.run.node.methods.base.execstrat import BaseExecutionStrategy
from fluidize.core.modules.run.node.methods.local.ExecuteNew import LocalExecutionManagerNew


class LocalExecutionStrategy(BaseExecutionStrategy):
    def __init__(self, node, prev_node, project, mlflow_tracker=None, run_id: Optional[str] = None) -> None:
        super().__init__(node, prev_node, project, mlflow_tracker, run_id)

    def _set_environment(self):
        return LocalEnvironment.LocalEnvironmentManager(
            node=self.node,
            prev_node=self.prev_node,
            project=self.project,
        )

    def _load_execution_manager(self):
        return LocalExecutionManagerNew(
            self.node,
            self.prev_node,
            self.project,
            self.run_id,
        )

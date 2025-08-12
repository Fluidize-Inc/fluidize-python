import shutil
from pathlib import Path

from fluidize.core.modules.run.node.methods.local.execstrat import LocalExecutionStrategy
from fluidize.core.modules.run.project.methods.base import BaseProjectRunner
from fluidize.core.types.project import ProjectSummary
from fluidize.core.utils.retrieval.handler import register_handler


class LocalProjectRunner(BaseProjectRunner):
    """
    Handles the execution of a project run, coordinating multiple node executions
    within a single run folder.
    """

    def __init__(self, project: ProjectSummary) -> None:
        """Initialize the project runner with a project"""
        super().__init__(project)
        self.strategy = self.get_default_execution_strategy()

    def _get_run_number(self, runs_path: Path) -> int:
        """
        Helper function to find the next available run number
        in the specified runs directory.
        """
        run_numbers = [int(p.name.split("_")[1]) for p in runs_path.glob("run_*") if p.is_dir()]
        return 1 if not run_numbers else max(run_numbers) + 1

    def _copy_project_contents(self, source_path: Path, destination_path: Path) -> None:
        """
        Copy the contents of the project directory to the new run directory (excluding the 'run' directory).
        """
        for item in source_path.iterdir():
            if item.name != "runs":
                dest_item = destination_path / item.name
                if item.is_dir():
                    shutil.copytree(item, dest_item)
                else:
                    shutil.copy2(item, dest_item)

    def get_default_execution_strategy(self):  # type: ignore[no-untyped-def]
        return LocalExecutionStrategy


# Auto-register this handler when module is imported
register_handler("project_runner", "local", LocalProjectRunner)

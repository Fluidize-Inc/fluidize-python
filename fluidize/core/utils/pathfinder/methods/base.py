from abc import ABC, abstractmethod
from typing import Optional

from upath import UPath

from fluidize.core.constants import FileConstants
from fluidize.core.types.project import ProjectSummary


class BasePathFinder(ABC):
    @abstractmethod
    def get_projects_path(self) -> UPath:
        """Get the path to the projects directory"""
        pass

    def get_project_path(self, project: ProjectSummary) -> UPath:
        """Get the path to a specific project"""
        return self.get_projects_path() / project.id

    def get_project_metadata_path(self, project: ProjectSummary) -> UPath:
        """Get the path to the metadata file for a specific project"""
        return self.get_project_path(project) / FileConstants.METADATA_SUFFIX

    @abstractmethod
    def get_simulations_path(self, sim_global: bool) -> UPath:
        """Get the path to the simulations directory"""
        pass

    def get_simulation_path(self, simulation_id: str, sim_global: bool) -> UPath:
        """Get the path to a specific simulation within a project"""
        return self.get_simulations_path(sim_global) / simulation_id

    def get_runs_path(self, project: ProjectSummary) -> UPath:
        """Get the path to the runs directory for a specific project"""
        project_path = self.get_project_path(project)
        return project_path / "runs"

    def get_run_path(self, project: ProjectSummary, run_number: Optional[int] = None) -> UPath:
        """Get the path to a specific run within a project"""
        return self.get_runs_path(project) / f"run_{run_number}"

    def get_node_path(self, project: ProjectSummary, node_id: str, run_number: Optional[int] = None) -> UPath:
        """Get the directory for a specific node.

        If run_number is provided, it will return the path to the node corresponding to that run.
        If run_number is None, it will return the path to the node in the editor.

        """
        if run_number is not None:
            return self.get_runs_path(project) / f"run_{run_number}" / node_id
        # Without the run number it's the editor run path
        return self.get_project_path(project) / node_id

    def get_node_parameters_path(
        self, project: ProjectSummary, node_id: str, run_number: Optional[int] = None
    ) -> UPath:
        """Get the path to the parameters file for a specific node.

        If run_number is provided, it will return the path to the node parameters corresponding to that run.
        If run_number is None, it will return the path to the node parameters in the editor.

        """
        return self.get_node_path(project, node_id, run_number) / "parameters.json"

    def get_properties_path(self, project: ProjectSummary, node_id: str, run_number: Optional[int] = None) -> UPath:
        return self.get_node_path(project, node_id, run_number) / "properties.yaml"

    def get_node_output_path(self, project: ProjectSummary, run_number: int, node_id: str) -> UPath:
        """
        Get the path to the output directory for a specific node in a run.

        Args:
            project: The project containing the run
            run_number: The run number
            node_id: ID of the node

        Returns:
            Path to the node's output directory: {project_path}/runs/run_{run_number}/outputs/{node_id}/
        """
        return self.get_run_path(project, run_number) / FileConstants.OUTPUTS_DIR / node_id

    @abstractmethod
    def get_mlflow_tracking_uri(self) -> str:
        """Get the MLFlow tracking URI for this storage backend"""
        pass

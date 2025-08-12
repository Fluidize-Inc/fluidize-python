from typing import TYPE_CHECKING, Optional

from upath import UPath

from fluidize.core.types.project import ProjectSummary
from fluidize.core.utils.retrieval.handler import get_handler

if TYPE_CHECKING:
    pass


class PathFinder:
    def __init__(self) -> None:
        pass

    @classmethod
    def _get_handler(cls):  # type: ignore[no-untyped-def]
        return get_handler("pathfinder")

    # Get the directory of where the projects are stored
    @classmethod
    def get_projects_path(cls) -> UPath:
        return cls._get_handler().get_projects_path()  # type: ignore[no-any-return]

    @classmethod
    def get_project_path(cls, project: ProjectSummary) -> UPath:
        return cls._get_handler().get_project_path(project)  # type: ignore[no-any-return]

    @classmethod
    def get_project_metadata_path(cls, project: ProjectSummary) -> UPath:
        return cls._get_handler().get_project_metadata_path(project)  # type: ignore[no-any-return]

    @classmethod
    def get_simulations_path(cls, sim_global: bool) -> UPath:
        return cls._get_handler().get_simulations_path(sim_global)  # type: ignore[no-any-return]

    @classmethod
    def get_simulation_path(cls, simulation_id: str, sim_global: bool) -> UPath:
        return cls._get_handler().get_simulation_path(simulation_id, sim_global)  # type: ignore[no-any-return]

    @classmethod
    def get_runs_path(cls, project: ProjectSummary) -> UPath:
        return cls._get_handler().get_runs_path(project)  # type: ignore[no-any-return]

    @classmethod
    def get_run_path(cls, project: ProjectSummary, run_number: int) -> UPath:
        return cls._get_handler().get_run_path(project, run_number)  # type: ignore[no-any-return]

    @classmethod
    def get_node_path(cls, project: ProjectSummary, node_id: str, run_number: Optional[int] = None) -> UPath:
        return cls._get_handler().get_node_path(project, node_id, run_number)  # type: ignore[no-any-return]

    @classmethod
    def get_node_parameters_path(cls, project: ProjectSummary, node_id: str, run_number: Optional[int] = None) -> UPath:
        return cls._get_handler().get_node_parameters_path(project, node_id, run_number)  # type: ignore[no-any-return]

    @classmethod
    def get_properties_path(cls, project: ProjectSummary, node_id: str, run_number: Optional[int] = None) -> UPath:
        """
        Get the path to the properties file for a specific node in a project.
        """
        return cls._get_handler().get_properties_path(project, node_id, run_number)  # type: ignore[no-any-return]

    @classmethod
    def infer_cloud_bucket_and_path(cls, path: UPath) -> tuple[str, UPath]:
        """
        Infer the cloud storage bucket and path from a given UPath.

        Args:
            path (UPath): The path to infer the bucket and path from.

        Returns:
            tuple[str, UPath]: A tuple containing the bucket name and the inferred path.
        """
        return cls._get_handler().infer_cloud_bucket_and_path(path)  # type: ignore[no-any-return]

    @classmethod
    def get_mlflow_tracking_uri(cls) -> str:
        """
        Get the MLflow tracking URI based on the request context.

        Args:
            request (Request): The FastAPI request object.

        Returns:
            str: The MLflow tracking URI.
        """
        return cls._get_handler().get_mlflow_tracking_uri()  # type: ignore[no-any-return]

from upath import UPath

from fluidize.config import config
from fluidize.core.utils.retrieval.handler import register_handler

from .base import BasePathFinder


class LocalPathFinder(BasePathFinder):
    def get_projects_path(self) -> UPath:
        """Get the path to the projects directory for local storage"""
        return UPath(config.local_projects_path)

    def get_simulations_path(self, sim_global: bool) -> UPath:
        return UPath(config.local_simulations_path)

    def get_mlflow_tracking_uri(self) -> str:
        """Get the MLFlow tracking URI for local storage"""
        return f"file://{config.local_base_path.resolve()}/mlruns"


# Auto-register this handler when module is imported
register_handler("pathfinder", "local", LocalPathFinder)

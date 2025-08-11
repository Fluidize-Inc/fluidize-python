"""
Local backend implementation - aggregates all local handlers.
"""

from typing import Any

from .graph import GraphHandler
from .projects import ProjectsHandler


class LocalBackend:
    """
    Local backend that provides SDK-compatible interface using local handlers.

    Organized like FluidizeSDK:
    - backend.projects.list()
    - backend.graph.retrieve()  (TODO)
    - backend.runs.run_flow()   (TODO)
    """

    def __init__(self, config: Any) -> None:
        """
        Initialize the local backend with all handlers.

        Args:
            config: FluidizeConfig instance
        """
        self.config = config

        # Initialize handlers (like SDK resources)
        self.projects = ProjectsHandler(config)

        self.graph = GraphHandler()
        # self.runs = RunsHandler(config)

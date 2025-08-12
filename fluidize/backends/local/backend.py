"""
Local backend implementation - aggregates all local handlers.
"""

from typing import Any

from .graph import GraphHandler
from .projects import ProjectsHandler
from .runs import RunsHandler


class LocalBackend:
    """
    Local backend that provides SDK-compatible interface using local handlers.

    """

    def __init__(self, config: Any) -> None:
        """
        Initialize the local backend with all handlers.

        Args:
            config: FluidizeConfig instance
        """
        self.config = config

        self.projects = ProjectsHandler(config)
        self.graph = GraphHandler()
        self.runs = RunsHandler(config)

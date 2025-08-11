from typing import Any

from upath import UPath

from fluidize.core.types.project import ProjectSummary
from fluidize.core.utils.retrieval.handler import get_handler


class DataWriter:
    def __init__(self) -> None:
        pass

    @classmethod
    def _get_handler(cls) -> Any:
        return get_handler("datawriter")

    @classmethod
    def write_json_for_project(cls, project: ProjectSummary, suffix: str, data: dict) -> bool:
        """
        Writes the given `data` to JSON for the given `project`.
        """
        return cls._get_handler().write_json_for_project(project, suffix, data)

    @classmethod
    def write_json(cls, filepath: UPath, data: dict) -> bool:
        """
        Writes JSON data to the specified path, handling root-level files correctly.
        This is a more generic method that properly handles paths based on the file type.

        Note that the mode parameter is legacy and needs to be removed.
        """
        return cls._get_handler().write_json(filepath, data)

    @classmethod
    def write_yaml(cls, filepath: UPath, data: dict) -> bool:
        """
        Writes YAML data to the specified path.

        Args:
            filepath: Path to the YAML file
            data: Data to write in YAML format

        Returns:
            bool: True if successful, False otherwise
        """
        return cls._get_handler().write_yaml(filepath, data)

    @classmethod
    def create_directory(cls, directory_path: UPath) -> bool:
        """
        Creates a directory along with any necessary parent directories.
        Automatically handles local or cluster storage based on the current mode.

        Args:
            directory_path: Path to the directory to create

        Returns:
            bool: True if successful, False otherwise
        """
        return cls._get_handler().create_directory(directory_path)

    @classmethod
    def save_simulation(cls, simulation, sim_global: bool = True) -> dict:
        """
        Saves a new simulation with the given simulation object.

        Args:
            simulation: The Simulation object containing all simulation data

        Returns:
            Dict with status and simulation name
        """
        return cls._get_handler().save_simulation(simulation, sim_global)

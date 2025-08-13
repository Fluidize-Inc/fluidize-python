from abc import ABC, abstractmethod
from typing import Union

from upath import UPath

from fluidize.core.types.project import ProjectSummary
from fluidize.core.utils.pathfinder.path_finder import PathFinder


class BaseDataWriter(ABC):
    """
    Base class for all data writers. Implements higher-level operations using primitive
    methods that must be implemented by subclasses.
    """

    def write_json_for_project(self, project: ProjectSummary, suffix: str, data: dict) -> None:
        """
        Writes the given data to JSON for the given project.
        """
        project_path = PathFinder.get_project_path(project)
        # build file path using UPath
        file_path: UPath = project_path / suffix
        dir_path = file_path.parent

        self._ensure_directory_exists(dir_path)
        self._write_json_file(file_path, data)

    def write_json(self, filepath: Union[str, UPath], data: dict) -> None:
        """
        Writes JSON data to the specified file path.
        """
        path = UPath(filepath) if not isinstance(filepath, UPath) else filepath
        dir_path = path.parent
        self._ensure_directory_exists(dir_path)
        self._write_json_file(path, data)

    def write_yaml(self, filepath: UPath, data: dict) -> None:
        """
        Writes YAML data to the specified file path.

        Args:
            filepath: Path to the YAML file
            data: Data to write in YAML format

        Returns:
            None
        """
        path = UPath(filepath) if not isinstance(filepath, UPath) else filepath
        dir_path = path.parent
        self._ensure_directory_exists(dir_path)
        self._write_yaml(path, data)

    def write_text(self, filepath: UPath, data: str) -> None:
        """
        Writes text data to the specified file path.

        Args:
            filepath: Path to the text file
            data: Text data to write

        Returns:
            None
        """
        path = UPath(filepath) if not isinstance(filepath, UPath) else filepath
        dir_path = path.parent
        self._ensure_directory_exists(dir_path)
        self._write_text_file(path, data)

    def create_directory(self, directory_path: UPath) -> bool:
        """
        Creates a directory along with any necessary parent directories.

        Args:
            directory_path: Path to the directory to create
            request: Optional request object

        Returns:
            bool: True if successful, False otherwise
        """
        return self._ensure_directory_exists(directory_path)

    # TODO
    # def save_simulation(self, simulation, sim_global) -> dict:
    #     # Get simulation path
    #     sim_path = PathFinder.get_simulations_path(sim_global) / simulation.name

    #     # Create simulation directory
    #     self._ensure_directory_exists(sim_path)

    #     # Generate all node files
    #     generator = GenerateNode()
    #     file_definitions = generator.generate_node_files(simulation)

    #     # Write all files using the appropriate writer method
    #     for file_def in file_definitions:
    #         file_path = sim_path / file_def['filename']
    #         if not self._write_text_file(file_path, file_def['content']):
    #             raise Exception(f"Failed to write file: {file_path}")

    #     return {
    #         "status": "success",
    #         "simulation_name": simulation.name,
    #         "files_written": [f['filename'] for f in file_definitions]
    #     }

    # Abstract primitive operations that must be implemented by subclasses
    @abstractmethod
    def _ensure_directory_exists(self, dir_path: UPath) -> bool:
        """
        Ensures that the specified directory exists.
        Creates it if it doesn't exist.

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def _write_json_file(self, file_path: UPath, data: dict) -> bool:
        """
        Writes JSON data to the specified file path.

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def _write_text_file(self, file_path: UPath, data: str) -> bool:
        """
        Writes text data to the specified file path.

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def _write_yaml(self, file_path: UPath, data: dict) -> bool:
        """
        Writes YAML data to the specified file path.

        Returns:
            bool: True if successful, False otherwise
        """
        pass

from typing import Optional

from upath import UPath

from fluidize.core.modules.run.node.methods.base.Environment import BaseEnvironmentManager
from fluidize.core.types.node import nodeProperties_simulation
from fluidize.core.types.project import ProjectSummary


class LocalEnvironmentManager(BaseEnvironmentManager):
    def __init__(
        self, node: nodeProperties_simulation, prev_node: Optional[nodeProperties_simulation], project: ProjectSummary
    ) -> None:
        super().__init__(node, prev_node, project)

    def _get_file_content(self, loc: UPath) -> str:
        """Helper method to read file content."""
        with open(loc) as f:
            content = f.read()
        return content

    def _write_file_content(self, loc: UPath, content: str) -> None:
        with open(loc, "w") as f:
            f.write(content)

    def _should_process_file(self, file_path: UPath) -> bool:
        """Determine if a file should be processed for parameter substitution in local storage."""
        try:
            # Skip if file is too large (over 10MB) to avoid memory issues
            if file_path.stat().st_size > 10 * 1024 * 1024:
                return False

            # Skip common binary file extensions
            binary_extensions = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".zip", ".tar", ".gz", ".exe", ".bin"}
            return file_path.suffix.lower() not in binary_extensions
        except (OSError, PermissionError):
            # If we can't access the file, skip it
            return False

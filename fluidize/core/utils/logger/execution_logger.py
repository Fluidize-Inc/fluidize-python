"""
Execution Logger

Utility for saving execution logs (stdout/stderr) from various execution modes.
This module provides a centralized way to persist execution logs to files
using the PathFinder and DataWriter utilities.
"""

import logging
from typing import Optional

from fluidize.core.types.project import ProjectSummary
from fluidize.core.utils.dataloader.data_writer import DataWriter
from fluidize.core.utils.pathfinder.path_finder import PathFinder

logger = logging.getLogger(__name__)


class ExecutionLogger:
    """
    Centralized execution log management for all execution modes.

    This class provides static methods for saving execution logs
    from Docker, VM, and other execution environments.
    """

    @classmethod
    def save_execution_logs(
        cls,
        project: ProjectSummary,
        run_metadata: Optional[object],
        node_id: str,
        stdout: str,
        stderr: str,
    ) -> bool:
        """
        Save both stdout and stderr logs for a node execution.

        Args:
            project: Project information
            run_metadata: Run metadata containing run_number
            node_id: Node identifier
            stdout: Standard output content
            stderr: Standard error content

        Returns:
            True if logs were saved successfully, False otherwise
        """
        if not cls._validate_run_metadata(run_metadata):
            logger.warning("No valid run metadata available, skipping log file saving")
            return False

        try:
            # Create nodes log directory
            run_number = run_metadata.run_number  # type: ignore[union-attr]
            nodes_log_dir = PathFinder.get_logs_path(project, run_number) / "nodes"
            DataWriter.create_directory(nodes_log_dir)

            # Save both stdout and stderr
            stdout_saved = cls.save_stdout(project, run_metadata, node_id, stdout)
            stderr_saved = cls.save_stderr(project, run_metadata, node_id, stderr)

            return stdout_saved or stderr_saved  # Success if at least one was saved

        except Exception as e:
            logger.warning(f"Failed to save execution logs for node {node_id}: {e}")
            return False

    @classmethod
    def save_stdout(
        cls,
        project: ProjectSummary,
        run_metadata: Optional[object],
        node_id: str,
        stdout: str,
    ) -> bool:
        """
        Save stdout log for a node execution.

        Args:
            project: Project information
            run_metadata: Run metadata containing run_number
            node_id: Node identifier
            stdout: Standard output content

        Returns:
            True if stdout was saved successfully, False otherwise
        """
        if not cls._validate_run_metadata(run_metadata) or not stdout:
            return False

        try:
            run_number = run_metadata.run_number  # type: ignore[union-attr]
            stdout_path = PathFinder.get_log_path(project, run_number, node_id, "stdout")
            DataWriter.write_text(stdout_path, stdout)
            logger.info(f"Saved stdout log to: {stdout_path}")
            return True

        except Exception as e:
            logger.warning(f"Failed to save stdout log for node {node_id}: {e}")
            return False

    @classmethod
    def save_stderr(
        cls,
        project: ProjectSummary,
        run_metadata: Optional[object],
        node_id: str,
        stderr: str,
    ) -> bool:
        """
        Save stderr log for a node execution.

        Args:
            project: Project information
            run_metadata: Run metadata containing run_number
            node_id: Node identifier
            stderr: Standard error content

        Returns:
            True if stderr was saved successfully, False otherwise
        """
        if not cls._validate_run_metadata(run_metadata) or not stderr:
            return False

        try:
            run_number = run_metadata.run_number  # type: ignore[union-attr]
            stderr_path = PathFinder.get_log_path(project, run_number, node_id, "stderr")
            DataWriter.write_text(stderr_path, stderr)
            logger.info(f"Saved stderr log to: {stderr_path}")
            return True

        except Exception as e:
            logger.warning(f"Failed to save stderr log for node {node_id}: {e}")
            return False

    @classmethod
    def _validate_run_metadata(cls, run_metadata: Optional[object]) -> bool:
        """
        Validate that run metadata has the required run_number attribute.

        Args:
            run_metadata: Run metadata object to validate

        Returns:
            True if run_metadata is valid, False otherwise
        """
        return (
            run_metadata is not None
            and hasattr(run_metadata, "run_number")
            and run_metadata.run_number is not None
        )

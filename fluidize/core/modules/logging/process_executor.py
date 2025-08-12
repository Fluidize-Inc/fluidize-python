"""
Process executor with integrated log streaming.

Provides a clean abstraction for executing shell commands with automatic
log broadcasting support.
"""

import subprocess
from typing import Optional

from .log_broadcaster import log_broadcaster  # type: ignore[import-untyped]


class ProcessExecutor:
    """Execute processes with automatic log streaming to broadcaster."""

    def __init__(self, run_id: Optional[str] = None, node_id: Optional[str] = None):
        self.run_id = run_id
        self.node_id = node_id

    def execute_with_logging(self, command: str, description: str = "Process") -> tuple[str, bool]:
        """
        Execute a command with automatic log streaming.

        Args:
            command: Shell command to execute
            description: Human-readable description for logging

        Returns:
            Tuple of (result_message, success_bool)
        """
        try:
            # Log start
            if self.run_id:
                log_broadcaster.broadcast_log_sync(self.run_id, self.node_id, f"Starting: {description}", "INFO")

            # Execute command
            # Note: shell=True is needed for command execution but validated command sources should be used
            process = subprocess.Popen(  # noqa: S602
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Stream output
            if process.stdout:
                for line in process.stdout:
                    line = line.rstrip("\n")
                    if line and self.run_id:  # Only broadcast non-empty lines
                        log_broadcaster.broadcast_log_sync(self.run_id, self.node_id, line, "INFO")

            # Check result
            return_code = process.wait()

            if return_code == 0:
                if self.run_id:
                    log_broadcaster.broadcast_log_sync(self.run_id, self.node_id, f"Completed: {description}", "INFO")
                return "success", True
            else:
                error_msg = f"{description} failed with return code: {return_code}"
                if self.run_id:
                    log_broadcaster.broadcast_log_sync(self.run_id, self.node_id, error_msg, "ERROR")
                return f"failure: {error_msg}", False

        except Exception as e:
            error_msg = f"{description} failed: {e!s}"
            if self.run_id:
                log_broadcaster.broadcast_log_sync(self.run_id, self.node_id, error_msg, "ERROR")
            return f"failure: {error_msg}", False

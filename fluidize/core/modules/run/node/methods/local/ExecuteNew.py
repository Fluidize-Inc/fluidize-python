"""
New LocalExecutionManager using Universal Container Builder

This replaces the old string-based Docker command construction with
the new type-safe utilities and proper Docker SDK.
"""

import logging
from typing import Optional

from fluidize.core.modules.execute.docker_client import DockerExecutionClient
from fluidize.core.modules.execute.utilities import UniversalContainerBuilder
from fluidize.core.modules.run.node.methods.base.Execute import BaseExecutionManager
from fluidize.core.types.execution_models import ExecutionMode, create_execution_context
from fluidize.core.types.node import nodeProperties_simulation
from fluidize.core.types.project import ProjectSummary
from fluidize.core.types.runs import ContainerPaths, NodePaths
from fluidize.core.utils.logger.execution_logger import ExecutionLogger

logger = logging.getLogger(__name__)


class LocalExecutionManagerNew(BaseExecutionManager):
    """
    Enhanced LocalExecutionManager using the new universal utilities.

    This version:
    - Uses UniversalContainerBuilder for proper specification creation
    - Uses DockerExecutionClient with Docker SDK (no more unsafe strings)
    - Maintains the same interface as BaseExecutionManager
    - Provides better error handling and validation
    """

    def __init__(
        self,
        node: nodeProperties_simulation,
        prev_node: Optional[nodeProperties_simulation],
        project: ProjectSummary,
        run_id: Optional[str] = None,
        run_metadata: Optional[object] = None,
    ) -> None:
        super().__init__(node, prev_node, project)
        self.run_id = run_id
        self.run_metadata = run_metadata
        self.docker_client: Optional[DockerExecutionClient] = None
        logger.info(f"LocalExecutionManagerNew initialized for node: {node.node_id}")
        logger.info(f"run_metadata type: {type(self.run_metadata)}")
        if hasattr(self.run_metadata, "run_number"):
            logger.info(f"run_metadata.run_number: {self.run_metadata.run_number}")
        else:
            logger.info("run_metadata does not have run_number attribute")

    def print_job_info(self) -> None:
        """Log information about the job being executed"""
        logger.info(f"Executing node: {self.node.node_id}")
        logger.info(f"Container image: {self.node.container_image}")
        logger.info(f"Project: {self.project.id}")
        if self.prev_node:
            logger.info(f"Previous node: {self.prev_node.node_id}")

    def _execute_node(self) -> str:
        """
        Main execution method using new universal utilities.

        This replaces the old manual Docker command building with
        proper type-safe utilities.

        Returns:
            "success" if successful, error message if failed
        """
        try:
            self.print_job_info()

            # Step 1: Create execution context
            logger.info("Creating execution context...")
            context = create_execution_context(
                node=self.node,
                project=self.project,
                prev_node=self.prev_node,
                execution_mode=ExecutionMode.LOCAL_DOCKER,
                run_id=self.run_id,
            )

            # Step 2: Build universal container specification
            logger.info("Building container specification...")
            spec = UniversalContainerBuilder.build_container_spec(context)

            # Step 3: Validate specification
            logger.info("Validating specification...")
            validation = UniversalContainerBuilder.validate_spec(spec)

            if validation["errors"]:
                error_msg = f"Specification validation failed: {validation['errors']}"
                logger.error(error_msg)
                return f"failure: {error_msg}"

            # Log warnings
            for warning in validation.get("warnings", []):
                logger.warning(f"Specification warning: {warning}")

            # Step 4: Initialize Docker client and pull image
            logger.info("Initializing Docker client...")
            if not self.docker_client:
                self.docker_client = DockerExecutionClient()

            logger.info(f"Pulling Docker image: {spec.container_spec.image}")
            if not self.docker_client.pull_image(spec.container_spec.image):
                return f"failure: Failed to pull Docker image: {spec.container_spec.image}"

            # Step 5: Execute container using Docker SDK
            logger.info("Executing container...")
            result = self.docker_client.run_container(
                spec.container_spec, spec.volume_spec.volumes if spec.volume_spec else []
            )

            # Step 6: Save execution logs
            ExecutionLogger.save_execution_logs(
                self.project, self.run_metadata, str(self.node.node_id), result.stdout, result.stderr
            )

            # Step 7: Handle results
            if result.success:
                logger.info("Container execution completed successfully")
                logger.debug(f"Container stdout: {result.stdout}")
                return "success"
            else:
                error_msg = f"Container execution failed (exit code {result.exit_code}): {result.stderr}"
                logger.error(error_msg)
                logger.debug(f"Container stdout: {result.stdout}")
                return f"failure: {error_msg}"

        except Exception as e:
            error_msg = f"Exception during node execution: {e!s}"
            logger.error(error_msg, exc_info=True)
            return f"failure: {error_msg}"

        finally:
            # Clean up Docker client
            pass
            # if self.docker_client:
            #     self.docker_client.close()

    def run_container(self, node_paths: NodePaths, container_paths: ContainerPaths) -> tuple[str, bool]:
        """
        Legacy method for backwards compatibility.

        This method is called by the old code but now delegates to
        the new _execute_node() implementation.
        """
        logger.warning("run_container() called - this is legacy method, using new implementation")
        result = self._execute_node()
        success = result == "success"
        return result, success

    def pull_docker_image(self) -> bool:
        """
        Legacy method for backwards compatibility.

        Image pulling is now handled inside _execute_node() but we
        keep this method for any legacy code that might call it.
        """
        logger.warning("pull_docker_image() called - this is legacy method")
        try:
            if not self.docker_client:
                self.docker_client = DockerExecutionClient()
            return bool(self.docker_client.pull_image(self.node.container_image))
        except Exception:
            logger.exception("Failed to pull image")
            return False

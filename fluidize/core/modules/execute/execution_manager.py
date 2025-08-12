"""
Execution Manager

Integration layer that bridges the gap between ExecutionContext and existing
execution clients. This allows existing code to easily use the new utilities.
"""

import logging
from typing import Any, Optional

from fluidize.core.types.execution_models import ExecutionMode, create_execution_context
from fluidize.core.types.node import nodeProperties_simulation
from fluidize.core.types.project import ProjectSummary

from .docker_client import DockerExecutionClient
from .kubernetes_client import KubernetesExecutionClient
from .utilities.universal_builder import UniversalContainerBuilder
from .vm_client import VMExecutionClient

logger = logging.getLogger(__name__)


class ExecutionManager:
    """
    High-level execution manager that coordinates between utilities and clients.

    This is the main integration point that existing code can use to execute
    containers using the new universal utilities.
    """

    def __init__(self):
        """Initialize execution manager."""
        self.docker_client = None
        self.k8s_client = None
        self.vm_client = None
        logger.info("ExecutionManager initialized")

    def execute_node(
        self,
        project: ProjectSummary,
        node: nodeProperties_simulation,
        prev_node: Optional[nodeProperties_simulation] = None,
        execution_mode: ExecutionMode = ExecutionMode.LOCAL_DOCKER,
        run_number: Optional[int] = None,
        run_id: Optional[str] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute a node using the new universal utilities.

        This is the main entry point that existing code can use.

        Args:
            project: Project information
            node: Node to execute
            prev_node: Previous node (for dependencies)
            execution_mode: How to execute the container
            run_number: Run number (optional)
            run_id: Run ID (optional)
            **kwargs: Additional execution options

        Returns:
            Execution result dictionary with success status and details
        """
        try:
            logger.info(f"Executing node {node.node_id} in {execution_mode.value} mode")

            # Step 1: Create execution context
            context = create_execution_context(
                node=node,
                project=project,
                prev_node=prev_node,
                execution_mode=execution_mode,
                run_number=run_number,
                run_id=run_id,
                **kwargs,
            )

            # Step 2: Build universal container specification
            spec = UniversalContainerBuilder.build_container_spec(context)

            # Step 3: Validate the specification
            validation = UniversalContainerBuilder.validate_spec(spec)
            if validation["errors"]:
                error_msg = f"Specification validation failed: {validation['errors']}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "validation": validation}

            # Log warnings if any
            if validation["warnings"]:
                for warning in validation["warnings"]:
                    logger.warning(f"Specification warning: {warning}")

            # Step 4: Execute based on mode
            result = self._execute_with_mode(context.execution_mode, spec, **kwargs)

            logger.info(f"Node {node.node_id} execution completed: {result.get('success', False)}")
        except Exception as e:
            logger.error(f"Node execution failed: {e}", exc_info=True)
            return {"success": False, "error": str(e), "node_id": node.node_id}
        else:
            return result

    def _execute_with_mode(self, execution_mode: ExecutionMode, spec, **kwargs) -> dict[str, Any]:
        """Execute using the appropriate client based on execution mode."""

        if execution_mode == ExecutionMode.LOCAL_DOCKER:
            return self._execute_docker(spec, **kwargs)

        elif execution_mode == ExecutionMode.VM_DOCKER:
            return self._execute_vm(spec, **kwargs)

        elif execution_mode == ExecutionMode.KUBERNETES:
            return self._execute_kubernetes(spec, **kwargs)

        elif execution_mode == ExecutionMode.CLOUD_BATCH:
            # Could integrate with existing batch execution
            logger.warning("Cloud Batch execution not yet implemented, falling back to VM")
            return self._execute_vm(spec, **kwargs)

        else:
            return {"success": False, "error": f"Unsupported execution mode: {execution_mode.value}"}

    def _execute_docker(self, spec, **kwargs) -> dict[str, Any]:
        """Execute using Docker client."""
        try:
            if not self.docker_client:
                self.docker_client = DockerExecutionClient()

            # Pull image first
            if not self.docker_client.pull_image(spec.container_spec.image):
                return {"success": False, "error": f"Failed to pull image: {spec.container_spec.image}"}

            # Execute container
            result = self.docker_client.run_container(spec.container_spec, spec.volume_spec.volumes, **kwargs)
        except Exception as e:
            logger.exception("Docker execution failed")
            return {"success": False, "error": str(e), "execution_mode": "local_docker"}
        else:
            return {
                "success": result.success,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "container_id": result.container_id,
                "execution_mode": "local_docker",
            }

    def _execute_vm(self, spec, **kwargs) -> dict[str, Any]:
        """Execute using VM client."""
        try:
            if not self.vm_client:
                self.vm_client = VMExecutionClient()

            # Execute container on VM
            result = self.vm_client.run_container(spec.container_spec, spec.volume_spec.volumes, **kwargs)
        except Exception as e:
            logger.exception("VM execution failed")
            return {"success": False, "error": str(e), "execution_mode": "vm_docker"}
        else:
            return {
                "success": result.success,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": result.command,
                "execution_mode": "vm_docker",
            }

    def _execute_kubernetes(self, spec, **kwargs) -> dict[str, Any]:
        """Execute using Kubernetes client."""
        try:
            if not self.k8s_client:
                namespace = kwargs.get("namespace", "fluidize")
                self.k8s_client = KubernetesExecutionClient(namespace=namespace)

            # Generate job name
            job_name = f"fluidize-{spec.container_spec.name}-{kwargs.get('timestamp', 'job')}"
            job_name = job_name.lower().replace("_", "-")[:63]  # K8s name limits

            # Submit Kubernetes job
            result = self.k8s_client.submit_job(spec.pod_spec, job_name, **kwargs)
        except Exception as e:
            logger.exception("Kubernetes execution failed")
            return {"success": False, "error": str(e), "execution_mode": "kubernetes"}
        else:
            return {
                "success": result.success,
                "job_name": result.job_name,
                "namespace": result.namespace,
                "logs": result.logs,
                "exit_code": result.exit_code,
                "start_time": result.start_time,
                "completion_time": result.completion_time,
                "failure_reason": result.failure_reason,
                "execution_mode": "kubernetes",
            }

    def close(self):
        """Clean up resources."""
        if self.docker_client:
            self.docker_client.close()
        if self.vm_client:
            self.vm_client.close()
        # K8s client doesn't need explicit cleanup

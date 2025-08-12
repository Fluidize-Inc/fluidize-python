"""
Environment Builder

Handles construction of environment variables for all execution methods.
Provides consistent environment variable building across local, VM, K8s, and Argo execution.
"""

from fluidize.core.types.execution_models import ExecutionContext
from fluidize.core.types.runs import ContainerPaths


class EnvironmentBuilder:
    """
    Builds environment variables from ExecutionContext.

    This class centralizes all environment variable construction logic,
    ensuring consistency across all execution methods.
    """

    @staticmethod
    def build_complete_env_vars(context: ExecutionContext, container_paths: ContainerPaths) -> dict[str, str]:
        """
        Build complete set of environment variables for container execution.

        Args:
            context: Execution context with node and project info
            container_paths: Container filesystem paths

        Returns:
            Complete dictionary of environment variables
        """
        env_vars = {}

        # Start with standard Fluidize environment variables
        env_vars.update(EnvironmentBuilder.build_standard_fluidize_env_vars(context))

        # Add path-related environment variables
        env_vars.update(EnvironmentBuilder.build_path_env_vars(context, container_paths))

        # Add workflow context if available
        if context.workflow_context:
            env_vars.update(EnvironmentBuilder.build_workflow_env_vars(context))

        # Add custom environment variables
        env_vars.update(context.custom_env_vars)

        return env_vars

    @staticmethod
    def build_standard_fluidize_env_vars(context: ExecutionContext) -> dict[str, str]:
        """
        Build standard Fluidize environment variables.

        Args:
            context: Execution context

        Returns:
            Standard Fluidize environment variables
        """
        env_vars = {
            "FLUIDIZE_NODE_ID": context.node.node_id,
            "FLUIDIZE_PROJECT_ID": context.project.id,
            "FLUIDIZE_PROJECT_LABEL": context.project.label,
            "FLUIDIZE_EXECUTION_MODE": context.execution_mode.value,
            "FLUIDIZE_CONTAINER_IMAGE": context.node.container_image,
        }

        # Add run context if available
        if context.run_id:
            env_vars["FLUIDIZE_RUN_ID"] = context.run_id
        if context.run_number:
            env_vars["FLUIDIZE_RUN_NUMBER"] = str(context.run_number)

        # Add dependency information
        if context.dependencies:
            env_vars["FLUIDIZE_DEPENDENCIES"] = ",".join(context.dependencies)
            env_vars["FLUIDIZE_HAS_DEPENDENCIES"] = "true"
        else:
            env_vars["FLUIDIZE_HAS_DEPENDENCIES"] = "false"

        # Add resource information
        if context.resource_requirements:
            env_vars["FLUIDIZE_REQUIRES_GPU"] = "true" if context.requires_gpu() else "false"
            env_vars["FLUIDIZE_NODE_POOL"] = context.get_node_pool()

        return env_vars

    @staticmethod
    def build_path_env_vars(context: ExecutionContext, container_paths: ContainerPaths) -> dict[str, str]:
        """
        Build path-related environment variables.

        Args:
            context: Execution context
            container_paths: Container filesystem paths

        Returns:
            Path-related environment variables
        """
        env_vars = {
            "FLUIDIZE_NODE_PATH": str(container_paths.node_path),
            "FLUIDIZE_SIMULATION_PATH": str(container_paths.simulation_path),
            "FLUIDIZE_OUTPUT_PATH": str(container_paths.output_path),
        }

        # Add input path if there are dependencies
        if container_paths.input_path:
            env_vars["FLUIDIZE_INPUT_PATH"] = str(container_paths.input_path)

        # Add node-specific paths
        env_vars["FLUIDIZE_SOURCE_OUTPUT_FOLDER"] = context.node.source_output_folder
        env_vars["FLUIDIZE_SIMULATION_MOUNT_PATH"] = context.node.simulation_mount_path

        return env_vars

    @staticmethod
    def build_workflow_env_vars(context: ExecutionContext) -> dict[str, str]:
        """
        Build workflow-related environment variables.

        Args:
            context: Execution context with workflow context

        Returns:
            Workflow-related environment variables
        """
        if not context.workflow_context:
            return {}

        workflow = context.workflow_context

        env_vars = {
            "FLUIDIZE_WORKFLOW_ID": workflow.workflow_id,
            "FLUIDIZE_WORKFLOW_NAME": workflow.workflow_name,
            "FLUIDIZE_STEP_NAME": workflow.step_name,
            "FLUIDIZE_EXECUTION_ORDER": str(workflow.execution_order),
        }

        # Add parallel group if available
        if workflow.parallel_group:
            env_vars["FLUIDIZE_PARALLEL_GROUP"] = workflow.parallel_group

        # Add dependency information
        if workflow.depends_on:
            env_vars["FLUIDIZE_WORKFLOW_DEPENDENCIES"] = ",".join(workflow.depends_on)

        # Add failure handling
        env_vars["FLUIDIZE_CONTINUE_ON_FAILURE"] = "true" if workflow.continue_on_failure else "false"

        return env_vars

    @staticmethod
    def build_kubernetes_env_list(env_vars: dict[str, str]) -> list[dict[str, str]]:
        """
        Convert environment variables to Kubernetes env list format.

        Args:
            env_vars: Dictionary of environment variables

        Returns:
            List of Kubernetes env objects
        """
        return [{"name": key, "value": value} for key, value in env_vars.items()]

    @staticmethod
    def build_docker_env_args(env_vars: dict[str, str]) -> list[str]:
        """
        Convert environment variables to Docker CLI argument format.

        Args:
            env_vars: Dictionary of environment variables

        Returns:
            List of Docker -e arguments
        """
        docker_args = []
        for key, value in env_vars.items():
            docker_args.extend(["-e", f"{key}={value}"])
        return docker_args

    @staticmethod
    def validate_env_vars(env_vars: dict[str, str]) -> dict[str, list[str]]:
        """
        Validate environment variables for completeness and correctness.

        Args:
            env_vars: Environment variables to validate

        Returns:
            Dictionary with 'errors', 'warnings', and 'info' lists
        """
        errors = []
        warnings = []
        info = []

        # Use helper methods to reduce complexity
        errors.extend(EnvironmentBuilder._validate_required_vars(env_vars))
        warnings.extend(EnvironmentBuilder._validate_path_vars(env_vars))
        warnings.extend(EnvironmentBuilder._validate_workflow_vars(env_vars))
        warnings.extend(EnvironmentBuilder._validate_dependencies(env_vars))
        warnings.extend(EnvironmentBuilder._validate_gpu_requirements(env_vars))
        info.extend(EnvironmentBuilder._collect_info(env_vars))

        return {"errors": errors, "warnings": warnings, "info": info}

    @staticmethod
    def _validate_required_vars(env_vars: dict[str, str]) -> list[str]:
        """Validate required environment variables."""
        errors = []
        required_vars = [
            "FLUIDIZE_NODE_ID",
            "FLUIDIZE_PROJECT_ID",
            "FLUIDIZE_EXECUTION_MODE",
            "FLUIDIZE_NODE_PATH",
            "FLUIDIZE_SIMULATION_PATH",
            "FLUIDIZE_OUTPUT_PATH",
        ]

        for var in required_vars:
            if var not in env_vars:
                errors.append(f"Missing required environment variable: {var}")
            elif not env_vars[var]:
                errors.append(f"Empty required environment variable: {var}")
        return errors

    @staticmethod
    def _validate_path_vars(env_vars: dict[str, str]) -> list[str]:
        """Validate path environment variables."""
        warnings = []
        path_vars = ["FLUIDIZE_NODE_PATH", "FLUIDIZE_SIMULATION_PATH", "FLUIDIZE_OUTPUT_PATH", "FLUIDIZE_INPUT_PATH"]

        for var in path_vars:
            if var in env_vars:
                path = env_vars[var]
                if not path.startswith("/"):
                    warnings.append(f"{var} should be an absolute path: {path}")
                if " " in path:
                    warnings.append(f"{var} contains spaces which may cause issues: {path}")
        return warnings

    @staticmethod
    def _validate_workflow_vars(env_vars: dict[str, str]) -> list[str]:
        """Validate workflow-related environment variables."""
        warnings = []
        if "FLUIDIZE_WORKFLOW_ID" in env_vars and "FLUIDIZE_STEP_NAME" not in env_vars:
            warnings.append("Workflow ID present but missing step name")
        return warnings

    @staticmethod
    def _validate_dependencies(env_vars: dict[str, str]) -> list[str]:
        """Validate dependency-related environment variables."""
        warnings = []
        if env_vars.get("FLUIDIZE_HAS_DEPENDENCIES") == "true" and "FLUIDIZE_INPUT_PATH" not in env_vars:
            warnings.append("Has dependencies but no input path specified")
        return warnings

    @staticmethod
    def _validate_gpu_requirements(env_vars: dict[str, str]) -> list[str]:
        """Validate GPU requirement environment variables."""
        warnings = []
        if env_vars.get("FLUIDIZE_REQUIRES_GPU") == "true":
            node_pool = env_vars.get("FLUIDIZE_NODE_POOL", "")
            if "gpu" not in node_pool.lower():
                warnings.append("Requires GPU but node pool doesn't indicate GPU support")
        return warnings

    @staticmethod
    def _collect_info(env_vars: dict[str, str]) -> list[str]:
        """Collect informational messages about environment variables."""
        info = []
        info.append(f"Total environment variables: {len(env_vars)}")
        if env_vars.get("FLUIDIZE_EXECUTION_MODE"):
            info.append(f"Execution mode: {env_vars['FLUIDIZE_EXECUTION_MODE']}")
        if env_vars.get("FLUIDIZE_NODE_POOL"):
            info.append(f"Target node pool: {env_vars['FLUIDIZE_NODE_POOL']}")
        return info

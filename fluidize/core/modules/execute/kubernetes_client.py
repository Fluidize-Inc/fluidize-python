"""
Kubernetes Execution Client using kubernetes-client

This client handles Kubernetes Job execution using the official Kubernetes
Python client library. Provides type-safe K8s resource management.
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
except ImportError:
    client = None
    config = None
    ApiException = Exception

from fluidize.core.types.execution_models import PodSpec

logger = logging.getLogger(__name__)


@dataclass
class JobResult:
    """Result of Kubernetes Job execution."""

    job_name: str
    namespace: str
    success: bool
    exit_code: Optional[int] = None
    logs: str = ""
    job_status: str = ""
    pod_name: Optional[str] = None
    start_time: Optional[str] = None
    completion_time: Optional[str] = None
    failure_reason: Optional[str] = None


class KubernetesExecutionClient:
    """
    Kubernetes execution client using kubernetes-client library.

    This client provides type-safe Kubernetes Job submission and monitoring
    without YAML string manipulation.
    """

    def __init__(self, namespace: str = "fluidize"):
        """
        Initialize Kubernetes client.

        Args:
            namespace: Default namespace for operations
        """
        if client is None:
            msg = "Kubernetes client not available. Install with: pip install kubernetes"
            raise ImportError(msg)

        self.namespace = namespace

        try:
            # Try to load in-cluster config first (if running in K8s)
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config")
        except config.ConfigException:
            try:
                # Fall back to local kubeconfig
                config.load_kube_config()
                logger.info("Loaded local Kubernetes config")
            except config.ConfigException:
                logger.exception("Failed to load Kubernetes config")
                raise

        # Initialize API clients
        self.batch_v1 = client.BatchV1Api()
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

        logger.info(f"Kubernetes client initialized for namespace: {namespace}")

    def submit_job(self, pod_spec: PodSpec, job_name: str, **job_options) -> JobResult:
        """
        Submit a Kubernetes Job and wait for completion.

        Args:
            pod_spec: Pod specification
            job_name: Name for the job
            **job_options: Additional job configuration

        Returns:
            JobResult with execution details
        """
        try:
            # Create Job object using kubernetes-client types
            job = self._build_job_object(pod_spec, job_name, **job_options)

            logger.info(f"Submitting Kubernetes Job: {job_name}")

            # Submit job
            self.batch_v1.create_namespaced_job(namespace=self.namespace, body=job)

            logger.info(f"Job {job_name} submitted successfully")

            # Wait for completion
            return self.wait_for_job_completion(job_name)

        except ApiException as e:
            logger.exception("Kubernetes API error")
            return JobResult(
                job_name=job_name, namespace=self.namespace, success=False, failure_reason=f"API Error: {e.reason}"
            )
        except Exception as e:
            logger.exception("Error submitting job")
            return JobResult(job_name=job_name, namespace=self.namespace, success=False, failure_reason=str(e))

    def submit_job_async(self, pod_spec: PodSpec, job_name: str, **job_options) -> str:
        """
        Submit a Kubernetes Job without waiting for completion.

        Args:
            pod_spec: Pod specification
            job_name: Name for the job
            **job_options: Additional job configuration

        Returns:
            Job name for monitoring
        """
        job = self._build_job_object(pod_spec, job_name, **job_options)

        self.batch_v1.create_namespaced_job(namespace=self.namespace, body=job)

        logger.info(f"Job {job_name} submitted asynchronously")
        return job_name

    def wait_for_job_completion(self, job_name: str, timeout: int = 3600, poll_interval: int = 10) -> JobResult:
        """
        Wait for job completion and return results.

        Args:
            job_name: Name of the job to monitor
            timeout: Maximum wait time in seconds
            poll_interval: Polling interval in seconds

        Returns:
            JobResult with execution details
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Get job status
                job = self.batch_v1.read_namespaced_job_status(name=job_name, namespace=self.namespace)

                # Check if job completed
                if job.status.completion_time:
                    logger.info(f"Job {job_name} completed successfully")
                    return self._build_success_result(job_name, job)

                # Check if job failed
                if job.status.failed:
                    logger.error(f"Job {job_name} failed")
                    return self._build_failure_result(job_name, job)

                # Job still running
                logger.debug(f"Job {job_name} still running...")
                time.sleep(poll_interval)

            except ApiException as e:
                logger.exception("Error checking job status")
                return JobResult(
                    job_name=job_name,
                    namespace=self.namespace,
                    success=False,
                    failure_reason=f"Status check failed: {e.reason}",
                )

        # Timeout
        logger.error(f"Job {job_name} timed out after {timeout} seconds")
        return JobResult(
            job_name=job_name,
            namespace=self.namespace,
            success=False,
            failure_reason=f"Timeout after {timeout} seconds",
        )

    def get_job_logs(self, job_name: str) -> str:
        """
        Get logs from job pods.

        Args:
            job_name: Name of the job

        Returns:
            Combined logs from all job pods
        """
        try:
            # Find pods for this job
            pods = self.core_v1.list_namespaced_pod(namespace=self.namespace, label_selector=f"job-name={job_name}")

            all_logs = []
            for pod in pods.items:
                try:
                    logs = self.core_v1.read_namespaced_pod_log(
                        name=pod.metadata.name,
                        namespace=self.namespace,
                        container=None,  # Get logs from all containers
                    )
                    all_logs.append(f"=== Pod: {pod.metadata.name} ===\n{logs}")
                except ApiException as e:
                    all_logs.append(f"=== Pod: {pod.metadata.name} ===\nError getting logs: {e.reason}")

            return "\n\n".join(all_logs)

        except ApiException as e:
            logger.exception("Error getting job logs")
            return f"Error getting logs: {e.reason}"

    def delete_job(self, job_name: str, delete_pods: bool = True) -> bool:
        """
        Delete a Kubernetes job.

        Args:
            job_name: Name of the job to delete
            delete_pods: Whether to delete associated pods

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete job
            self.batch_v1.delete_namespaced_job(
                name=job_name, namespace=self.namespace, propagation_policy="Foreground" if delete_pods else "Orphan"
            )

            logger.info(f"Job {job_name} deleted successfully")
        except ApiException:
            logger.exception("Error deleting job %s", job_name)
            return False
        else:
            return True

    def _build_job_object(self, pod_spec: PodSpec, job_name: str, **job_options) -> client.V1Job:
        """Build Kubernetes Job object using client types."""

        # Convert pod spec to Kubernetes types
        containers = []
        for container_spec in pod_spec.containers:
            container = client.V1Container(
                name=container_spec.name,
                image=container_spec.image,
                command=container_spec.command if container_spec.command else None,
                args=container_spec.args if container_spec.args else None,
                working_dir=container_spec.working_dir,
                env=[client.V1EnvVar(name=k, value=v) for k, v in container_spec.env_vars.items()],
                volume_mounts=[
                    client.V1VolumeMount(
                        name=mount.name, mount_path=mount.mount_path, sub_path=mount.sub_path, read_only=mount.read_only
                    )
                    for mount in container_spec.volume_mounts
                ],
                resources=self._build_resource_requirements(container_spec.resources),
                security_context=self._build_security_context(container_spec.security_context),
            )
            containers.append(container)

        # Build volumes
        volumes = []
        for volume in pod_spec.volumes:
            if volume.volume_type == "hostPath":
                vol = client.V1Volume(
                    name=volume.name, host_path=client.V1HostPathVolumeSource(path=volume.source["path"])
                )
            elif volume.volume_type == "persistentVolumeClaim":
                vol = client.V1Volume(
                    name=volume.name,
                    persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                        claim_name=volume.source["claimName"]
                    ),
                )
            elif volume.volume_type == "emptyDir":
                vol = client.V1Volume(name=volume.name, empty_dir=client.V1EmptyDirVolumeSource())
            else:
                continue  # Skip unsupported volume types

            volumes.append(vol)

        # Build pod template
        pod_template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels=pod_spec.labels, annotations=pod_spec.annotations),
            spec=client.V1PodSpec(
                containers=containers,
                volumes=volumes,
                restart_policy=pod_spec.restart_policy,
                service_account_name=pod_spec.service_account_name,
                node_selector=pod_spec.node_selector if pod_spec.node_selector else None,
                tolerations=self._build_tolerations(pod_spec.tolerations),
                affinity=self._build_affinity(pod_spec.affinity),
                dns_policy=pod_spec.dns_policy,
                hostname=pod_spec.hostname,
                subdomain=pod_spec.subdomain,
            ),
        )

        # Build job
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(
                name=job_name, namespace=self.namespace, labels=pod_spec.labels, annotations=pod_spec.annotations
            ),
            spec=client.V1JobSpec(
                template=pod_template,
                ttl_seconds_after_finished=job_options.get("ttl_seconds_after_finished", 3600),
                backoff_limit=job_options.get("backoff_limit", 3),
                active_deadline_seconds=job_options.get("active_deadline_seconds"),
                completions=job_options.get("completions", 1),
                parallelism=job_options.get("parallelism", 1),
            ),
        )

        return job

    def _build_resource_requirements(self, resources: dict) -> Optional[client.V1ResourceRequirements]:
        """Build Kubernetes resource requirements."""
        if not resources:
            return None

        return client.V1ResourceRequirements(requests=resources.get("requests"), limits=resources.get("limits"))

    def _build_security_context(self, security_context: dict) -> Optional[client.V1SecurityContext]:
        """Build Kubernetes security context."""
        if not security_context:
            return None

        return client.V1SecurityContext(
            run_as_user=security_context.get("runAsUser"),
            run_as_group=security_context.get("runAsGroup"),
            privileged=security_context.get("privileged"),
            read_only_root_filesystem=security_context.get("readOnlyRootFilesystem"),
        )

    def _build_tolerations(self, tolerations: list[dict]) -> list[client.V1Toleration]:
        """Build Kubernetes tolerations."""
        if not tolerations:
            return []

        return [
            client.V1Toleration(
                key=tol.get("key"),
                operator=tol.get("operator", "Equal"),
                value=tol.get("value"),
                effect=tol.get("effect"),
            )
            for tol in tolerations
        ]

    def _build_affinity(self, affinity: Optional[dict]) -> Optional[client.V1Affinity]:
        """Build Kubernetes affinity (simplified)."""
        # This is a complex structure - implement based on specific needs
        return None

    def _build_success_result(self, job_name: str, job) -> JobResult:
        """Build success result from job object."""
        logs = self.get_job_logs(job_name)

        return JobResult(
            job_name=job_name,
            namespace=self.namespace,
            success=True,
            exit_code=0,
            logs=logs,
            job_status="Completed",
            start_time=str(job.status.start_time) if job.status.start_time else None,
            completion_time=str(job.status.completion_time) if job.status.completion_time else None,
        )

    def _build_failure_result(self, job_name: str, job) -> JobResult:
        """Build failure result from job object."""
        logs = self.get_job_logs(job_name)

        return JobResult(
            job_name=job_name,
            namespace=self.namespace,
            success=False,
            logs=logs,
            job_status="Failed",
            start_time=str(job.status.start_time) if job.status.start_time else None,
            failure_reason=f"Job failed with {job.status.failed} failed attempts",
        )

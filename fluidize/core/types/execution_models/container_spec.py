"""
Universal container specification that works across all execution methods.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class VolumeMount:
    """Volume mount specification."""

    name: str
    mount_path: str
    sub_path: Optional[str] = None
    read_only: bool = False


@dataclass
class Volume:
    """Volume specification."""

    name: str
    volume_type: str  # "hostPath", "persistentVolumeClaim", "emptyDir", etc.
    source: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContainerSpec:
    """
    Universal container specification that can be converted to different formats.

    This spec contains all information needed to run a container across
    local Docker, VM Docker, Kubernetes Jobs, or Argo Workflows.
    """

    # Basic container info
    name: str
    image: str
    command: list[str] = field(default_factory=list)
    args: list[str] = field(default_factory=list)

    # Working directory
    working_dir: Optional[str] = None

    # Environment variables
    env_vars: dict[str, str] = field(default_factory=dict)

    # Volume mounts
    volume_mounts: list[VolumeMount] = field(default_factory=list)

    # Resource requirements
    resources: dict[str, Any] = field(default_factory=dict)

    # Security context
    security_context: dict[str, Any] = field(default_factory=dict)

    # Lifecycle hooks
    lifecycle: dict[str, Any] = field(default_factory=dict)

    # Labels and annotations
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)

    def to_kubernetes_container(self) -> dict[str, Any]:
        """Convert to Kubernetes container specification."""
        container: dict[str, Any] = {
            "name": self.name,
            "image": self.image,
            "env": [{"name": k, "value": v} for k, v in self.env_vars.items()],
            "volumeMounts": [
                {
                    "name": mount.name,
                    "mountPath": mount.mount_path,
                    **({"subPath": mount.sub_path} if mount.sub_path else {}),
                    **({"readOnly": mount.read_only} if mount.read_only else {}),
                }
                for mount in self.volume_mounts
            ],
        }

        if self.command:
            container["command"] = self.command
        if self.args:
            container["args"] = self.args
        if self.working_dir:
            container["workingDir"] = self.working_dir
        if self.resources:
            container["resources"] = self.resources
        if self.security_context:
            container["securityContext"] = self.security_context
        if self.lifecycle:
            container["lifecycle"] = self.lifecycle

        return container

    def to_argo_template(self) -> dict[str, Any]:
        """Convert to Argo Workflow template."""
        return {"name": self.name, "container": self.to_kubernetes_container()}


@dataclass
class PodSpec:
    """
    Universal pod specification for Kubernetes-based execution.
    """

    # Containers in the pod
    containers: list[ContainerSpec] = field(default_factory=list)

    # Volumes available to containers
    volumes: list[Volume] = field(default_factory=list)

    # Pod-level settings
    restart_policy: str = "Never"
    service_account_name: Optional[str] = None
    node_selector: dict[str, str] = field(default_factory=dict)
    tolerations: list[dict[str, Any]] = field(default_factory=list)
    affinity: Optional[dict[str, Any]] = None

    # Security context
    security_context: dict[str, Any] = field(default_factory=dict)

    # DNS and networking
    dns_policy: str = "ClusterFirst"
    hostname: Optional[str] = None
    subdomain: Optional[str] = None

    # Labels and annotations
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)

    def to_kubernetes_pod_spec(self) -> dict[str, Any]:
        """Convert to Kubernetes Pod specification."""
        pod_spec: dict[str, Any] = {
            "restartPolicy": self.restart_policy,
            "containers": [container.to_kubernetes_container() for container in self.containers],
            "volumes": [{"name": volume.name, volume.volume_type: volume.source} for volume in self.volumes],
        }

        if self.service_account_name:
            pod_spec["serviceAccountName"] = self.service_account_name
        if self.node_selector:
            pod_spec["nodeSelector"] = self.node_selector
        if self.tolerations:
            pod_spec["tolerations"] = self.tolerations
        if self.affinity:
            pod_spec["affinity"] = self.affinity
        if self.security_context:
            pod_spec["securityContext"] = self.security_context
        if self.dns_policy:
            pod_spec["dnsPolicy"] = self.dns_policy
        if self.hostname:
            pod_spec["hostname"] = self.hostname
        if self.subdomain:
            pod_spec["subdomain"] = self.subdomain

        return pod_spec

    def to_kubernetes_job(self, job_name: str, namespace: str = "default") -> dict[str, Any]:
        """Convert to Kubernetes Job specification."""
        return {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": job_name,
                "namespace": namespace,
                "labels": self.labels,
                "annotations": self.annotations,
            },
            "spec": {
                "ttlSecondsAfterFinished": 3600,
                "backoffLimit": 3,
                "template": {"metadata": {"labels": self.labels}, "spec": self.to_kubernetes_pod_spec()},
            },
        }

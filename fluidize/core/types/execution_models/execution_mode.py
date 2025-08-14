"""
Execution modes for Fluidize nodes.
"""

from enum import Enum


class ExecutionMode(Enum):
    """Supported execution modes for Fluidize nodes."""

    LOCAL_DOCKER = "local_docker"
    VM_DOCKER = "vm_docker"
    KUBERNETES = "kubernetes"
    CLOUD_BATCH = "cloud_batch"
    CLUSTER_SLURM = "cluster_slurm"
    ARGO_WORKFLOW = "argo_workflow"

"""
Resource requirements for container execution.
"""

from dataclasses import dataclass
from enum import Enum


class NodePoolType(Enum):
    """Kubernetes node pool types."""

    SMALL_CPU = "small-cpu-pool"
    MEDIUM_CPU = "medium-cpu-pool"
    LARGE_CPU = "large-cpu-pool"
    GPU = "gpu-pool"
    AUTO = "auto"  # Let system decide


class GPUType(Enum):
    """Supported GPU types."""

    NVIDIA_TESLA_T4 = "nvidia-tesla-t4"
    NVIDIA_TESLA_V100 = "nvidia-tesla-v100"
    NVIDIA_A100 = "nvidia-tesla-a100"


@dataclass
class ResourceRequirements:
    """Resource requirements for container execution."""

    # CPU resources
    cpu_request: str = "100m"  # Minimum CPU
    cpu_limit: str = "2000m"  # Maximum CPU

    # Memory resources
    memory_request: str = "256Mi"  # Minimum memory
    memory_limit: str = "2Gi"  # Maximum memory

    # GPU resources
    gpu_count: int = 0
    gpu_type: GPUType = GPUType.NVIDIA_TESLA_T4

    # Storage resources
    disk_size: str = "10Gi"
    disk_type: str = "pd-standard"  # pd-standard, pd-ssd, pd-balanced

    # Node pool preference
    node_pool_preference: NodePoolType = NodePoolType.AUTO

    def requires_gpu(self) -> bool:
        """Check if GPU resources are required."""
        return self.gpu_count > 0

    def get_node_pool(self) -> str:
        """Get the appropriate node pool name."""
        if self.node_pool_preference == NodePoolType.AUTO:
            if self.requires_gpu():
                return NodePoolType.GPU.value
            elif self._is_high_cpu():
                return NodePoolType.MEDIUM_CPU.value
            else:
                return NodePoolType.SMALL_CPU.value
        return str(self.node_pool_preference.value)

    def _is_high_cpu(self) -> bool:
        """Determine if this is a high CPU workload."""
        # Extract number from CPU limit (e.g., "2000m" -> 2000)
        cpu_limit_num = int(self.cpu_limit.replace("m", ""))
        return cpu_limit_num > 1000  # More than 1 CPU

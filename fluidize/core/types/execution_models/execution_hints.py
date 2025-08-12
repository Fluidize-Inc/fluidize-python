"""
Execution hints and configurations for container execution.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RetryPolicy:
    """Retry policy for failed executions."""

    max_retries: int = 3
    backoff_limit: int = 6
    restart_policy: str = "OnFailure"  # Never, OnFailure, Always


@dataclass
class ExecutionHints:
    """Execution-specific hints and configurations."""

    # Platform specifications
    platform: Optional[str] = None  # linux/amd64, linux/arm64
    architecture: Optional[str] = None

    # Security settings
    privileged: bool = False
    run_as_user: Optional[int] = None
    run_as_group: Optional[int] = None

    # Networking
    network_mode: str = "default"
    dns_policy: str = "ClusterFirst"

    # Container settings
    tty: bool = False
    stdin: bool = False

    # Timeouts
    active_deadline_seconds: Optional[int] = None  # Max execution time
    termination_grace_period: int = 30

    # Node scheduling
    node_selector: dict[str, str] = field(default_factory=dict)
    tolerations: list[dict[str, Any]] = field(default_factory=list)
    affinity: Optional[dict[str, Any]] = None

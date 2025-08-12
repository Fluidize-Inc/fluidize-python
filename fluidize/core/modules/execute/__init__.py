"""
Execution Module

This module provides execution clients for different environments:
- Docker SDK for local execution
- VM/SSH clients for remote execution
- Shared utilities for all execution methods

All clients use proper libraries instead of unsafe command string construction:
- DockerExecutionClient: Uses docker-py SDK
- KubernetesExecutionClient: Uses kubernetes-client library
- VMExecutionClient: Uses shlex.quote() for safe SSH command execution
"""

from .docker_client import ContainerResult, DockerExecutionClient

# from .kubernetes_client import JobResult, KubernetesExecutionClient
from .vm_client import VMExecutionClient, VMExecutionResult

__all__ = [
    "ContainerResult",
    "DockerExecutionClient",
    "JobResult",
    # "KubernetesExecutionClient",
    "VMExecutionClient",
    "VMExecutionResult",
]

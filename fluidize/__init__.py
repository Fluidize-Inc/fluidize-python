"""Fluidize Python library for scientific computing pipeline automation."""

import fluidize.core.utils.dataloader.loader.loader_local
import fluidize.core.utils.dataloader.loader.writer_local

# Auto-register local handlers when fluidize is imported
# This ensures handlers are available without manual imports
import fluidize.core.utils.pathfinder.methods.local  # noqa: F401

from .config import config

__version__ = "0.0.2"
__all__ = ["config"]

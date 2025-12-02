"""
CV-CUE API Wrapper

A Python wrapper for interacting with the CV-CUE API.
"""

from .cv_cue_client import CVCueClient
from .config import logger

# Import resources to trigger registration
from . import resources

__version__ = "0.1.0"
__all__ = ["CVCueClient", "logger"]

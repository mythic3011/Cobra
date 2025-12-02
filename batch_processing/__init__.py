"""
Batch processing module for Cobra comic line art colorization system.

This module provides batch processing capabilities for colorizing multiple
comic pages or panels simultaneously while maintaining high-quality results.
"""

from .exceptions import (
    BatchProcessingError,
    ImageProcessingError,
    ConfigurationError,
    ResourceError,
    QueueError,
    ValidationError,
)
from .logging_config import setup_logging, get_logger
from .config import BatchConfig, ConfigurationHandler
from .processor import BatchProcessor

__version__ = "0.1.0"

__all__ = [
    "BatchProcessingError",
    "ImageProcessingError",
    "ConfigurationError",
    "ResourceError",
    "QueueError",
    "ValidationError",
    "setup_logging",
    "get_logger",
    "BatchConfig",
    "ConfigurationHandler",
    "BatchProcessor",
]

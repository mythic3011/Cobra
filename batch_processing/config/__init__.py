"""
Configuration management for batch processing.

This submodule handles configuration loading, validation, and merging
for batch processing operations.
"""

from .config_handler import BatchConfig, ConfigurationHandler

__all__ = ["BatchConfig", "ConfigurationHandler"]

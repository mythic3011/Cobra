"""
Logging configuration for batch processing operations.

This module provides centralized logging configuration for the batch processing
system, including structured logging with timestamps, component names, and
different log levels for various operations.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


# Default log format with timestamp, level, component, and message
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log levels mapping
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: Optional[str] = None,
    console_output: bool = True,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
) -> logging.Logger:
    """
    Set up logging configuration for batch processing operations.
    
    This function configures the root logger with appropriate handlers for
    console and/or file output. It creates log directories if needed and
    sets up structured logging with timestamps and component names.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional specific log file path. If not provided and log_dir
                 is specified, a timestamped log file will be created
        log_dir: Directory for log files. If specified, logs will be written
                to files in this directory
        console_output: Whether to output logs to console (stdout)
        log_format: Custom log format string. If None, uses DEFAULT_LOG_FORMAT
        date_format: Custom date format string. If None, uses DEFAULT_DATE_FORMAT
    
    Returns:
        Configured root logger instance
    
    Raises:
        ValueError: If log_level is not a valid log level
        OSError: If log directory cannot be created
    
    Example:
        >>> logger = setup_logging(log_level="DEBUG", log_dir="./logs")
        >>> logger.info("Batch processing started")
    """
    # Validate log level
    if log_level.upper() not in LOG_LEVELS:
        raise ValueError(
            f"Invalid log level: {log_level}. "
            f"Must be one of: {', '.join(LOG_LEVELS.keys())}"
        )
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVELS[log_level.upper()])
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Set up formatter
    formatter = logging.Formatter(
        fmt=log_format or DEFAULT_LOG_FORMAT,
        datefmt=date_format or DEFAULT_DATE_FORMAT,
    )
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOG_LEVELS[log_level.upper()])
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if log directory or file is specified
    if log_dir or log_file:
        if log_file:
            # Use specified log file
            log_path = Path(log_file)
        else:
            # Create timestamped log file in log directory
            log_dir_path = Path(log_dir)
            log_dir_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"batch_processing_{timestamp}.log"
            log_path = log_dir_path / log_filename
        
        # Ensure parent directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file handler
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setLevel(LOG_LEVELS[log_level.upper()])
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        root_logger.info(f"Logging to file: {log_path}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific component.
    
    This function returns a logger with the specified name, which will
    inherit the configuration from the root logger set up by setup_logging().
    
    Args:
        name: Name of the logger, typically the module name (__name__)
    
    Returns:
        Logger instance for the specified component
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing image batch")
    """
    return logging.getLogger(name)


def configure_component_logger(
    component_name: str,
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure a logger for a specific component with custom settings.
    
    This function allows individual components to have different log levels
    or output files while still inheriting the base configuration.
    
    Args:
        component_name: Name of the component (e.g., "batch_processor", "queue")
        log_level: Optional custom log level for this component
        log_file: Optional separate log file for this component
    
    Returns:
        Configured logger for the component
    
    Example:
        >>> queue_logger = configure_component_logger(
        ...     "queue", log_level="DEBUG", log_file="queue.log"
        ... )
    """
    logger = logging.getLogger(component_name)
    
    if log_level:
        if log_level.upper() not in LOG_LEVELS:
            raise ValueError(
                f"Invalid log level: {log_level}. "
                f"Must be one of: {', '.join(LOG_LEVELS.keys())}"
            )
        logger.setLevel(LOG_LEVELS[log_level.upper()])
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        formatter = logging.Formatter(
            fmt=DEFAULT_LOG_FORMAT,
            datefmt=DEFAULT_DATE_FORMAT,
        )
        
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

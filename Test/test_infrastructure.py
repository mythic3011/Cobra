"""
Test script to verify batch processing infrastructure setup.

This script tests:
1. Directory structure creation
2. Exception classes
3. Logging configuration
"""

import tempfile
import os
from pathlib import Path

from batch_processing import (
    BatchProcessingError,
    ImageProcessingError,
    ConfigurationError,
    ResourceError,
    QueueError,
    ValidationError,
    setup_logging,
    get_logger,
)


def test_directory_structure():
    """Test that all required directories exist."""
    print("Testing directory structure...")
    
    base_path = Path("batch_processing")
    required_dirs = [
        base_path,
        base_path / "core",
        base_path / "config",
        base_path / "io",
        base_path / "memory",
        base_path / "classification",
        base_path / "ui",
    ]
    
    for dir_path in required_dirs:
        assert dir_path.exists(), f"Directory {dir_path} does not exist"
        assert (dir_path / "__init__.py").exists(), f"Missing __init__.py in {dir_path}"
    
    print("✓ Directory structure is correct")


def test_exception_hierarchy():
    """Test exception classes and hierarchy."""
    print("\nTesting exception hierarchy...")
    
    # Test ImageProcessingError
    try:
        raise ImageProcessingError("/path/to/image.png", "Test error message")
    except ImageProcessingError as e:
        assert e.image_path == "/path/to/image.png"
        assert e.message == "Test error message"
        assert "Error processing /path/to/image.png" in str(e)
    
    # Test exception inheritance
    try:
        raise ConfigurationError("Config error")
    except BatchProcessingError:
        pass  # Should catch as base class
    
    # Test all exception types can be instantiated
    exceptions = [
        ConfigurationError("test"),
        ResourceError("test"),
        QueueError("test"),
        ValidationError("test"),
    ]
    
    for exc in exceptions:
        assert isinstance(exc, BatchProcessingError)
    
    print("✓ Exception hierarchy is correct")


def test_logging_configuration():
    """Test logging setup and configuration."""
    print("\nTesting logging configuration...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test basic logging setup
        logger = setup_logging(
            log_level="INFO",
            log_dir=tmpdir,
            console_output=False
        )
        
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
        # Verify log file was created
        log_files = list(Path(tmpdir).glob("batch_processing_*.log"))
        assert len(log_files) == 1, "Log file was not created"
        
        # Verify log file contains messages
        log_content = log_files[0].read_text()
        assert "Test info message" in log_content
        assert "Test warning message" in log_content
        assert "Test error message" in log_content
        
        # Test component logger
        component_logger = get_logger("test_component")
        component_logger.info("Component message")
        
        # Verify component message in log
        log_content = log_files[0].read_text()
        assert "test_component" in log_content
        assert "Component message" in log_content
    
    print("✓ Logging configuration is correct")


def test_logging_levels():
    """Test different logging levels."""
    print("\nTesting logging levels...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test DEBUG level
        logger = setup_logging(
            log_level="DEBUG",
            log_dir=tmpdir,
            console_output=False
        )
        
        logger.debug("Debug message")
        logger.info("Info message")
        
        log_files = list(Path(tmpdir).glob("batch_processing_*.log"))
        log_content = log_files[0].read_text()
        
        assert "Debug message" in log_content
        assert "Info message" in log_content
    
    print("✓ Logging levels work correctly")


def test_module_imports():
    """Test that all modules can be imported."""
    print("\nTesting module imports...")
    
    # Test main module imports
    from batch_processing import exceptions, logging_config
    
    # Test submodule imports
    import batch_processing.core
    import batch_processing.config
    import batch_processing.io
    import batch_processing.memory
    import batch_processing.classification
    import batch_processing.ui
    
    print("✓ All modules can be imported")


def main():
    """Run all infrastructure tests."""
    print("=" * 60)
    print("Batch Processing Infrastructure Tests")
    print("=" * 60)
    
    test_directory_structure()
    test_exception_hierarchy()
    test_logging_configuration()
    test_logging_levels()
    test_module_imports()
    
    print("\n" + "=" * 60)
    print("✓ All infrastructure tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

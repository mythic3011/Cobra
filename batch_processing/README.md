# Batch Processing Module

This module provides batch processing capabilities for the Cobra comic line art colorization system.

## Directory Structure

```
batch_processing/
├── __init__.py              # Module initialization and exports
├── exceptions.py            # Exception classes for error handling
├── logging_config.py        # Logging configuration and utilities
├── README.md               # This file
├── core/                   # Core batch processing components
│   └── __init__.py
├── config/                 # Configuration management
│   └── __init__.py
├── io/                     # File I/O operations
│   └── __init__.py
├── memory/                 # Memory management
│   └── __init__.py
├── classification/         # Image classification
│   └── __init__.py
└── ui/                     # User interface components
    └── __init__.py
```

## Components

### Core (`batch_processing/core/`)
Contains the main batch processing engine:
- `BatchProcessor`: Main coordinator for batch operations
- `ImageQueue`: Queue management for images
- `StatusTracker`: Processing status tracking

### Configuration (`batch_processing/config/`)
Handles configuration management:
- `ConfigurationHandler`: Config loading and validation
- `BatchConfig`: Configuration data classes

### I/O (`batch_processing/io/`)
File and directory operations:
- Directory scanning and validation
- ZIP file extraction and creation (with nested ZIP support)
- Output path management
- Image file validation
- Automatic separation of line art from colored references
- Metadata inclusion in output ZIPs

**Key Features:**
- Extract images from ZIP files (supports nested ZIPs up to 1 level deep)
- Automatically classify and separate line art from colored reference images
- Create output ZIPs with optional metadata and structure preservation
- Automatic cleanup of temporary extraction directories

See [io/README.md](io/README.md) for detailed documentation and examples.

### Memory (`batch_processing/memory/`)
Resource management:
- `MemoryManager`: GPU/CPU memory management
- Cache clearing and garbage collection
- Memory usage monitoring

### Classification (`batch_processing/classification/`)
Image classification:
- `ImageClassifier`: Automatic line art vs colored image detection
- Color analysis and edge detection
- Classification confidence scoring

### UI (`batch_processing/ui/`)
User interfaces:
- Gradio web interface components
- CLI interface for headless operation

## Exception Hierarchy

```
BatchProcessingError (base)
├── ImageProcessingError
├── ConfigurationError
├── ResourceError
├── QueueError
├── ValidationError
├── ZIPExtractionError
└── ClassificationError
```

## Logging

The module uses structured logging with:
- Timestamps for all log entries
- Component-specific loggers
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Console and file output options
- Automatic log file rotation with timestamps

### Usage Example

```python
from batch_processing import setup_logging, get_logger

# Set up logging
setup_logging(log_level="INFO", log_dir="./logs", console_output=True)

# Get a logger for your component
logger = get_logger(__name__)

# Use the logger
logger.info("Starting batch processing")
logger.error("An error occurred", exc_info=True)
```

## Error Handling

All batch processing operations use the exception hierarchy defined in `exceptions.py`:

```python
from batch_processing import ImageProcessingError, ValidationError

try:
    # Process image
    process_image(path)
except ImageProcessingError as e:
    logger.error(f"Failed to process {e.image_path}: {e.message}")
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
```

## Development Guidelines

1. **Logging**: Use the provided logging utilities for all operations
2. **Exceptions**: Raise appropriate exception types for different error scenarios
3. **Documentation**: Document all public functions and classes
4. **Type Hints**: Use type hints for all function signatures
5. **Testing**: Write tests for all new functionality

## Requirements

See the main project `requirements.txt` for dependencies.

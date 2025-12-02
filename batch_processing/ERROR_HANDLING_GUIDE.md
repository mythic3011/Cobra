# Error Handling Guide for Batch Processing

## Quick Reference

This guide provides quick reference for error handling in the batch processing system.

## Error Types

### BatchProcessingError (Base)
Base exception for all batch processing errors.

```python
from batch_processing.exceptions import BatchProcessingError

try:
    # batch processing code
    pass
except BatchProcessingError as e:
    # Catches any batch processing error
    print(f"Batch processing error: {e}")
```

### ImageProcessingError
Raised when processing a specific image fails.

```python
from batch_processing.exceptions import ImageProcessingError

try:
    processor.process_single_image(queue_item)
except ImageProcessingError as e:
    print(f"Failed to process {e.image_path}: {e.message}")
```

### ConfigurationError
Raised when configuration is invalid.

```python
from batch_processing.exceptions import ConfigurationError

try:
    handler.load_config_file("config.json")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    # Use defaults or prompt user
```

### ValidationError
Raised when input validation fails.

```python
from batch_processing.exceptions import ValidationError

try:
    processor.add_images([])
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Common Error Scenarios

### Scenario 1: Invalid Image Files

**Problem**: Some images in the batch are corrupted or don't exist.

**Behavior**: Invalid images are skipped, valid images are processed.

```python
processor = BatchProcessor(config)

# Mix of valid and invalid images
processor.add_images([
    "valid1.png",
    "/nonexistent/invalid.png",  # Skipped with warning
    "valid2.png"
])

# Processing continues with valid images only
processor.start_processing()
```

**Logs**:
```
[WARNING] Skipping invalid image: /nonexistent/invalid.png
[INFO] Successfully added 2 images to queue. Skipped 1 invalid images.
```

### Scenario 2: Invalid Configuration Values

**Problem**: Configuration file has invalid values.

**Behavior**: Invalid values are replaced with defaults, processing continues.

```python
# config.json contains:
# {
#   "default": {
#     "style": "invalid_style",
#     "seed": -5
#   }
# }

handler = ConfigurationHandler()
handler.load_config_file("config.json")

# Invalid values replaced with defaults
config = handler.get_default_config()
# config['style'] == 'line + shadow'  (default)
# config['seed'] == 0  (default)
```

**Logs**:
```
[WARNING] Invalid value for 'style' in default: 'invalid_style'. Using default: line + shadow
[WARNING] Invalid value for 'seed' in default: -5. Using default: 0
```

### Scenario 3: Out of Memory During Processing

**Problem**: GPU runs out of memory while processing an image.

**Behavior**: Memory is cleared, error is logged, processing continues with next image.

```python
processor.start_processing()

# If OOM occurs on image 3:
# - Image 3 marked as failed
# - Memory is cleared
# - Processing continues with image 4
```

**Logs**:
```
[ERROR] Out of memory during colorization. Try reducing image size or closing other applications.
[INFO] Clearing memory after image processing
[INFO] Processing image 4/10: next_image.png
```

### Scenario 4: JSON Parsing Error

**Problem**: Configuration file has invalid JSON syntax.

**Behavior**: ConfigurationError is raised with detailed error message.

```python
try:
    handler.load_config_file("bad_config.json")
except ConfigurationError as e:
    print(f"Cannot load config: {e}")
    # Use default configuration
    config = BatchConfig(
        input_dir="./input",
        output_dir="./output",
        reference_images=["ref.png"]
    )
```

**Error Message**:
```
Failed to parse JSON configuration file bad_config.json: Expecting property name enclosed in double quotes: line 5 column 12
Line 5, Column 12: Expecting property name enclosed in double quotes
```

### Scenario 5: Permission Denied

**Problem**: Cannot read input file or write output file.

**Behavior**: Error is logged with context, processing continues with next image.

```python
processor.start_processing()

# If permission denied on image 2:
# - Image 2 marked as failed with error message
# - Processing continues with image 3
```

**Logs**:
```
[ERROR] Processing failed at stage 'loading input image': Permission denied reading file: /path/to/image.png
[INFO] Image processing failed: Permission denied (Continuing with remaining images)
```

## Best Practices

### 1. Always Use Try-Catch for Batch Operations

```python
from batch_processing.exceptions import BatchProcessingError

try:
    processor = BatchProcessor(config)
    processor.add_images(image_paths)
    processor.start_processing()
except BatchProcessingError as e:
    logger.error(f"Batch processing failed: {e}")
    # Handle error appropriately
```

### 2. Check Status After Processing

```python
processor.start_processing()

status = processor.get_status()
if status['failed'] > 0:
    # Some images failed
    all_statuses = processor.status_tracker.get_all_statuses()
    for image_id, img_status in all_statuses.items():
        if img_status.state == "failed":
            print(f"Failed: {img_status.error_message}")
```

### 3. Validate Configuration Before Use

```python
handler = ConfigurationHandler()

try:
    handler.load_config_file("config.json")
    config_dict = handler.get_default_config()
    
    # Validate before creating BatchConfig
    handler.validate_config(config_dict)
    
except ConfigurationError as e:
    print(f"Invalid configuration: {e}")
    # Use defaults or prompt user
```

### 4. Handle Empty Results

```python
try:
    processor.add_images(image_paths)
except ValidationError as e:
    if "empty" in str(e).lower():
        print("No images to process")
    elif "no valid images" in str(e).lower():
        print("All images were invalid")
```

### 5. Log Errors for Debugging

```python
import logging

logger = logging.getLogger(__name__)

try:
    processor.start_processing()
except ImageProcessingError as e:
    logger.error(
        f"Image processing failed",
        extra={
            'image_path': e.image_path,
            'error': str(e)
        },
        exc_info=True  # Include traceback
    )
```

## Error Recovery Strategies

### Strategy 1: Retry Failed Images

```python
# Get failed images
all_statuses = processor.status_tracker.get_all_statuses()
failed_images = [
    status.input_path 
    for status in all_statuses.values() 
    if status.state == "failed"
]

# Create new processor and retry
if failed_images:
    retry_processor = BatchProcessor(config)
    retry_processor.add_images(failed_images)
    retry_processor.start_processing()
```

### Strategy 2: Use Defaults on Config Error

```python
def load_config_with_fallback(config_path, default_config):
    handler = ConfigurationHandler()
    
    try:
        handler.load_config_file(config_path)
        return handler.get_default_config()
    except ConfigurationError as e:
        logger.warning(f"Config error, using defaults: {e}")
        return default_config
```

### Strategy 3: Graceful Degradation

```python
def process_with_fallback(processor, image_paths):
    try:
        processor.add_images(image_paths)
    except ValidationError:
        # Try with just the first valid image
        for path in image_paths:
            try:
                processor.add_images([path])
                break
            except ValidationError:
                continue
    
    if processor.queue.size() > 0:
        processor.start_processing()
    else:
        logger.error("No valid images to process")
```

## Debugging Tips

### 1. Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
)
```

### 2. Check Error Chaining

```python
try:
    processor.process_single_image(queue_item)
except ImageProcessingError as e:
    print(f"Error: {e}")
    if e.__cause__:
        print(f"Caused by: {e.__cause__}")
```

### 3. Inspect Status Tracker

```python
# Get detailed status for all images
all_statuses = processor.status_tracker.get_all_statuses()

for image_id, status in all_statuses.items():
    print(f"Image: {image_id}")
    print(f"  State: {status.state}")
    print(f"  Error: {status.error_message}")
    print(f"  Time: {status.processing_time}s")
```

### 4. Monitor Memory Usage

```python
# Check memory before processing
memory_usage = processor.memory_manager.check_memory_usage()
print(f"Memory usage: {memory_usage:.1%}")

# Process with monitoring
processor.start_processing()

# Check memory after
memory_usage = processor.memory_manager.check_memory_usage()
print(f"Memory usage after: {memory_usage:.1%}")
```

## Testing Error Handling

### Unit Test Example

```python
def test_invalid_config_uses_defaults():
    """Test that invalid config values use defaults."""
    handler = ConfigurationHandler()
    
    # Create config with invalid values
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
        json.dump({
            'default': {
                'style': 'invalid',
                'seed': -5
            }
        }, f)
        f.flush()
        
        # Load config
        handler.load_config_file(f.name)
        config = handler.get_default_config()
        
        # Check defaults were used
        assert config['style'] == 'line + shadow'
        assert config['seed'] == 0
```

### Integration Test Example

```python
def test_batch_continues_on_failure():
    """Test that batch continues when individual images fail."""
    processor = BatchProcessor(config)
    
    # Add mix of valid and invalid
    processor.add_images([
        'valid1.png',
        '/nonexistent/invalid.png',
        'valid2.png'
    ])
    
    # Process
    processor.start_processing()
    
    # Check that valid images were processed
    status = processor.get_status()
    assert status['completed'] >= 1
    assert status['failed'] >= 1
```

## Summary

The error handling system provides:

- ✅ **Resilience**: Processing continues despite individual failures
- ✅ **Context**: Errors include detailed information for debugging
- ✅ **Defaults**: Invalid configuration uses sensible defaults
- ✅ **Logging**: All errors are logged with appropriate levels
- ✅ **Recovery**: Failed operations can be retried or handled gracefully

For more details, see `Test/ERROR_HANDLING_IMPLEMENTATION_SUMMARY.md`.

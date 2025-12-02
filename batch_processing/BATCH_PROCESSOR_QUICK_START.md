# BatchProcessor Quick Start Guide

## Overview

The `BatchProcessor` class provides batch processing capabilities for colorizing multiple comic line art images using the Cobra colorization system.

## Basic Usage

### 1. Import Required Classes

```python
from batch_processing import BatchProcessor, BatchConfig
```

### 2. Create Configuration

```python
config = BatchConfig(
    input_dir="./input_images",           # Directory with images to process
    output_dir="./output_images",         # Where to save results
    reference_images=[                     # Reference images for colorization
        "ref1.png",
        "ref2.png",
        "ref3.png"
    ],
    style="line + shadow",                 # "line" or "line + shadow"
    seed=42,                               # Random seed for reproducibility
    num_inference_steps=10,                # Number of diffusion steps
    top_k=3,                               # Number of top references to use
    recursive=False,                       # Scan subdirectories?
    overwrite=False,                       # Overwrite existing outputs?
    preview_mode=False                     # Process only first image?
)
```

### 3. Initialize Processor

```python
processor = BatchProcessor(config)
```

The processor will automatically:
- Initialize the processing queue
- Set up status tracking
- Configure memory management
- Detect available device (CUDA/MPS/CPU)

### 4. Add Images to Queue

```python
# Add images from a list
image_paths = ["page1.png", "page2.png", "page3.png"]
processor.add_images(image_paths)

# Or scan a directory
from batch_processing.io import scan_directory
images = scan_directory(config.input_dir, recursive=config.recursive)
processor.add_images(images)
```

### 5. Start Processing

```python
# Process all images
processor.start_processing()
```

### 6. Check Status

```python
# Get current status
status = processor.get_status()

print(f"Total images: {status['total_images']}")
print(f"Completed: {status['completed']}")
print(f"Failed: {status['failed']}")
print(f"Pending: {status['pending']}")
print(f"Success rate: {status['success_rate']:.1f}%")

if status['elapsed_time']:
    print(f"Processing time: {status['elapsed_time']:.2f} seconds")
```

## Advanced Features

### Pause and Resume

```python
# Start processing
processor.start_processing()

# In another thread or after some condition:
processor.pause_processing()  # Pauses after current image

# Check status while paused
status = processor.get_status()
print(f"Paused at: {status['completed']}/{status['total_images']}")

# Resume processing
processor.resume_processing()
```

### Cancel Processing

```python
# Start processing
processor.start_processing()

# Cancel remaining images
processor.cancel_processing()

# Remaining images will be marked as CANCELLED
status = processor.get_status()
print(f"Cancelled: {status['cancelled']} images")
```

### Monitor Progress

```python
import time

processor.start_processing()

# Monitor in a separate thread
while processor._processing:
    status = processor.get_status()
    print(f"Progress: {status['completed']}/{status['total_images']}")
    time.sleep(1)

print("Processing complete!")
```

## Configuration Options

### BatchConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_dir` | str | Required | Directory containing input images |
| `output_dir` | str | Required | Directory for output images |
| `reference_images` | List[str] | Required | Paths to reference images |
| `style` | str | "line + shadow" | Colorization style |
| `seed` | int | 0 | Random seed |
| `num_inference_steps` | int | 10 | Diffusion steps |
| `top_k` | int | 3 | Number of top references |
| `recursive` | bool | False | Scan subdirectories |
| `overwrite` | bool | False | Overwrite existing files |
| `preview_mode` | bool | False | Process only first image |
| `max_concurrent` | int | 1 | Max concurrent images |
| `input_is_zip` | bool | False | Input is ZIP file |
| `output_as_zip` | bool | False | Package output as ZIP |
| `zip_output_name` | str | None | Name for output ZIP |

## Status Information

The `get_status()` method returns a dictionary with:

```python
{
    'summary': StatusSummary,      # Detailed summary object
    'is_processing': bool,         # Currently processing?
    'is_paused': bool,             # Currently paused?
    'is_cancelled': bool,          # Was cancelled?
    'queue_size': int,             # Images remaining in queue
    'total_images': int,           # Total images in batch
    'completed': int,              # Successfully completed
    'failed': int,                 # Failed to process
    'pending': int,                # Not yet started
    'processing': int,             # Currently being processed
    'cancelled': int,              # Cancelled images
    'success_rate': float,         # Percentage successful
    'elapsed_time': float          # Total time in seconds
}
```

## Error Handling

The processor handles errors gracefully:

```python
try:
    processor.start_processing()
except BatchProcessingError as e:
    print(f"Batch processing error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")

# Check which images failed
status = processor.get_status()
if status['failed'] > 0:
    # Get detailed status for each image
    all_statuses = processor.status_tracker.get_all_statuses()
    for image_id, img_status in all_statuses.items():
        if img_status.state == "failed":
            print(f"Failed: {img_status.id}")
            print(f"Error: {img_status.error_message}")
```

## Memory Management

The processor automatically manages memory:

- Clears GPU/CPU cache after each image
- Triggers garbage collection when needed
- Monitors memory usage throughout processing

You can access the memory manager directly:

```python
# Check current memory usage
usage = processor.memory_manager.check_memory_usage()
print(f"Memory usage: {usage:.1%}")

# Manually clear cache
processor.memory_manager.clear_cache()

# Manually trigger GC if needed
processor.memory_manager.trigger_gc_if_needed()
```

## Complete Example

```python
from batch_processing import BatchProcessor, BatchConfig, setup_logging
from batch_processing.io import scan_directory

# Setup logging
setup_logging(log_level="INFO", log_dir="./logs")

# Create configuration
config = BatchConfig(
    input_dir="./comic_pages",
    output_dir="./colorized_pages",
    reference_images=[
        "./references/character_ref.png",
        "./references/background_ref.png"
    ],
    style="line + shadow",
    seed=42,
    num_inference_steps=10,
    top_k=3,
    recursive=True,
    overwrite=False
)

# Initialize processor
processor = BatchProcessor(config)

# Scan directory and add images
images = scan_directory(config.input_dir, recursive=True)
print(f"Found {len(images)} images to process")

processor.add_images(images)

# Start processing
print("Starting batch processing...")
processor.start_processing()

# Get final status
status = processor.get_status()
print(f"\nProcessing complete!")
print(f"Total: {status['total_images']}")
print(f"Completed: {status['completed']}")
print(f"Failed: {status['failed']}")
print(f"Success rate: {status['success_rate']:.1f}%")
print(f"Time: {status['elapsed_time']:.2f} seconds")
```

## Tips and Best Practices

1. **Start Small**: Test with a few images first before processing large batches
2. **Monitor Memory**: Watch memory usage for large batches
3. **Use Logging**: Enable logging to track progress and debug issues
4. **Handle Failures**: Check status after processing to identify failed images
5. **Save Progress**: The status tracker maintains state throughout processing
6. **Reference Quality**: Use high-quality reference images for best results
7. **Consistent Style**: Use the same style for all images in a batch for consistency

## Troubleshooting

### Out of Memory Errors
- Reduce `num_inference_steps`
- Process fewer images at once
- Use smaller reference images
- Enable memory monitoring

### Slow Processing
- Reduce `num_inference_steps`
- Reduce `top_k` value
- Use fewer reference images
- Check device (GPU vs CPU)

### Failed Images
- Check input image format
- Verify reference images are valid
- Check output directory permissions
- Review error messages in status

## Next Steps

- See `demo_batch_processor.py` for working examples
- Read `BATCH_PROCESSOR_IMPLEMENTATION_SUMMARY.md` for technical details
- Check `test_batch_processor.py` for usage patterns
- Explore other batch processing modules in `batch_processing/`

# Memory Management Module

This module provides memory management functionality for batch processing operations in the Cobra colorization system.

## Overview

The `MemoryManager` class handles GPU memory management, including:
- Cache clearing for CUDA and MPS devices
- Memory usage monitoring
- Automatic garbage collection triggering
- Memory requirement estimation for images

## Usage

### Basic Usage

```python
import torch
from batch_processing.memory import MemoryManager

# Initialize with device
device = torch.device("mps")  # or "cuda" or "cpu"
manager = MemoryManager(device, memory_threshold=0.8)

# Clear GPU cache after processing an image
manager.clear_cache()

# Check current memory usage
usage = manager.check_memory_usage()
print(f"Memory usage: {usage:.2%}")

# Trigger garbage collection if needed
manager.trigger_gc_if_needed()

# Estimate memory for an image
estimate = manager.estimate_memory_required((1024, 1024))
print(f"Estimated memory: {estimate / 1024**2:.1f} MB")
```

### Integration with Batch Processing

```python
# Initialize at start of batch
manager = MemoryManager(device, memory_threshold=0.8)

# Process images
for image_path in image_paths:
    # Estimate memory needed
    estimate = manager.estimate_memory_required(image.size)
    
    # Process image
    result = process_image(image_path)
    
    # Clean up after each image
    manager.clear_cache()
    
    # Periodically check and trigger GC
    manager.trigger_gc_if_needed()
```

## API Reference

### MemoryManager

#### `__init__(device: torch.device, memory_threshold: float = 0.8)`

Initialize the MemoryManager.

**Parameters:**
- `device`: The torch device to manage (cuda, mps, or cpu)
- `memory_threshold`: Memory usage threshold (0-1) for triggering GC. Default is 0.8 (80%)

**Raises:**
- `ValueError`: If memory_threshold is not between 0 and 1

#### `clear_cache() -> None`

Clear GPU memory caches.

For CUDA devices, calls `torch.cuda.empty_cache()`.
For MPS devices, calls `torch.mps.empty_cache()`.
For CPU, this is a no-op.

#### `check_memory_usage() -> float`

Check current memory usage as a percentage.

**Returns:**
- Memory usage as a float between 0 and 1 (0% to 100%)
- Returns 0.0 for CPU devices or if memory info is unavailable

#### `trigger_gc_if_needed() -> None`

Trigger garbage collection if memory usage exceeds threshold.

Checks current memory usage and triggers Python's garbage collector
if usage exceeds the configured threshold. Also clears GPU cache after GC.

#### `estimate_memory_required(image_size: Tuple[int, int]) -> int`

Estimate memory required for processing an image.

**Parameters:**
- `image_size`: Tuple of (width, height) in pixels

**Returns:**
- Estimated memory requirement in bytes

## Memory Estimation

The memory estimation considers:
- Input image (RGB float32)
- Latent representation (compressed)
- Model activations
- Reference images (assumes 4 references)
- Overhead for intermediate tensors (1.5x multiplier)

Example estimates:
- 512x512: ~23 MB
- 1024x1024: ~91 MB
- 2048x2048: ~365 MB

## Device Support

### CUDA
- Full memory monitoring with `torch.cuda.memory_allocated()` and `torch.cuda.memory_reserved()`
- Cache clearing with `torch.cuda.empty_cache()`

### MPS (Apple Silicon)
- Basic memory monitoring with `torch.mps.current_allocated_memory()`
- Cache clearing with `torch.mps.empty_cache()`
- Conservative usage estimation (MPS doesn't expose total memory)

### CPU
- No memory monitoring (returns 0.0)
- No cache clearing (no-op)
- Memory estimation still works for planning purposes

## Best Practices

1. **Initialize once per batch**: Create a single MemoryManager instance for the entire batch operation

2. **Clear cache after each image**: Call `clear_cache()` after processing each image to free GPU memory

3. **Periodic GC checks**: Call `trigger_gc_if_needed()` every few images or when memory usage is high

4. **Plan batch sizes**: Use `estimate_memory_required()` to determine how many images can fit in memory

5. **Set appropriate threshold**: Default 0.8 (80%) works well, but adjust based on your system:
   - Lower threshold (0.6-0.7): More aggressive cleanup, safer for limited memory
   - Higher threshold (0.85-0.9): Less frequent GC, better performance if memory is ample

## Example: Batch Processing with Memory Management

```python
import torch
from batch_processing.memory import MemoryManager

def process_batch(image_paths, device):
    """Process a batch of images with memory management."""
    manager = MemoryManager(device, memory_threshold=0.8)
    
    results = []
    for i, image_path in enumerate(image_paths):
        # Load and process image
        image = load_image(image_path)
        
        # Estimate memory
        estimate = manager.estimate_memory_required(image.size)
        print(f"Processing {image_path} (estimated {estimate/1024**2:.1f}MB)")
        
        # Process
        result = colorize_image(image)
        results.append(result)
        
        # Clean up
        manager.clear_cache()
        
        # Check memory every 5 images
        if (i + 1) % 5 == 0:
            usage = manager.check_memory_usage()
            print(f"Memory usage after {i+1} images: {usage:.2%}")
            manager.trigger_gc_if_needed()
    
    return results
```

## Testing

Run the test suite:

```bash
uv run pytest test_memory_manager.py -v
```

Run the demo:

```bash
uv run python demo_memory_manager.py
```

## Requirements

This module requires:
- PyTorch (torch)
- Python 3.8+

The module automatically detects and adapts to the available device (CUDA, MPS, or CPU).

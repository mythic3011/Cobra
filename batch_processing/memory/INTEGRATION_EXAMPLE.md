# MemoryManager Integration Example

This document shows how the MemoryManager will be integrated with the BatchProcessor.

## Integration with BatchProcessor

```python
import torch
from batch_processing.memory import MemoryManager
from batch_processing.core import ImageQueue, StatusTracker

class BatchProcessor:
    """Main batch processing coordinator with memory management."""
    
    def __init__(self, config: BatchConfig):
        self.config = config
        self.device = torch.device("mps" if torch.backends.mps.is_available() 
                                   else "cuda" if torch.cuda.is_available() 
                                   else "cpu")
        
        # Initialize components
        self.queue = ImageQueue()
        self.status_tracker = StatusTracker()
        
        # Initialize memory manager with 80% threshold
        self.memory_manager = MemoryManager(
            device=self.device,
            memory_threshold=0.8
        )
        
        logger.info(f"BatchProcessor initialized with device: {self.device}")
    
    def process_single_image(self, item: ImageQueueItem) -> ProcessingResult:
        """Process a single image with memory management."""
        try:
            # Update status
            self.status_tracker.update_status(
                item.id, 
                ProcessingStatus(id=item.id, state="processing", start_time=time.time())
            )
            
            # Estimate memory needed
            image = Image.open(item.input_path)
            memory_estimate = self.memory_manager.estimate_memory_required(image.size)
            logger.info(f"Processing {item.id}, estimated memory: {memory_estimate/1024**2:.1f}MB")
            
            # Process the image
            result = colorize_image(
                image=image,
                reference_images=self.config.reference_images,
                style=self.config.style,
                seed=self.config.seed,
                num_inference_steps=self.config.num_inference_steps,
                top_k=self.config.top_k
            )
            
            # Save result
            result.save(item.output_path)
            
            # Update status to completed
            self.status_tracker.update_status(
                item.id,
                ProcessingStatus(
                    id=item.id,
                    state="completed",
                    end_time=time.time(),
                    output_path=item.output_path
                )
            )
            
            return ProcessingResult(
                success=True,
                output_image=result,
                output_path=item.output_path,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error processing {item.id}: {e}")
            self.status_tracker.update_status(
                item.id,
                ProcessingStatus(
                    id=item.id,
                    state="failed",
                    error_message=str(e)
                )
            )
            return ProcessingResult(success=False, error=str(e))
        
        finally:
            # CRITICAL: Clear GPU cache after each image
            self.memory_manager.clear_cache()
            logger.debug(f"Cleared cache after processing {item.id}")
    
    def start_processing(self) -> None:
        """Process all images in the queue with memory management."""
        total_images = self.queue.size()
        logger.info(f"Starting batch processing of {total_images} images")
        
        processed_count = 0
        
        while not self.queue.is_empty():
            # Get next item
            item = self.queue.dequeue()
            
            # Process the image
            result = self.process_single_image(item)
            processed_count += 1
            
            # Check memory usage every 5 images
            if processed_count % 5 == 0:
                usage = self.memory_manager.check_memory_usage()
                logger.info(f"Progress: {processed_count}/{total_images}, Memory: {usage:.2%}")
                
                # Trigger GC if needed
                self.memory_manager.trigger_gc_if_needed()
            
            # Check for pause/cancel requests
            if self.should_pause:
                logger.info("Batch processing paused")
                break
            
            if self.should_cancel:
                logger.info("Batch processing cancelled")
                break
        
        # Final cleanup
        logger.info("Batch processing complete, performing final cleanup")
        self.memory_manager.clear_cache()
        self.memory_manager.trigger_gc_if_needed()
        
        final_usage = self.memory_manager.check_memory_usage()
        logger.info(f"Final memory usage: {final_usage:.2%}")
```

## Memory Management Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Batch Processing Start                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │ Initialize             │
            │ MemoryManager          │
            │ (threshold: 80%)       │
            └────────────┬───────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │ For each image:        │
            └────────────┬───────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │ 1. Estimate memory     │
            │    needed              │
            └────────────┬───────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │ 2. Process image       │
            └────────────┬───────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │ 3. Clear GPU cache     │
            │    (ALWAYS)            │
            └────────────┬───────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │ 4. Every 5 images:     │
            │    - Check usage       │
            │    - Trigger GC if     │
            │      needed            │
            └────────────┬───────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │ More images?           │
            └────┬───────────────┬───┘
                 │ Yes           │ No
                 │               │
                 ▼               ▼
            ┌────────┐   ┌──────────────┐
            │ Loop   │   │ Final        │
            │ back   │   │ cleanup      │
            └────────┘   └──────┬───────┘
                                │
                                ▼
                    ┌───────────────────┐
                    │ Batch Complete    │
                    └───────────────────┘
```

## Error Handling with Memory Management

```python
def process_single_image_with_error_handling(self, item: ImageQueueItem) -> ProcessingResult:
    """Process image with OOM error handling."""
    max_retries = 2
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Check if we have enough memory
            image = Image.open(item.input_path)
            memory_needed = self.memory_manager.estimate_memory_required(image.size)
            current_usage = self.memory_manager.check_memory_usage()
            
            # If memory is tight, clean up first
            if current_usage > 0.7:
                logger.warning(f"High memory usage ({current_usage:.2%}), cleaning up before processing")
                self.memory_manager.clear_cache()
                self.memory_manager.trigger_gc_if_needed()
            
            # Process the image
            result = self.process_image(image, item)
            
            # Success - clear cache and return
            self.memory_manager.clear_cache()
            return result
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.error(f"OOM error on attempt {retry_count + 1}/{max_retries}")
                
                # Aggressive cleanup
                self.memory_manager.clear_cache()
                self.memory_manager.trigger_gc_if_needed()
                
                retry_count += 1
                
                if retry_count < max_retries:
                    logger.info("Retrying after cleanup...")
                    time.sleep(1)  # Brief pause
                else:
                    logger.error(f"Failed after {max_retries} attempts, skipping image")
                    return ProcessingResult(
                        success=False,
                        error="Out of memory - image too large"
                    )
            else:
                # Other error - don't retry
                raise
        
        finally:
            # Always clear cache
            self.memory_manager.clear_cache()
```

## Memory-Aware Batch Planning

```python
def plan_batch_size(image_paths: List[str], device: torch.device) -> int:
    """Determine optimal batch size based on available memory."""
    manager = MemoryManager(device)
    
    # Sample first image to estimate
    sample_image = Image.open(image_paths[0])
    memory_per_image = manager.estimate_memory_required(sample_image.size)
    
    # Get available memory
    if device.type == "cuda":
        total_memory = torch.cuda.get_device_properties(device).total_memory
        available = total_memory * 0.8  # Use 80% of total
    elif device.type == "mps":
        # Conservative estimate for MPS
        available = 4 * 1024**3  # 4GB
    else:
        # CPU - no limit
        return len(image_paths)
    
    # Calculate how many images we can process
    max_concurrent = int(available / memory_per_image)
    
    logger.info(f"Memory per image: {memory_per_image/1024**2:.1f}MB")
    logger.info(f"Available memory: {available/1024**2:.1f}MB")
    logger.info(f"Recommended batch size: {max_concurrent}")
    
    return max(1, max_concurrent)
```

## Monitoring and Logging

```python
def log_memory_stats(self, image_id: str, stage: str) -> None:
    """Log memory statistics at different processing stages."""
    usage = self.memory_manager.check_memory_usage()
    
    if self.device.type == "cuda":
        allocated = torch.cuda.memory_allocated(self.device) / 1024**2
        reserved = torch.cuda.memory_reserved(self.device) / 1024**2
        logger.info(
            f"[{image_id}] {stage}: "
            f"Usage={usage:.2%}, "
            f"Allocated={allocated:.1f}MB, "
            f"Reserved={reserved:.1f}MB"
        )
    elif self.device.type == "mps":
        allocated = torch.mps.current_allocated_memory() / 1024**2
        logger.info(
            f"[{image_id}] {stage}: "
            f"Usage={usage:.2%}, "
            f"Allocated={allocated:.1f}MB"
        )
    else:
        logger.info(f"[{image_id}] {stage}: CPU mode")

# Usage in processing:
def process_single_image(self, item: ImageQueueItem) -> ProcessingResult:
    self.log_memory_stats(item.id, "start")
    
    # ... process image ...
    
    self.log_memory_stats(item.id, "after_inference")
    self.memory_manager.clear_cache()
    self.log_memory_stats(item.id, "after_cleanup")
```

## Best Practices Summary

1. **Always clear cache after each image**
   ```python
   try:
       result = process_image(image)
   finally:
       self.memory_manager.clear_cache()
   ```

2. **Check memory periodically (every 5-10 images)**
   ```python
   if processed_count % 5 == 0:
       self.memory_manager.trigger_gc_if_needed()
   ```

3. **Estimate before processing**
   ```python
   estimate = self.memory_manager.estimate_memory_required(image.size)
   logger.info(f"Estimated memory: {estimate/1024**2:.1f}MB")
   ```

4. **Handle OOM errors gracefully**
   ```python
   except RuntimeError as e:
       if "out of memory" in str(e).lower():
           self.memory_manager.clear_cache()
           self.memory_manager.trigger_gc_if_needed()
           # Retry or skip
   ```

5. **Final cleanup at batch end**
   ```python
   self.memory_manager.clear_cache()
   self.memory_manager.trigger_gc_if_needed()
   ```

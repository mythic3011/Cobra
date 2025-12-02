"""
Batch processor for colorizing multiple images.

This module provides the BatchProcessor class which orchestrates the
batch colorization of multiple comic line art images.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
import uuid

import torch
from PIL import Image

from .config import BatchConfig
from .core.queue import ImageQueue, ImageQueueItem
from .core.status import StatusTracker, ProcessingState
from .memory.memory_manager import MemoryManager
from .io.file_handler import validate_image_file, create_output_path, handle_filename_collision
from .exceptions import BatchProcessingError, ImageProcessingError, ValidationError
from .logging_config import get_logger

logger = get_logger(__name__)


class BatchProcessor:
    """
    Main batch processing coordinator for comic line art colorization.
    
    This class orchestrates the processing of multiple images through the
    colorization pipeline, managing queues, status tracking, and memory.
    
    Attributes:
        config: BatchConfig containing all processing parameters
        queue: ImageQueue for managing images to process
        status_tracker: StatusTracker for monitoring processing status
        memory_manager: MemoryManager for efficient memory usage
    """
    
    def __init__(self, config: BatchConfig):
        """
        Initialize the BatchProcessor.
        
        Sets up the queue, status tracker, memory manager, and logging
        for batch processing operations.
        
        Args:
            config: BatchConfig with all processing parameters
            
        Raises:
            ValidationError: If configuration is invalid
        """
        logger.info("Initializing BatchProcessor")
        
        # Store configuration
        self.config = config
        logger.debug(f"Configuration: {config.to_dict()}")
        
        # Initialize queue
        self.queue = ImageQueue()
        logger.debug("ImageQueue initialized")
        
        # Initialize status tracker
        self.status_tracker = StatusTracker()
        logger.debug("StatusTracker initialized")
        
        # Initialize memory manager
        # Determine device
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")
        
        self.memory_manager = MemoryManager(device=device, memory_threshold=0.8)
        logger.info(f"MemoryManager initialized for device: {device}")
        
        # Control flags for pause/resume/cancel
        self._paused = False
        self._cancelled = False
        self._processing = False
        
        # Preview mode state
        self._preview_processed = False
        self._preview_approved = False
        self._preview_result = None
        
        logger.info("BatchProcessor initialization complete")

    def add_images(self, image_paths: List[str]) -> None:
        """
        Add images to the processing queue.
        
        Validates each image, creates ImageQueueItem for valid images,
        and enqueues them for processing. Invalid images are skipped
        with logging.
        
        Args:
            image_paths: List of paths to image files to process
            
        Raises:
            ValidationError: If image_paths is empty or all images are invalid
        """
        if not image_paths:
            error_msg = "Cannot add images: image_paths list is empty"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        logger.info(f"Adding {len(image_paths)} images to processing queue")
        
        valid_count = 0
        invalid_count = 0
        
        for image_path in image_paths:
            # Validate image file
            if not validate_image_file(image_path):
                logger.warning(f"Skipping invalid image: {image_path}")
                invalid_count += 1
                continue
            
            try:
                # Generate unique ID for this image
                image_id = str(uuid.uuid4())
                
                # Create output path
                output_path = create_output_path(
                    input_path=image_path,
                    output_dir=self.config.output_dir,
                    suffix="_colorized"
                )
                
                # Handle filename collision
                output_path = handle_filename_collision(
                    path=output_path,
                    overwrite=self.config.overwrite
                )
                
                # Create queue item
                queue_item = ImageQueueItem(
                    id=image_id,
                    input_path=image_path,
                    output_path=output_path,
                    config=None,  # Per-image config can be added later
                    priority=0,
                    image_type="line_art",  # Default type
                    classification_confidence=None
                )
                
                # Enqueue the item
                self.queue.enqueue(queue_item)
                
                # Add to status tracker
                self.status_tracker.add_image(image_id)
                
                valid_count += 1
                logger.debug(f"Added to queue: {Path(image_path).name} -> {Path(output_path).name}")
                
            except Exception as e:
                logger.error(f"Failed to add image {image_path}: {str(e)}")
                invalid_count += 1
        
        # Check if any valid images were added
        if valid_count == 0:
            error_msg = f"No valid images added. {invalid_count} images were invalid."
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        logger.info(
            f"Successfully added {valid_count} images to queue. "
            f"Skipped {invalid_count} invalid images."
        )

    def process_single_image(self, queue_item: ImageQueueItem) -> None:
        """
        Process a single image through the colorization pipeline.
        
        This method:
        1. Loads the input image
        2. Extracts line art from the image
        3. Loads reference images
        4. Calls the colorization pipeline
        5. Saves the output with metadata
        6. Updates status tracker
        7. Clears memory after processing
        
        Args:
            queue_item: ImageQueueItem containing image paths and config
            
        Raises:
            ImageProcessingError: If processing fails
        """
        image_id = queue_item.id
        input_path = queue_item.input_path
        output_path = queue_item.output_path
        
        logger.info(f"Processing image: {Path(input_path).name}")
        
        # Save progress before critical operation
        try:
            self.status_tracker.update_status(
                image_id=image_id,
                state=ProcessingState.PROCESSING.value
            )
        except Exception as e:
            logger.error(f"Failed to update status to processing: {e}")
            # Continue anyway - status update failure shouldn't stop processing
        
        # Track which stage failed for better error reporting
        current_stage = "initialization"
        
        try:
            # Import colorization functions from app.py
            # Note: This is a simplified integration - in production, these would be
            # refactored into a separate module
            current_stage = "importing modules"
            logger.debug(f"Stage: {current_stage}")
            
            try:
                from app import (
                    extract_sketch_line_image,
                    colorize_image,
                    process_multi_images,
                    device
                )
            except ImportError as e:
                raise ImageProcessingError(
                    input_path,
                    f"Failed to import colorization modules: {e}"
                ) from e
            
            # Load input image
            current_stage = "loading input image"
            logger.debug(f"Stage: {current_stage} - {input_path}")
            
            try:
                input_image = Image.open(input_path)
            except FileNotFoundError:
                raise ImageProcessingError(
                    input_path,
                    f"Input file not found: {input_path}"
                )
            except PermissionError:
                raise ImageProcessingError(
                    input_path,
                    f"Permission denied reading file: {input_path}"
                )
            except Exception as e:
                raise ImageProcessingError(
                    input_path,
                    f"Failed to load image: {e}"
                ) from e
            
            # Extract line art from input image
            current_stage = "extracting line art"
            logger.debug(f"Stage: {current_stage}")
            
            try:
                (
                    extracted_line,
                    hint_color,
                    hint_mask,
                    query_image_origin,
                    extracted_image_ori,
                    resolution
                ) = extract_sketch_line_image(input_image, self.config.style)
            except Exception as e:
                raise ImageProcessingError(
                    input_path,
                    f"Failed to extract line art: {e}"
                ) from e
            
            # Load reference images
            current_stage = "loading reference images"
            logger.debug(f"Stage: {current_stage} - {len(self.config.reference_images)} references")
            
            try:
                # Create file-like objects for reference images
                class FileWrapper:
                    def __init__(self, path):
                        self.name = path
                
                reference_files = [FileWrapper(ref) for ref in self.config.reference_images]
            except Exception as e:
                raise ImageProcessingError(
                    input_path,
                    f"Failed to prepare reference images: {e}"
                ) from e
            
            # Call colorization pipeline
            current_stage = "running colorization pipeline"
            logger.debug(f"Stage: {current_stage}")
            
            try:
                output_gallery = colorize_image(
                    extracted_line=extracted_line,
                    reference_images=reference_files,
                    resolution=resolution,
                    seed=self.config.seed,
                    num_inference_steps=self.config.num_inference_steps,
                    top_k=self.config.top_k,
                    hint_mask=hint_mask,
                    hint_color=hint_color,
                    query_image_origin=query_image_origin,
                    extracted_image_ori=extracted_image_ori
                )
            except RuntimeError as e:
                # Check if it's an OOM error
                if "out of memory" in str(e).lower() or "oom" in str(e).lower():
                    logger.error(f"Out of memory error during colorization: {e}")
                    # Try to clear memory and re-raise with helpful message
                    try:
                        self.memory_manager.clear_cache()
                        self.memory_manager.trigger_gc_if_needed()
                    except Exception as mem_error:
                        logger.warning(f"Failed to clear memory after OOM: {mem_error}")
                    
                    raise ImageProcessingError(
                        input_path,
                        f"Out of memory during colorization. Try reducing image size or closing other applications."
                    ) from e
                else:
                    raise ImageProcessingError(
                        input_path,
                        f"Runtime error during colorization: {e}"
                    ) from e
            except Exception as e:
                raise ImageProcessingError(
                    input_path,
                    f"Failed during colorization: {e}"
                ) from e
            
            # Extract result
            current_stage = "extracting result"
            logger.debug(f"Stage: {current_stage}")
            
            try:
                if not output_gallery or len(output_gallery) == 0:
                    raise ImageProcessingError(
                        input_path,
                        "Colorization produced no output"
                    )
                colorized_image = output_gallery[0]
            except (IndexError, TypeError) as e:
                raise ImageProcessingError(
                    input_path,
                    f"Failed to extract colorized result: {e}"
                ) from e
            
            # Save output image
            current_stage = "saving output"
            logger.debug(f"Stage: {current_stage} - {output_path}")
            
            try:
                # Ensure output directory exists
                output_dir = Path(output_path).parent
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Save the image
                colorized_image.save(output_path)
            except PermissionError:
                raise ImageProcessingError(
                    input_path,
                    f"Permission denied writing to: {output_path}"
                )
            except OSError as e:
                if "No space left on device" in str(e):
                    raise ImageProcessingError(
                        input_path,
                        f"Disk full - cannot save output: {output_path}"
                    ) from e
                else:
                    raise ImageProcessingError(
                        input_path,
                        f"Failed to save output: {e}"
                    ) from e
            except Exception as e:
                raise ImageProcessingError(
                    input_path,
                    f"Unexpected error saving output: {e}"
                ) from e
            
            # Verify output was saved
            current_stage = "verifying output"
            logger.debug(f"Stage: {current_stage}")
            
            if not Path(output_path).exists():
                raise ImageProcessingError(
                    input_path,
                    "Output file was not created"
                )
            
            # Verify file is not empty
            if Path(output_path).stat().st_size == 0:
                raise ImageProcessingError(
                    input_path,
                    "Output file is empty"
                )
            
            # Update status to completed
            current_stage = "updating status"
            logger.debug(f"Stage: {current_stage}")
            
            try:
                self.status_tracker.update_status(
                    image_id=image_id,
                    state=ProcessingState.COMPLETED.value,
                    output_path=output_path
                )
            except Exception as e:
                logger.error(f"Failed to update status to completed: {e}")
                # Don't fail the whole operation if status update fails
            
            logger.info(f"Successfully processed: {Path(input_path).name}")
            
        except ImageProcessingError:
            # Already properly formatted, just update status and re-raise
            logger.error(f"Processing failed at stage '{current_stage}': {input_path}")
            
            try:
                self.status_tracker.update_status(
                    image_id=image_id,
                    state=ProcessingState.FAILED.value,
                    error_message=f"Failed at {current_stage}"
                )
            except Exception as status_error:
                logger.error(f"Failed to update status: {status_error}")
            
            raise
            
        except Exception as e:
            # Unexpected error - wrap with context
            error_msg = f"Unexpected error at stage '{current_stage}': {str(e)}"
            logger.error(f"Processing failed: {error_msg}", exc_info=True)
            
            try:
                self.status_tracker.update_status(
                    image_id=image_id,
                    state=ProcessingState.FAILED.value,
                    error_message=error_msg
                )
            except Exception as status_error:
                logger.error(f"Failed to update status: {status_error}")
            
            # Re-raise as ImageProcessingError with full context
            raise ImageProcessingError(input_path, error_msg) from e
        
        finally:
            # Always clear memory after processing (success or failure)
            logger.debug("Clearing memory after image processing")
            try:
                self.memory_manager.clear_cache()
            except Exception as e:
                logger.warning(f"Failed to clear memory cache: {e}")

    def start_processing(self) -> None:
        """
        Start processing all images in the queue.
        
        Processes images sequentially from the queue, handling errors
        gracefully without stopping the batch. Updates progress information
        and triggers memory cleanup between images.
        
        The method respects pause and cancel flags, allowing the user to
        control the batch processing flow.
        
        In preview mode, only the first image is processed and the method
        waits for user approval before continuing with remaining images.
        
        Raises:
            BatchProcessingError: If processing cannot start (e.g., empty queue)
        """
        # Check if queue is empty
        if self.queue.size() == 0:
            error_msg = "Cannot start processing: queue is empty"
            logger.error(error_msg)
            raise BatchProcessingError(error_msg)
        
        # Check if already processing
        if self._processing:
            logger.warning("Processing is already in progress")
            return
        
        # Check if in preview mode and already processed preview
        if self.config.preview_mode and self._preview_processed and not self._preview_approved:
            logger.info("Preview mode: waiting for user approval before continuing")
            return
        
        logger.info(f"Starting batch processing of {self.queue.size()} images")
        if self.config.preview_mode and not self._preview_processed:
            logger.info("Preview mode enabled - will process first image only")
        
        # Set processing flag
        self._processing = True
        self._cancelled = False
        self._paused = False
        
        # Track progress
        total_images = self.queue.size()
        processed_count = 0
        failed_count = 0
        
        try:
            # In preview mode, process only the first image
            if self.config.preview_mode and not self._preview_processed:
                # Dequeue first image
                queue_item = self.queue.dequeue()
                if queue_item is None:
                    logger.error("Failed to dequeue first image for preview")
                    return
                
                logger.info(f"Processing preview image: {Path(queue_item.input_path).name}")
                
                # Save progress before preview processing
                logger.debug(f"Starting preview processing: {queue_item.input_path}")
                
                # Process the preview image
                try:
                    self.process_single_image(queue_item)
                    
                    # Store preview result
                    try:
                        status = self.status_tracker.get_status(queue_item.id)
                    except Exception as e:
                        logger.warning(f"Failed to get status for preview: {e}")
                        status = None
                    
                    self._preview_result = {
                        "output_path": queue_item.output_path,
                        "input_path": queue_item.input_path,
                        "status": status,
                        "image_id": queue_item.id
                    }
                    
                    self._preview_processed = True
                    
                    logger.info(
                        f"Preview processing complete. "
                        f"Output saved to: {queue_item.output_path}"
                    )
                    logger.info(
                        f"Waiting for user approval. "
                        f"{self.queue.size()} images remaining in queue."
                    )
                    
                except ImageProcessingError as e:
                    # Expected error type - log and store result
                    logger.error(
                        f"Preview image processing failed: {str(e)} "
                        f"(User can adjust settings and retry)"
                    )
                    
                    try:
                        status = self.status_tracker.get_status(queue_item.id)
                    except Exception as status_error:
                        logger.warning(f"Failed to get status: {status_error}")
                        status = None
                    
                    self._preview_result = {
                        "output_path": None,
                        "input_path": queue_item.input_path,
                        "status": status,
                        "error": str(e),
                        "image_id": queue_item.id
                    }
                    self._preview_processed = True
                    
                except Exception as e:
                    # Unexpected error - log with full context
                    logger.error(
                        f"Unexpected error processing preview: {str(e)} "
                        f"(User can adjust settings and retry)",
                        exc_info=True
                    )
                    
                    # Update status to failed
                    try:
                        self.status_tracker.update_status(
                            image_id=queue_item.id,
                            state=ProcessingState.FAILED.value,
                            error_message=f"Unexpected error: {str(e)}"
                        )
                    except Exception as status_error:
                        logger.error(f"Failed to update status: {status_error}")
                    
                    try:
                        status = self.status_tracker.get_status(queue_item.id)
                    except Exception as status_error:
                        logger.warning(f"Failed to get status: {status_error}")
                        status = None
                    
                    self._preview_result = {
                        "output_path": None,
                        "input_path": queue_item.input_path,
                        "status": status,
                        "error": f"Unexpected error: {str(e)}",
                        "image_id": queue_item.id
                    }
                    self._preview_processed = True
                
                # Trigger memory cleanup after preview
                try:
                    self.memory_manager.trigger_gc_if_needed()
                except Exception as mem_error:
                    logger.warning(f"Memory cleanup failed: {mem_error}")
                
                return  # Stop here and wait for approval
            
            # Normal processing (non-preview mode or after preview approval)
            # Process images sequentially
            while self.queue.size() > 0:
                # Check for pause
                if self._paused:
                    logger.info("Processing paused")
                    break
                
                # Check for cancellation
                if self._cancelled:
                    logger.info("Processing cancelled")
                    # Mark remaining images as cancelled
                    while self.queue.size() > 0:
                        item = self.queue.dequeue()
                        if item:
                            self.status_tracker.update_status(
                                image_id=item.id,
                                state=ProcessingState.CANCELLED.value
                            )
                    break
                
                # Dequeue next image
                queue_item = self.queue.dequeue()
                if queue_item is None:
                    break
                
                # Update progress
                processed_count += 1
                logger.info(
                    f"Processing image {processed_count}/{total_images}: "
                    f"{Path(queue_item.input_path).name}"
                )
                
                # Save progress before processing (in case of crash)
                try:
                    # Log current state for recovery
                    logger.debug(
                        f"About to process: {queue_item.input_path} "
                        f"(Progress: {processed_count}/{total_images})"
                    )
                except Exception as log_error:
                    # Don't fail if logging fails
                    pass
                
                # Process the image
                try:
                    self.process_single_image(queue_item)
                    
                except ImageProcessingError as e:
                    # Log error but continue with next image (resilience requirement)
                    logger.error(
                        f"Image processing failed: {str(e)} "
                        f"(Continuing with remaining images)"
                    )
                    failed_count += 1
                    # Status already updated in process_single_image
                    
                except Exception as e:
                    # Unexpected error - log with full context and continue
                    logger.error(
                        f"Unexpected error processing {queue_item.input_path}: {str(e)} "
                        f"(Continuing with remaining images)",
                        exc_info=True
                    )
                    failed_count += 1
                    
                    # Update status to failed
                    try:
                        self.status_tracker.update_status(
                            image_id=queue_item.id,
                            state=ProcessingState.FAILED.value,
                            error_message=f"Unexpected error: {str(e)}"
                        )
                    except Exception as status_error:
                        logger.error(f"Failed to update status: {status_error}")
                
                # Trigger memory cleanup between images
                try:
                    self.memory_manager.trigger_gc_if_needed()
                except Exception as mem_error:
                    logger.warning(f"Memory cleanup failed: {mem_error}")
            
            # Get final summary
            summary = self.status_tracker.get_summary()
            
            # Log completion
            if self._cancelled:
                logger.info(
                    f"Batch processing cancelled. "
                    f"Completed: {summary.completed}, "
                    f"Failed: {summary.failed}, "
                    f"Cancelled: {summary.cancelled}"
                )
            elif self._paused:
                logger.info(
                    f"Batch processing paused. "
                    f"Completed: {summary.completed}, "
                    f"Failed: {summary.failed}, "
                    f"Pending: {summary.pending}"
                )
            else:
                logger.info(
                    f"Batch processing complete. "
                    f"Total: {summary.total}, "
                    f"Completed: {summary.completed}, "
                    f"Failed: {summary.failed}"
                )
                
                if summary.elapsed_time:
                    logger.info(f"Total processing time: {summary.elapsed_time:.2f} seconds")
                
                if summary.completed > 0:
                    logger.info(f"Success rate: {summary.success_rate:.1f}%")
        
        finally:
            # Clear processing flag (but not in preview mode waiting for approval)
            if not (self.config.preview_mode and self._preview_processed and not self._preview_approved):
                self._processing = False
            
            # Final memory cleanup
            try:
                self.memory_manager.clear_cache()
                logger.debug("Final memory cleanup complete")
            except Exception as e:
                logger.warning(f"Final memory cleanup failed: {e}")
    
    def pause_processing(self) -> None:
        """
        Pause batch processing.
        
        The current image will complete processing, but the next image
        will not start until resume_processing() is called.
        """
        if not self._processing:
            logger.warning("Cannot pause: processing is not active")
            return
        
        if self._paused:
            logger.warning("Processing is already paused")
            return
        
        logger.info("Pausing batch processing")
        self._paused = True
    
    def resume_processing(self) -> None:
        """
        Resume paused batch processing.
        
        Processing will continue with the next unprocessed image in the queue.
        """
        if not self._paused:
            logger.warning("Cannot resume: processing is not paused")
            return
        
        logger.info("Resuming batch processing")
        self._paused = False
        
        # Continue processing
        self.start_processing()
    
    def cancel_processing(self) -> None:
        """
        Cancel batch processing.
        
        Processing will stop and all remaining images will be marked as cancelled.
        """
        if not self._processing:
            logger.warning("Cannot cancel: processing is not active")
            return
        
        if self._cancelled:
            logger.warning("Processing is already cancelled")
            return
        
        logger.info("Cancelling batch processing")
        self._cancelled = True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current batch processing status.
        
        Returns:
            Dictionary containing status information including:
            - summary: StatusSummary with counts and timing
            - is_processing: Whether processing is currently active
            - is_paused: Whether processing is paused
            - is_cancelled: Whether processing was cancelled
            - queue_size: Number of images remaining in queue
        """
        summary = self.status_tracker.get_summary()
        
        return {
            "summary": summary,
            "is_processing": self._processing,
            "is_paused": self._paused,
            "is_cancelled": self._cancelled,
            "queue_size": self.queue.size(),
            "total_images": summary.total,
            "completed": summary.completed,
            "failed": summary.failed,
            "pending": summary.pending,
            "processing": summary.processing,
            "cancelled": summary.cancelled,
            "success_rate": summary.success_rate,
            "elapsed_time": summary.elapsed_time,
        }
    
    def is_preview_mode(self) -> bool:
        """
        Check if preview mode is enabled.
        
        Returns:
            True if preview mode is enabled, False otherwise
        """
        return self.config.preview_mode
    
    def is_waiting_for_preview_approval(self) -> bool:
        """
        Check if the processor is waiting for preview approval.
        
        Returns:
            True if preview has been processed and is waiting for approval
        """
        return self._preview_processed and not self._preview_approved
    
    def get_preview_result(self) -> Optional[Dict[str, Any]]:
        """
        Get the preview processing result.
        
        Returns:
            Dictionary containing preview result information:
            - output_path: Path to the preview output image
            - input_path: Path to the preview input image
            - status: Processing status of the preview image
            Returns None if no preview has been processed
        """
        return self._preview_result
    
    def approve_preview(self) -> None:
        """
        Approve the preview result and continue processing remaining images.
        
        This method should be called after the user has reviewed the preview
        result and wants to proceed with the same settings.
        
        Raises:
            BatchProcessingError: If not in preview mode or no preview to approve
        """
        if not self.config.preview_mode:
            error_msg = "Cannot approve preview: preview mode is not enabled"
            logger.error(error_msg)
            raise BatchProcessingError(error_msg)
        
        if not self._preview_processed:
            error_msg = "Cannot approve preview: no preview has been processed"
            logger.error(error_msg)
            raise BatchProcessingError(error_msg)
        
        if self._preview_approved:
            logger.warning("Preview has already been approved")
            return
        
        logger.info("Preview approved - continuing with remaining images")
        self._preview_approved = True
        
        # Continue processing remaining images
        self._continue_after_preview()
    
    def reject_preview(self) -> None:
        """
        Reject the preview result and stop processing.
        
        This method should be called after the user has reviewed the preview
        result and wants to adjust settings before processing the batch.
        
        The user can then modify the configuration and restart processing.
        
        Raises:
            BatchProcessingError: If not in preview mode or no preview to reject
        """
        if not self.config.preview_mode:
            error_msg = "Cannot reject preview: preview mode is not enabled"
            logger.error(error_msg)
            raise BatchProcessingError(error_msg)
        
        if not self._preview_processed:
            error_msg = "Cannot reject preview: no preview has been processed"
            logger.error(error_msg)
            raise BatchProcessingError(error_msg)
        
        logger.info("Preview rejected - stopping processing for settings adjustment")
        
        # Reset preview state
        self._preview_processed = False
        self._preview_approved = False
        self._preview_result = None
        
        # Mark remaining images as pending (they're already in that state)
        logger.info("Remaining images are still in queue and can be reprocessed with new settings")
    
    def _continue_after_preview(self) -> None:
        """
        Continue processing remaining images after preview approval.
        
        This is an internal method called after preview approval.
        """
        if self.queue.size() == 0:
            logger.info("No remaining images to process after preview")
            return
        
        logger.info(f"Continuing with {self.queue.size()} remaining images")
        
        # Process remaining images
        processed_count = 1  # Preview was the first image
        total_images = self.queue.size() + 1  # Include the preview image
        failed_count = 0
        
        try:
            while self.queue.size() > 0:
                # Check for pause
                if self._paused:
                    logger.info("Processing paused")
                    break
                
                # Check for cancellation
                if self._cancelled:
                    logger.info("Processing cancelled")
                    # Mark remaining images as cancelled
                    while self.queue.size() > 0:
                        item = self.queue.dequeue()
                        if item:
                            self.status_tracker.update_status(
                                image_id=item.id,
                                state=ProcessingState.CANCELLED.value
                            )
                    break
                
                # Dequeue next image
                queue_item = self.queue.dequeue()
                if queue_item is None:
                    break
                
                # Update progress
                processed_count += 1
                logger.info(
                    f"Processing image {processed_count}/{total_images}: "
                    f"{Path(queue_item.input_path).name}"
                )
                
                # Save progress before processing
                try:
                    logger.debug(
                        f"About to process: {queue_item.input_path} "
                        f"(Progress: {processed_count}/{total_images})"
                    )
                except Exception:
                    pass
                
                # Process the image
                try:
                    self.process_single_image(queue_item)
                    
                except ImageProcessingError as e:
                    # Log error but continue with next image (resilience requirement)
                    logger.error(
                        f"Image processing failed: {str(e)} "
                        f"(Continuing with remaining images)"
                    )
                    failed_count += 1
                    
                except Exception as e:
                    # Unexpected error - log with full context and continue
                    logger.error(
                        f"Unexpected error processing {queue_item.input_path}: {str(e)} "
                        f"(Continuing with remaining images)",
                        exc_info=True
                    )
                    failed_count += 1
                    
                    # Update status to failed
                    try:
                        self.status_tracker.update_status(
                            image_id=queue_item.id,
                            state=ProcessingState.FAILED.value,
                            error_message=f"Unexpected error: {str(e)}"
                        )
                    except Exception as status_error:
                        logger.error(f"Failed to update status: {status_error}")
                
                # Trigger memory cleanup between images
                try:
                    self.memory_manager.trigger_gc_if_needed()
                except Exception as mem_error:
                    logger.warning(f"Memory cleanup failed: {mem_error}")
            
            # Get final summary
            summary = self.status_tracker.get_summary()
            
            # Log completion
            logger.info(
                f"Batch processing complete after preview approval. "
                f"Total: {summary.total}, "
                f"Completed: {summary.completed}, "
                f"Failed: {summary.failed}"
            )
            
            if summary.elapsed_time:
                logger.info(f"Total processing time: {summary.elapsed_time:.2f} seconds")
            
            if summary.completed > 0:
                logger.info(f"Success rate: {summary.success_rate:.1f}%")
        
        finally:
            # Clear processing flag
            self._processing = False
            
            # Final memory cleanup
            try:
                self.memory_manager.clear_cache()
                logger.debug("Final memory cleanup complete")
            except Exception as e:
                logger.warning(f"Final memory cleanup failed: {e}")

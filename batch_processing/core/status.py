"""
Status tracking system for batch processing operations.

This module provides the StatusTracker class for managing processing status
and the ProcessingStatus dataclass for representing the status of individual images.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum
import time


class ProcessingState(Enum):
    """Enumeration of possible processing states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingStatus:
    """
    Status information for an image in the batch processing queue.
    
    Attributes:
        id: Unique identifier for the image
        state: Current processing state (pending, processing, completed, failed, cancelled)
        start_time: Timestamp when processing started (None if not started)
        end_time: Timestamp when processing ended (None if not ended)
        error_message: Error message if processing failed (None if no error)
        output_path: Path to the output file if completed (None if not completed)
    """
    id: str
    state: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    
    def __post_init__(self):
        """Validate the status after initialization."""
        valid_states = [state.value for state in ProcessingState]
        if self.state not in valid_states:
            raise ValueError(
                f"Invalid state: {self.state}. Must be one of {valid_states}"
            )
    
    @property
    def processing_time(self) -> Optional[float]:
        """
        Calculate the processing time in seconds.
        
        Returns:
            Processing time in seconds if both start and end times are set,
            elapsed time if only start time is set, None otherwise
        """
        if self.start_time is None:
            return None
        
        if self.end_time is not None:
            return self.end_time - self.start_time
        
        # If processing is ongoing, return elapsed time
        return time.time() - self.start_time
    
    def is_terminal_state(self) -> bool:
        """
        Check if the status is in a terminal state.
        
        Returns:
            True if state is completed, failed, or cancelled
        """
        return self.state in [
            ProcessingState.COMPLETED.value,
            ProcessingState.FAILED.value,
            ProcessingState.CANCELLED.value
        ]


@dataclass
class StatusSummary:
    """
    Summary of batch processing status.
    
    Attributes:
        total: Total number of images in the batch
        pending: Number of images pending processing
        processing: Number of images currently being processed
        completed: Number of images successfully completed
        failed: Number of images that failed processing
        cancelled: Number of images that were cancelled
        start_time: Timestamp when batch processing started
        end_time: Timestamp when batch processing ended (None if ongoing)
    """
    total: int
    pending: int = 0
    processing: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def is_complete(self) -> bool:
        """Check if all images have reached a terminal state."""
        return (self.completed + self.failed + self.cancelled) == self.total
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100.0
    
    @property
    def elapsed_time(self) -> Optional[float]:
        """Calculate elapsed time in seconds."""
        if self.start_time is None:
            return None
        
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time


class StatusTracker:
    """
    Tracks processing status for all images in a batch.
    
    This class maintains the status of each image and provides methods
    to update and query status information.
    """
    
    def __init__(self):
        """Initialize an empty status tracker."""
        self._statuses: Dict[str, ProcessingStatus] = {}
        self._batch_start_time: Optional[float] = None
        self._batch_end_time: Optional[float] = None
    
    def add_image(self, image_id: str) -> None:
        """
        Add a new image to track with pending status.
        
        Args:
            image_id: Unique identifier for the image
        """
        if image_id in self._statuses:
            raise ValueError(f"Image {image_id} is already being tracked")
        
        self._statuses[image_id] = ProcessingStatus(
            id=image_id,
            state=ProcessingState.PENDING.value
        )
        
        # Set batch start time on first image
        if self._batch_start_time is None:
            self._batch_start_time = time.time()
    
    def update_status(
        self,
        image_id: str,
        state: str,
        error_message: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> None:
        """
        Update the status of an image.
        
        Args:
            image_id: Unique identifier for the image
            state: New processing state
            error_message: Error message if state is failed
            output_path: Output file path if state is completed
            
        Raises:
            KeyError: If image_id is not being tracked
            ValueError: If state is invalid
        """
        if image_id not in self._statuses:
            raise KeyError(f"Image {image_id} is not being tracked")
        
        # Validate state
        valid_states = [state.value for state in ProcessingState]
        if state not in valid_states:
            raise ValueError(
                f"Invalid state: {state}. Must be one of {valid_states}"
            )
        
        status = self._statuses[image_id]
        old_state = status.state
        status.state = state
        
        # Update timestamps based on state transitions
        current_time = time.time()
        
        if state == ProcessingState.PROCESSING.value and old_state == ProcessingState.PENDING.value:
            status.start_time = current_time
        
        if state in [ProcessingState.COMPLETED.value, ProcessingState.FAILED.value, ProcessingState.CANCELLED.value]:
            if status.end_time is None:
                status.end_time = current_time
        
        # Update error message and output path
        if error_message is not None:
            status.error_message = error_message
        
        if output_path is not None:
            status.output_path = output_path
        
        # Check if batch is complete
        summary = self.get_summary()
        if summary.is_complete and self._batch_end_time is None:
            self._batch_end_time = current_time
    
    def get_status(self, image_id: str) -> ProcessingStatus:
        """
        Get the status of a specific image.
        
        Args:
            image_id: Unique identifier for the image
            
        Returns:
            ProcessingStatus for the image
            
        Raises:
            KeyError: If image_id is not being tracked
        """
        if image_id not in self._statuses:
            raise KeyError(f"Image {image_id} is not being tracked")
        
        return self._statuses[image_id]
    
    def get_all_statuses(self) -> Dict[str, ProcessingStatus]:
        """
        Get the status of all tracked images.
        
        Returns:
            Dictionary mapping image IDs to their ProcessingStatus
        """
        return self._statuses.copy()
    
    def get_summary(self) -> StatusSummary:
        """
        Generate a summary of the batch processing status.
        
        Returns:
            StatusSummary with counts for each state
        """
        summary = StatusSummary(
            total=len(self._statuses),
            start_time=self._batch_start_time,
            end_time=self._batch_end_time
        )
        
        for status in self._statuses.values():
            if status.state == ProcessingState.PENDING.value:
                summary.pending += 1
            elif status.state == ProcessingState.PROCESSING.value:
                summary.processing += 1
            elif status.state == ProcessingState.COMPLETED.value:
                summary.completed += 1
            elif status.state == ProcessingState.FAILED.value:
                summary.failed += 1
            elif status.state == ProcessingState.CANCELLED.value:
                summary.cancelled += 1
        
        return summary
    
    def get_images_by_state(self, state: str) -> List[str]:
        """
        Get all image IDs in a specific state.
        
        Args:
            state: The processing state to filter by
            
        Returns:
            List of image IDs in the specified state
        """
        return [
            image_id
            for image_id, status in self._statuses.items()
            if status.state == state
        ]
    
    def clear(self) -> None:
        """Clear all tracked statuses."""
        self._statuses.clear()
        self._batch_start_time = None
        self._batch_end_time = None
    
    def __len__(self) -> int:
        """Return the number of tracked images."""
        return len(self._statuses)
    
    def __contains__(self, image_id: str) -> bool:
        """Check if an image is being tracked."""
        return image_id in self._statuses

"""
Queue system for batch processing of images.

This module provides the ImageQueue class for managing the processing queue
and the ImageQueueItem dataclass for representing items in the queue.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from collections import deque


@dataclass
class ImageQueueItem:
    """
    Represents an image in the processing queue.
    
    Attributes:
        id: Unique identifier for the queue item
        input_path: Path to the input image file
        output_path: Path where the processed image will be saved
        config: Optional dictionary of image-specific configuration
        priority: Priority level for processing (higher = processed first)
        image_type: Type of image ("line_art" or "colored")
        classification_confidence: Confidence score from image classification
    """
    id: str
    input_path: str
    output_path: str
    config: Optional[Dict] = None
    priority: int = 0
    image_type: Optional[str] = None
    classification_confidence: Optional[float] = None
    
    def __post_init__(self):
        """Validate the queue item after initialization."""
        if self.image_type is not None and self.image_type not in ["line_art", "colored"]:
            raise ValueError(f"Invalid image_type: {self.image_type}. Must be 'line_art' or 'colored'")
        
        if self.classification_confidence is not None:
            if not 0.0 <= self.classification_confidence <= 1.0:
                raise ValueError(f"classification_confidence must be between 0 and 1, got {self.classification_confidence}")


class ImageQueue:
    """
    Manages the queue of images to process.
    
    This class provides a priority queue implementation for batch image processing.
    Images can be enqueued with different priorities, and higher priority items
    are dequeued first.
    """
    
    def __init__(self):
        """Initialize an empty image queue."""
        self._queue: List[ImageQueueItem] = []
        self._size: int = 0
    
    def enqueue(self, item: ImageQueueItem) -> None:
        """
        Add an item to the queue.
        
        Items are inserted in priority order (higher priority first).
        Items with the same priority maintain FIFO order.
        
        Args:
            item: The ImageQueueItem to add to the queue
        """
        if not isinstance(item, ImageQueueItem):
            raise TypeError(f"Expected ImageQueueItem, got {type(item)}")
        
        # Find the correct position to insert based on priority
        insert_pos = len(self._queue)
        for i, queued_item in enumerate(self._queue):
            if item.priority > queued_item.priority:
                insert_pos = i
                break
        
        self._queue.insert(insert_pos, item)
        self._size += 1
    
    def dequeue(self) -> Optional[ImageQueueItem]:
        """
        Remove and return the highest priority item from the queue.
        
        Returns:
            The next ImageQueueItem to process, or None if queue is empty
        """
        if self._size == 0:
            return None
        
        item = self._queue.pop(0)
        self._size -= 1
        return item
    
    def peek(self) -> Optional[ImageQueueItem]:
        """
        View the highest priority item without removing it.
        
        Returns:
            The next ImageQueueItem that would be dequeued, or None if queue is empty
        """
        if self._size == 0:
            return None
        
        return self._queue[0]
    
    def size(self) -> int:
        """
        Get the current number of items in the queue.
        
        Returns:
            The number of items in the queue
        """
        return self._size
    
    def clear(self) -> None:
        """
        Remove all items from the queue.
        """
        self._queue.clear()
        self._size = 0
    
    def __len__(self) -> int:
        """Support len() function."""
        return self._size
    
    def __iter__(self):
        """Support iteration over queue items."""
        return iter(self._queue)
    
    def __bool__(self) -> bool:
        """Support boolean evaluation (True if not empty)."""
        return self._size > 0

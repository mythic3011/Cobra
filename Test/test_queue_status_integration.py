"""
Integration test showing how ImageQueue and StatusTracker work together.

This demonstrates the typical workflow of batch processing where images
are queued and their status is tracked throughout processing.
"""

import pytest
from batch_processing.core import ImageQueue, ImageQueueItem, StatusTracker, ProcessingState


def test_queue_and_status_integration():
    """Test that queue and status tracker work together correctly."""
    # Create queue and status tracker
    queue = ImageQueue()
    tracker = StatusTracker()
    
    # Add images to queue
    images = [
        ImageQueueItem(
            id="img_001",
            input_path="/input/page_001.png",
            output_path="/output/page_001.png"
        ),
        ImageQueueItem(
            id="img_002",
            input_path="/input/page_002.png",
            output_path="/output/page_002.png"
        ),
        ImageQueueItem(
            id="img_003",
            input_path="/input/page_003.png",
            output_path="/output/page_003.png"
        )
    ]
    
    # Enqueue all images and add to status tracker
    for item in images:
        queue.enqueue(item)
        tracker.add_image(item.id)
    
    # Verify initial state
    assert queue.size() == 3
    assert len(tracker) == 3
    
    summary = tracker.get_summary()
    assert summary.total == 3
    assert summary.pending == 3
    assert summary.processing == 0
    assert summary.completed == 0
    
    # Process first image
    item = queue.dequeue()
    assert item.id == "img_001"
    
    tracker.update_status(item.id, ProcessingState.PROCESSING.value)
    summary = tracker.get_summary()
    assert summary.pending == 2
    assert summary.processing == 1
    
    # Complete first image
    tracker.update_status(
        item.id,
        ProcessingState.COMPLETED.value,
        output_path=item.output_path
    )
    summary = tracker.get_summary()
    assert summary.processing == 0
    assert summary.completed == 1
    
    # Process second image
    item = queue.dequeue()
    assert item.id == "img_002"
    
    tracker.update_status(item.id, ProcessingState.PROCESSING.value)
    
    # Fail second image
    tracker.update_status(
        item.id,
        ProcessingState.FAILED.value,
        error_message="Processing error"
    )
    summary = tracker.get_summary()
    assert summary.completed == 1
    assert summary.failed == 1
    
    # Process third image
    item = queue.dequeue()
    assert item.id == "img_003"
    
    tracker.update_status(item.id, ProcessingState.PROCESSING.value)
    tracker.update_status(
        item.id,
        ProcessingState.COMPLETED.value,
        output_path=item.output_path
    )
    
    # Verify final state
    assert queue.size() == 0
    
    summary = tracker.get_summary()
    assert summary.total == 3
    assert summary.pending == 0
    assert summary.processing == 0
    assert summary.completed == 2
    assert summary.failed == 1
    assert summary.success_rate == pytest.approx(66.67, rel=0.1)
    assert summary.is_complete


def test_queue_priority_with_status():
    """Test that priority queue works with status tracking."""
    queue = ImageQueue()
    tracker = StatusTracker()
    
    # Add images with different priorities
    high_priority = ImageQueueItem(
        id="urgent",
        input_path="/input/urgent.png",
        output_path="/output/urgent.png",
        priority=10
    )
    
    normal_priority = ImageQueueItem(
        id="normal",
        input_path="/input/normal.png",
        output_path="/output/normal.png",
        priority=0
    )
    
    # Enqueue in reverse priority order
    queue.enqueue(normal_priority)
    queue.enqueue(high_priority)
    
    # Track both
    tracker.add_image(normal_priority.id)
    tracker.add_image(high_priority.id)
    
    # High priority should be dequeued first
    item = queue.dequeue()
    assert item.id == "urgent"
    
    tracker.update_status(item.id, ProcessingState.PROCESSING.value)
    
    # Verify status
    status = tracker.get_status("urgent")
    assert status.state == ProcessingState.PROCESSING.value
    
    status = tracker.get_status("normal")
    assert status.state == ProcessingState.PENDING.value


def test_batch_workflow_simulation():
    """Simulate a complete batch processing workflow."""
    queue = ImageQueue()
    tracker = StatusTracker()
    
    # Simulate adding a batch of 5 images
    batch_size = 5
    for i in range(1, batch_size + 1):
        item = ImageQueueItem(
            id=f"img_{i:03d}",
            input_path=f"/input/page_{i:03d}.png",
            output_path=f"/output/page_{i:03d}.png"
        )
        queue.enqueue(item)
        tracker.add_image(item.id)
    
    # Verify initial state
    assert queue.size() == batch_size
    assert len(tracker) == batch_size
    
    summary = tracker.get_summary()
    assert summary.total == batch_size
    assert summary.pending == batch_size
    assert summary.start_time is not None
    
    # Process all images
    processed = 0
    while queue.size() > 0:
        item = queue.dequeue()
        
        # Start processing
        tracker.update_status(item.id, ProcessingState.PROCESSING.value)
        
        # Simulate success or failure
        if processed == 2:  # Fail the third image
            tracker.update_status(
                item.id,
                ProcessingState.FAILED.value,
                error_message="Simulated error"
            )
        else:
            tracker.update_status(
                item.id,
                ProcessingState.COMPLETED.value,
                output_path=item.output_path
            )
        
        processed += 1
    
    # Verify final state
    assert queue.size() == 0
    
    summary = tracker.get_summary()
    assert summary.total == batch_size
    assert summary.pending == 0
    assert summary.processing == 0
    assert summary.completed == batch_size - 1
    assert summary.failed == 1
    assert summary.is_complete
    assert summary.end_time is not None
    assert summary.elapsed_time is not None
    
    # Verify we can query by state
    completed_images = tracker.get_images_by_state(ProcessingState.COMPLETED.value)
    failed_images = tracker.get_images_by_state(ProcessingState.FAILED.value)
    
    assert len(completed_images) == batch_size - 1
    assert len(failed_images) == 1
    assert "img_003" in failed_images  # The third image failed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Tests for the batch processing queue system.

This module contains unit tests for the ImageQueue and ImageQueueItem classes.
"""

import pytest
from batch_processing.core.queue import ImageQueue, ImageQueueItem


class TestImageQueueItem:
    """Tests for the ImageQueueItem dataclass."""
    
    def test_basic_creation(self):
        """Test creating a basic ImageQueueItem."""
        item = ImageQueueItem(
            id="img_001",
            input_path="/path/to/input.png",
            output_path="/path/to/output.png"
        )
        
        assert item.id == "img_001"
        assert item.input_path == "/path/to/input.png"
        assert item.output_path == "/path/to/output.png"
        assert item.config is None
        assert item.priority == 0
        assert item.image_type is None
        assert item.classification_confidence is None
    
    def test_creation_with_all_fields(self):
        """Test creating an ImageQueueItem with all fields."""
        config = {"seed": 42, "steps": 10}
        item = ImageQueueItem(
            id="img_002",
            input_path="/path/to/input2.png",
            output_path="/path/to/output2.png",
            config=config,
            priority=5,
            image_type="line_art",
            classification_confidence=0.95
        )
        
        assert item.id == "img_002"
        assert item.input_path == "/path/to/input2.png"
        assert item.output_path == "/path/to/output2.png"
        assert item.config == config
        assert item.priority == 5
        assert item.image_type == "line_art"
        assert item.classification_confidence == 0.95
    
    def test_invalid_image_type(self):
        """Test that invalid image_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid image_type"):
            ImageQueueItem(
                id="img_003",
                input_path="/path/to/input.png",
                output_path="/path/to/output.png",
                image_type="invalid_type"
            )
    
    def test_valid_image_types(self):
        """Test that valid image types are accepted."""
        line_art = ImageQueueItem(
            id="img_004",
            input_path="/path/to/input.png",
            output_path="/path/to/output.png",
            image_type="line_art"
        )
        assert line_art.image_type == "line_art"
        
        colored = ImageQueueItem(
            id="img_005",
            input_path="/path/to/input.png",
            output_path="/path/to/output.png",
            image_type="colored"
        )
        assert colored.image_type == "colored"
    
    def test_invalid_confidence_too_high(self):
        """Test that confidence > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="classification_confidence must be between 0 and 1"):
            ImageQueueItem(
                id="img_006",
                input_path="/path/to/input.png",
                output_path="/path/to/output.png",
                classification_confidence=1.5
            )
    
    def test_invalid_confidence_negative(self):
        """Test that negative confidence raises ValueError."""
        with pytest.raises(ValueError, match="classification_confidence must be between 0 and 1"):
            ImageQueueItem(
                id="img_007",
                input_path="/path/to/input.png",
                output_path="/path/to/output.png",
                classification_confidence=-0.1
            )
    
    def test_valid_confidence_boundaries(self):
        """Test that confidence at boundaries (0.0 and 1.0) is valid."""
        item_zero = ImageQueueItem(
            id="img_008",
            input_path="/path/to/input.png",
            output_path="/path/to/output.png",
            classification_confidence=0.0
        )
        assert item_zero.classification_confidence == 0.0
        
        item_one = ImageQueueItem(
            id="img_009",
            input_path="/path/to/input.png",
            output_path="/path/to/output.png",
            classification_confidence=1.0
        )
        assert item_one.classification_confidence == 1.0


class TestImageQueue:
    """Tests for the ImageQueue class."""
    
    def test_empty_queue_initialization(self):
        """Test that a new queue is empty."""
        queue = ImageQueue()
        assert queue.size() == 0
        assert len(queue) == 0
        assert not queue  # Should be falsy when empty
    
    def test_enqueue_single_item(self):
        """Test enqueueing a single item."""
        queue = ImageQueue()
        item = ImageQueueItem(
            id="img_001",
            input_path="/path/to/input.png",
            output_path="/path/to/output.png"
        )
        
        queue.enqueue(item)
        assert queue.size() == 1
        assert len(queue) == 1
        assert queue  # Should be truthy when not empty
    
    def test_enqueue_multiple_items(self):
        """Test enqueueing multiple items."""
        queue = ImageQueue()
        
        for i in range(5):
            item = ImageQueueItem(
                id=f"img_{i:03d}",
                input_path=f"/path/to/input{i}.png",
                output_path=f"/path/to/output{i}.png"
            )
            queue.enqueue(item)
        
        assert queue.size() == 5
    
    def test_enqueue_invalid_type(self):
        """Test that enqueueing non-ImageQueueItem raises TypeError."""
        queue = ImageQueue()
        
        with pytest.raises(TypeError, match="Expected ImageQueueItem"):
            queue.enqueue("not an ImageQueueItem")
    
    def test_dequeue_from_empty_queue(self):
        """Test that dequeueing from empty queue returns None."""
        queue = ImageQueue()
        assert queue.dequeue() is None
    
    def test_dequeue_single_item(self):
        """Test dequeueing a single item."""
        queue = ImageQueue()
        item = ImageQueueItem(
            id="img_001",
            input_path="/path/to/input.png",
            output_path="/path/to/output.png"
        )
        
        queue.enqueue(item)
        dequeued = queue.dequeue()
        
        assert dequeued is not None
        assert dequeued.id == "img_001"
        assert queue.size() == 0
    
    def test_dequeue_fifo_order(self):
        """Test that items are dequeued in FIFO order (same priority)."""
        queue = ImageQueue()
        
        # Enqueue items with same priority
        for i in range(3):
            item = ImageQueueItem(
                id=f"img_{i:03d}",
                input_path=f"/path/to/input{i}.png",
                output_path=f"/path/to/output{i}.png",
                priority=0
            )
            queue.enqueue(item)
        
        # Dequeue and verify FIFO order
        first = queue.dequeue()
        assert first.id == "img_000"
        
        second = queue.dequeue()
        assert second.id == "img_001"
        
        third = queue.dequeue()
        assert third.id == "img_002"
        
        assert queue.size() == 0
    
    def test_priority_ordering(self):
        """Test that higher priority items are dequeued first."""
        queue = ImageQueue()
        
        # Enqueue items with different priorities
        low_priority = ImageQueueItem(
            id="low",
            input_path="/path/to/low.png",
            output_path="/path/to/low_out.png",
            priority=1
        )
        
        high_priority = ImageQueueItem(
            id="high",
            input_path="/path/to/high.png",
            output_path="/path/to/high_out.png",
            priority=10
        )
        
        medium_priority = ImageQueueItem(
            id="medium",
            input_path="/path/to/medium.png",
            output_path="/path/to/medium_out.png",
            priority=5
        )
        
        # Enqueue in non-priority order
        queue.enqueue(low_priority)
        queue.enqueue(high_priority)
        queue.enqueue(medium_priority)
        
        # Dequeue and verify priority order
        first = queue.dequeue()
        assert first.id == "high"
        
        second = queue.dequeue()
        assert second.id == "medium"
        
        third = queue.dequeue()
        assert third.id == "low"
    
    def test_priority_with_fifo_within_same_priority(self):
        """Test that FIFO is maintained within same priority level."""
        queue = ImageQueue()
        
        # Enqueue multiple items with same priority
        for i in range(3):
            item = ImageQueueItem(
                id=f"priority5_{i}",
                input_path=f"/path/to/input{i}.png",
                output_path=f"/path/to/output{i}.png",
                priority=5
            )
            queue.enqueue(item)
        
        # Add a higher priority item
        high = ImageQueueItem(
            id="priority10",
            input_path="/path/to/high.png",
            output_path="/path/to/high_out.png",
            priority=10
        )
        queue.enqueue(high)
        
        # High priority should come first
        assert queue.dequeue().id == "priority10"
        
        # Then FIFO within priority 5
        assert queue.dequeue().id == "priority5_0"
        assert queue.dequeue().id == "priority5_1"
        assert queue.dequeue().id == "priority5_2"
    
    def test_peek_empty_queue(self):
        """Test that peeking at empty queue returns None."""
        queue = ImageQueue()
        assert queue.peek() is None
    
    def test_peek_does_not_remove(self):
        """Test that peek does not remove the item."""
        queue = ImageQueue()
        item = ImageQueueItem(
            id="img_001",
            input_path="/path/to/input.png",
            output_path="/path/to/output.png"
        )
        
        queue.enqueue(item)
        
        # Peek multiple times
        peeked1 = queue.peek()
        peeked2 = queue.peek()
        
        assert peeked1 is not None
        assert peeked2 is not None
        assert peeked1.id == "img_001"
        assert peeked2.id == "img_001"
        assert queue.size() == 1  # Size unchanged
    
    def test_peek_returns_highest_priority(self):
        """Test that peek returns the highest priority item."""
        queue = ImageQueue()
        
        low = ImageQueueItem(
            id="low",
            input_path="/path/to/low.png",
            output_path="/path/to/low_out.png",
            priority=1
        )
        
        high = ImageQueueItem(
            id="high",
            input_path="/path/to/high.png",
            output_path="/path/to/high_out.png",
            priority=10
        )
        
        queue.enqueue(low)
        queue.enqueue(high)
        
        peeked = queue.peek()
        assert peeked.id == "high"
        assert queue.size() == 2  # Both items still in queue
    
    def test_clear_empty_queue(self):
        """Test clearing an empty queue."""
        queue = ImageQueue()
        queue.clear()
        assert queue.size() == 0
    
    def test_clear_non_empty_queue(self):
        """Test clearing a non-empty queue."""
        queue = ImageQueue()
        
        for i in range(5):
            item = ImageQueueItem(
                id=f"img_{i:03d}",
                input_path=f"/path/to/input{i}.png",
                output_path=f"/path/to/output{i}.png"
            )
            queue.enqueue(item)
        
        assert queue.size() == 5
        queue.clear()
        assert queue.size() == 0
        assert queue.dequeue() is None
    
    def test_iteration(self):
        """Test iterating over queue items."""
        queue = ImageQueue()
        
        ids = ["img_001", "img_002", "img_003"]
        for img_id in ids:
            item = ImageQueueItem(
                id=img_id,
                input_path=f"/path/to/{img_id}.png",
                output_path=f"/path/to/{img_id}_out.png"
            )
            queue.enqueue(item)
        
        # Iterate and collect IDs
        collected_ids = [item.id for item in queue]
        assert collected_ids == ids
    
    def test_iteration_respects_priority_order(self):
        """Test that iteration shows items in priority order."""
        queue = ImageQueue()
        
        # Add items in non-priority order
        priorities = [(1, "low"), (10, "high"), (5, "medium")]
        for priority, name in priorities:
            item = ImageQueueItem(
                id=name,
                input_path=f"/path/to/{name}.png",
                output_path=f"/path/to/{name}_out.png",
                priority=priority
            )
            queue.enqueue(item)
        
        # Iteration should show priority order
        ids = [item.id for item in queue]
        assert ids == ["high", "medium", "low"]
    
    def test_bool_evaluation(self):
        """Test boolean evaluation of queue."""
        queue = ImageQueue()
        
        # Empty queue is falsy
        assert not queue
        assert bool(queue) is False
        
        # Non-empty queue is truthy
        item = ImageQueueItem(
            id="img_001",
            input_path="/path/to/input.png",
            output_path="/path/to/output.png"
        )
        queue.enqueue(item)
        
        assert queue
        assert bool(queue) is True
        
        # After dequeue, empty again
        queue.dequeue()
        assert not queue


class TestQueueIntegration:
    """Integration tests for queue operations."""
    
    def test_enqueue_dequeue_cycle(self):
        """Test multiple enqueue/dequeue cycles."""
        queue = ImageQueue()
        
        # First batch
        for i in range(3):
            item = ImageQueueItem(
                id=f"batch1_{i}",
                input_path=f"/path/to/input{i}.png",
                output_path=f"/path/to/output{i}.png"
            )
            queue.enqueue(item)
        
        # Dequeue one
        first = queue.dequeue()
        assert first.id == "batch1_0"
        assert queue.size() == 2
        
        # Add more
        for i in range(2):
            item = ImageQueueItem(
                id=f"batch2_{i}",
                input_path=f"/path/to/input{i}.png",
                output_path=f"/path/to/output{i}.png"
            )
            queue.enqueue(item)
        
        assert queue.size() == 4
        
        # Dequeue all
        ids = []
        while queue.size() > 0:
            item = queue.dequeue()
            ids.append(item.id)
        
        assert ids == ["batch1_1", "batch1_2", "batch2_0", "batch2_1"]
        assert queue.size() == 0
    
    def test_complex_priority_scenario(self):
        """Test complex priority ordering scenario."""
        queue = ImageQueue()
        
        # Add items with various priorities
        items_data = [
            ("img1", 0),
            ("img2", 5),
            ("img3", 0),
            ("img4", 10),
            ("img5", 5),
            ("img6", 0),
        ]
        
        for img_id, priority in items_data:
            item = ImageQueueItem(
                id=img_id,
                input_path=f"/path/to/{img_id}.png",
                output_path=f"/path/to/{img_id}_out.png",
                priority=priority
            )
            queue.enqueue(item)
        
        # Expected order: priority 10, then priority 5 (FIFO), then priority 0 (FIFO)
        expected_order = ["img4", "img2", "img5", "img1", "img3", "img6"]
        
        actual_order = []
        while queue.size() > 0:
            item = queue.dequeue()
            actual_order.append(item.id)
        
        assert actual_order == expected_order


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Tests for the status tracking system.

This module tests the StatusTracker and ProcessingStatus classes to ensure
they correctly track and report processing status for batch operations.
"""

import pytest
import time
from batch_processing.core.status import (
    StatusTracker,
    ProcessingStatus,
    ProcessingState,
    StatusSummary
)


class TestProcessingStatus:
    """Tests for the ProcessingStatus dataclass."""
    
    def test_create_pending_status(self):
        """Test creating a status in pending state."""
        status = ProcessingStatus(
            id="img_001",
            state=ProcessingState.PENDING.value
        )
        
        assert status.id == "img_001"
        assert status.state == ProcessingState.PENDING.value
        assert status.start_time is None
        assert status.end_time is None
        assert status.error_message is None
        assert status.output_path is None
    
    def test_create_completed_status(self):
        """Test creating a status in completed state."""
        start = time.time()
        end = start + 10.5
        
        status = ProcessingStatus(
            id="img_002",
            state=ProcessingState.COMPLETED.value,
            start_time=start,
            end_time=end,
            output_path="/output/img_002.png"
        )
        
        assert status.id == "img_002"
        assert status.state == ProcessingState.COMPLETED.value
        assert status.start_time == start
        assert status.end_time == end
        assert status.output_path == "/output/img_002.png"
    
    def test_create_failed_status(self):
        """Test creating a status in failed state."""
        status = ProcessingStatus(
            id="img_003",
            state=ProcessingState.FAILED.value,
            error_message="Out of memory"
        )
        
        assert status.id == "img_003"
        assert status.state == ProcessingState.FAILED.value
        assert status.error_message == "Out of memory"
    
    def test_invalid_state_raises_error(self):
        """Test that invalid state raises ValueError."""
        with pytest.raises(ValueError, match="Invalid state"):
            ProcessingStatus(
                id="img_004",
                state="invalid_state"
            )
    
    def test_processing_time_calculation(self):
        """Test processing time calculation."""
        start = time.time()
        end = start + 15.7
        
        status = ProcessingStatus(
            id="img_005",
            state=ProcessingState.COMPLETED.value,
            start_time=start,
            end_time=end
        )
        
        assert abs(status.processing_time - 15.7) < 0.01
    
    def test_processing_time_none_when_not_started(self):
        """Test processing time is None when not started."""
        status = ProcessingStatus(
            id="img_006",
            state=ProcessingState.PENDING.value
        )
        
        assert status.processing_time is None
    
    def test_processing_time_elapsed_when_ongoing(self):
        """Test processing time returns elapsed time when ongoing."""
        start = time.time()
        
        status = ProcessingStatus(
            id="img_007",
            state=ProcessingState.PROCESSING.value,
            start_time=start
        )
        
        time.sleep(0.1)
        elapsed = status.processing_time
        
        assert elapsed is not None
        assert elapsed >= 0.1
    
    def test_is_terminal_state(self):
        """Test terminal state detection."""
        completed = ProcessingStatus(id="1", state=ProcessingState.COMPLETED.value)
        failed = ProcessingStatus(id="2", state=ProcessingState.FAILED.value)
        cancelled = ProcessingStatus(id="3", state=ProcessingState.CANCELLED.value)
        pending = ProcessingStatus(id="4", state=ProcessingState.PENDING.value)
        processing = ProcessingStatus(id="5", state=ProcessingState.PROCESSING.value)
        
        assert completed.is_terminal_state()
        assert failed.is_terminal_state()
        assert cancelled.is_terminal_state()
        assert not pending.is_terminal_state()
        assert not processing.is_terminal_state()


class TestStatusSummary:
    """Tests for the StatusSummary dataclass."""
    
    def test_create_summary(self):
        """Test creating a status summary."""
        summary = StatusSummary(
            total=10,
            pending=3,
            processing=1,
            completed=5,
            failed=1,
            cancelled=0
        )
        
        assert summary.total == 10
        assert summary.pending == 3
        assert summary.processing == 1
        assert summary.completed == 5
        assert summary.failed == 1
        assert summary.cancelled == 0
    
    def test_is_complete_true(self):
        """Test is_complete when all images are in terminal state."""
        summary = StatusSummary(
            total=10,
            completed=8,
            failed=1,
            cancelled=1
        )
        
        assert summary.is_complete
    
    def test_is_complete_false(self):
        """Test is_complete when images are still processing."""
        summary = StatusSummary(
            total=10,
            pending=2,
            processing=1,
            completed=7
        )
        
        assert not summary.is_complete
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        summary = StatusSummary(
            total=10,
            completed=8,
            failed=2
        )
        
        assert summary.success_rate == 80.0
    
    def test_success_rate_zero_total(self):
        """Test success rate with zero total."""
        summary = StatusSummary(total=0)
        assert summary.success_rate == 0.0
    
    def test_elapsed_time_calculation(self):
        """Test elapsed time calculation."""
        start = time.time()
        end = start + 30.5
        
        summary = StatusSummary(
            total=5,
            start_time=start,
            end_time=end
        )
        
        assert abs(summary.elapsed_time - 30.5) < 0.01
    
    def test_elapsed_time_ongoing(self):
        """Test elapsed time when batch is ongoing."""
        start = time.time()
        
        summary = StatusSummary(
            total=5,
            start_time=start
        )
        
        time.sleep(0.1)
        elapsed = summary.elapsed_time
        
        assert elapsed is not None
        assert elapsed >= 0.1


class TestStatusTracker:
    """Tests for the StatusTracker class."""
    
    def test_create_empty_tracker(self):
        """Test creating an empty status tracker."""
        tracker = StatusTracker()
        
        assert len(tracker) == 0
        assert tracker.get_all_statuses() == {}
    
    def test_add_image(self):
        """Test adding an image to track."""
        tracker = StatusTracker()
        tracker.add_image("img_001")
        
        assert len(tracker) == 1
        assert "img_001" in tracker
        
        status = tracker.get_status("img_001")
        assert status.id == "img_001"
        assert status.state == ProcessingState.PENDING.value
    
    def test_add_multiple_images(self):
        """Test adding multiple images."""
        tracker = StatusTracker()
        tracker.add_image("img_001")
        tracker.add_image("img_002")
        tracker.add_image("img_003")
        
        assert len(tracker) == 3
        assert "img_001" in tracker
        assert "img_002" in tracker
        assert "img_003" in tracker
    
    def test_add_duplicate_image_raises_error(self):
        """Test that adding duplicate image raises error."""
        tracker = StatusTracker()
        tracker.add_image("img_001")
        
        with pytest.raises(ValueError, match="already being tracked"):
            tracker.add_image("img_001")
    
    def test_update_status_to_processing(self):
        """Test updating status to processing."""
        tracker = StatusTracker()
        tracker.add_image("img_001")
        
        tracker.update_status("img_001", ProcessingState.PROCESSING.value)
        
        status = tracker.get_status("img_001")
        assert status.state == ProcessingState.PROCESSING.value
        assert status.start_time is not None
    
    def test_update_status_to_completed(self):
        """Test updating status to completed."""
        tracker = StatusTracker()
        tracker.add_image("img_001")
        tracker.update_status("img_001", ProcessingState.PROCESSING.value)
        
        tracker.update_status(
            "img_001",
            ProcessingState.COMPLETED.value,
            output_path="/output/img_001.png"
        )
        
        status = tracker.get_status("img_001")
        assert status.state == ProcessingState.COMPLETED.value
        assert status.end_time is not None
        assert status.output_path == "/output/img_001.png"
    
    def test_update_status_to_failed(self):
        """Test updating status to failed."""
        tracker = StatusTracker()
        tracker.add_image("img_001")
        tracker.update_status("img_001", ProcessingState.PROCESSING.value)
        
        tracker.update_status(
            "img_001",
            ProcessingState.FAILED.value,
            error_message="GPU out of memory"
        )
        
        status = tracker.get_status("img_001")
        assert status.state == ProcessingState.FAILED.value
        assert status.end_time is not None
        assert status.error_message == "GPU out of memory"
    
    def test_update_status_invalid_image_raises_error(self):
        """Test updating status for non-existent image raises error."""
        tracker = StatusTracker()
        
        with pytest.raises(KeyError, match="not being tracked"):
            tracker.update_status("img_999", ProcessingState.PROCESSING.value)
    
    def test_update_status_invalid_state_raises_error(self):
        """Test updating to invalid state raises error."""
        tracker = StatusTracker()
        tracker.add_image("img_001")
        
        with pytest.raises(ValueError, match="Invalid state"):
            tracker.update_status("img_001", "invalid_state")
    
    def test_get_status(self):
        """Test getting status for a specific image."""
        tracker = StatusTracker()
        tracker.add_image("img_001")
        
        status = tracker.get_status("img_001")
        assert status.id == "img_001"
        assert status.state == ProcessingState.PENDING.value
    
    def test_get_status_nonexistent_raises_error(self):
        """Test getting status for non-existent image raises error."""
        tracker = StatusTracker()
        
        with pytest.raises(KeyError, match="not being tracked"):
            tracker.get_status("img_999")
    
    def test_get_all_statuses(self):
        """Test getting all statuses."""
        tracker = StatusTracker()
        tracker.add_image("img_001")
        tracker.add_image("img_002")
        tracker.add_image("img_003")
        
        all_statuses = tracker.get_all_statuses()
        
        assert len(all_statuses) == 3
        assert "img_001" in all_statuses
        assert "img_002" in all_statuses
        assert "img_003" in all_statuses
    
    def test_get_summary(self):
        """Test getting status summary."""
        tracker = StatusTracker()
        tracker.add_image("img_001")
        tracker.add_image("img_002")
        tracker.add_image("img_003")
        tracker.add_image("img_004")
        tracker.add_image("img_005")
        
        # Update some statuses
        tracker.update_status("img_001", ProcessingState.PROCESSING.value)
        tracker.update_status("img_002", ProcessingState.COMPLETED.value, output_path="/out/img_002.png")
        tracker.update_status("img_003", ProcessingState.COMPLETED.value, output_path="/out/img_003.png")
        tracker.update_status("img_004", ProcessingState.FAILED.value, error_message="Error")
        
        summary = tracker.get_summary()
        
        assert summary.total == 5
        assert summary.pending == 1
        assert summary.processing == 1
        assert summary.completed == 2
        assert summary.failed == 1
        assert summary.cancelled == 0
    
    def test_get_images_by_state(self):
        """Test getting images by state."""
        tracker = StatusTracker()
        tracker.add_image("img_001")
        tracker.add_image("img_002")
        tracker.add_image("img_003")
        tracker.add_image("img_004")
        
        tracker.update_status("img_001", ProcessingState.COMPLETED.value)
        tracker.update_status("img_002", ProcessingState.COMPLETED.value)
        tracker.update_status("img_003", ProcessingState.FAILED.value)
        
        completed = tracker.get_images_by_state(ProcessingState.COMPLETED.value)
        failed = tracker.get_images_by_state(ProcessingState.FAILED.value)
        pending = tracker.get_images_by_state(ProcessingState.PENDING.value)
        
        assert set(completed) == {"img_001", "img_002"}
        assert set(failed) == {"img_003"}
        assert set(pending) == {"img_004"}
    
    def test_clear(self):
        """Test clearing all statuses."""
        tracker = StatusTracker()
        tracker.add_image("img_001")
        tracker.add_image("img_002")
        
        assert len(tracker) == 2
        
        tracker.clear()
        
        assert len(tracker) == 0
        assert tracker.get_all_statuses() == {}
    
    def test_batch_start_time_set_on_first_image(self):
        """Test that batch start time is set when first image is added."""
        tracker = StatusTracker()
        
        summary = tracker.get_summary()
        assert summary.start_time is None
        
        tracker.add_image("img_001")
        
        summary = tracker.get_summary()
        assert summary.start_time is not None
    
    def test_batch_end_time_set_when_complete(self):
        """Test that batch end time is set when all images complete."""
        tracker = StatusTracker()
        tracker.add_image("img_001")
        tracker.add_image("img_002")
        
        summary = tracker.get_summary()
        assert summary.end_time is None
        
        tracker.update_status("img_001", ProcessingState.COMPLETED.value)
        summary = tracker.get_summary()
        assert summary.end_time is None  # Not complete yet
        
        tracker.update_status("img_002", ProcessingState.COMPLETED.value)
        summary = tracker.get_summary()
        assert summary.end_time is not None  # Now complete
    
    def test_status_transitions_with_timestamps(self):
        """Test complete status transition workflow with timestamps."""
        tracker = StatusTracker()
        tracker.add_image("img_001")
        
        # Initially pending
        status = tracker.get_status("img_001")
        assert status.state == ProcessingState.PENDING.value
        assert status.start_time is None
        assert status.end_time is None
        
        # Transition to processing
        tracker.update_status("img_001", ProcessingState.PROCESSING.value)
        status = tracker.get_status("img_001")
        assert status.state == ProcessingState.PROCESSING.value
        assert status.start_time is not None
        assert status.end_time is None
        
        start_time = status.start_time
        
        # Small delay to ensure different timestamps
        time.sleep(0.01)
        
        # Transition to completed
        tracker.update_status("img_001", ProcessingState.COMPLETED.value, output_path="/out/img_001.png")
        status = tracker.get_status("img_001")
        assert status.state == ProcessingState.COMPLETED.value
        assert status.start_time == start_time
        assert status.end_time is not None
        assert status.end_time > start_time
        assert status.output_path == "/out/img_001.png"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

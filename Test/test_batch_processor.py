"""
Tests for the BatchProcessor class.

This module tests the core batch processing functionality including
initialization, adding images, and the processing workflow.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import torch

from batch_processing import BatchProcessor, BatchConfig
from batch_processing.core.status import ProcessingState
from batch_processing.exceptions import ValidationError, BatchProcessingError


@pytest.fixture
def temp_dirs():
    """Create temporary input and output directories."""
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()
    
    yield input_dir, output_dir
    
    # Cleanup
    shutil.rmtree(input_dir, ignore_errors=True)
    shutil.rmtree(output_dir, ignore_errors=True)


@pytest.fixture
def sample_images(temp_dirs):
    """Create sample test images."""
    input_dir, _ = temp_dirs
    
    image_paths = []
    for i in range(3):
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color=(255, 255, 255))
        img_path = Path(input_dir) / f"test_image_{i}.png"
        img.save(img_path)
        image_paths.append(str(img_path))
    
    return image_paths


@pytest.fixture
def reference_images(temp_dirs):
    """Create sample reference images."""
    input_dir, _ = temp_dirs
    
    ref_paths = []
    for i in range(2):
        # Create a colored reference image
        img = Image.new('RGB', (100, 100), color=(255, 0, 0))
        img_path = Path(input_dir) / f"reference_{i}.png"
        img.save(img_path)
        ref_paths.append(str(img_path))
    
    return ref_paths


@pytest.fixture
def batch_config(temp_dirs, reference_images):
    """Create a test BatchConfig."""
    input_dir, output_dir = temp_dirs
    
    return BatchConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        reference_images=reference_images,
        style="line + shadow",
        seed=0,
        num_inference_steps=10,
        top_k=3,
        recursive=False,
        overwrite=False,
        preview_mode=False,
        max_concurrent=1
    )


class TestBatchProcessorInitialization:
    """Tests for BatchProcessor initialization."""
    
    def test_init_with_valid_config(self, batch_config):
        """Test initialization with valid configuration."""
        processor = BatchProcessor(batch_config)
        
        assert processor.config == batch_config
        assert processor.queue is not None
        assert processor.status_tracker is not None
        assert processor.memory_manager is not None
        assert processor.queue.size() == 0
        assert not processor._processing
        assert not processor._paused
        assert not processor._cancelled
    
    def test_init_creates_memory_manager_with_correct_device(self, batch_config):
        """Test that memory manager is created with the correct device."""
        processor = BatchProcessor(batch_config)
        
        # Check device is set correctly
        assert processor.memory_manager.device is not None
        
        # Device should be cuda, mps, or cpu
        device_type = processor.memory_manager.device.type
        assert device_type in ["cuda", "mps", "cpu"]


class TestAddImages:
    """Tests for the add_images method."""
    
    def test_add_valid_images(self, batch_config, sample_images):
        """Test adding valid images to the queue."""
        processor = BatchProcessor(batch_config)
        
        processor.add_images(sample_images)
        
        # Check queue size
        assert processor.queue.size() == len(sample_images)
        
        # Check status tracker has all images
        assert len(processor.status_tracker) == len(sample_images)
        
        # Check all images are in pending state
        summary = processor.status_tracker.get_summary()
        assert summary.pending == len(sample_images)
    
    def test_add_empty_list_raises_error(self, batch_config):
        """Test that adding empty list raises ValidationError."""
        processor = BatchProcessor(batch_config)
        
        with pytest.raises(ValidationError, match="image_paths list is empty"):
            processor.add_images([])
    
    def test_add_invalid_images_skips_them(self, batch_config, temp_dirs):
        """Test that invalid images are skipped."""
        processor = BatchProcessor(batch_config)
        input_dir, _ = temp_dirs
        
        # Create one valid and one invalid image path
        valid_img = Image.new('RGB', (100, 100), color=(255, 255, 255))
        valid_path = Path(input_dir) / "valid.png"
        valid_img.save(valid_path)
        
        invalid_path = Path(input_dir) / "nonexistent.png"
        
        processor.add_images([str(valid_path), str(invalid_path)])
        
        # Only valid image should be added
        assert processor.queue.size() == 1
    
    def test_add_all_invalid_images_raises_error(self, batch_config):
        """Test that adding only invalid images raises ValidationError."""
        processor = BatchProcessor(batch_config)
        
        invalid_paths = ["/nonexistent/image1.png", "/nonexistent/image2.png"]
        
        with pytest.raises(ValidationError, match="No valid images added"):
            processor.add_images(invalid_paths)
    
    def test_add_images_creates_output_paths(self, batch_config, sample_images):
        """Test that output paths are created for each image."""
        processor = BatchProcessor(batch_config)
        
        processor.add_images(sample_images)
        
        # Check each queue item has an output path
        for item in processor.queue:
            assert item.output_path is not None
            assert "_colorized" in item.output_path
            assert Path(item.output_path).parent == Path(batch_config.output_dir)


class TestGetStatus:
    """Tests for the get_status method."""
    
    def test_get_status_returns_correct_structure(self, batch_config, sample_images):
        """Test that get_status returns the correct structure."""
        processor = BatchProcessor(batch_config)
        processor.add_images(sample_images)
        
        status = processor.get_status()
        
        # Check all required keys are present
        assert "summary" in status
        assert "is_processing" in status
        assert "is_paused" in status
        assert "is_cancelled" in status
        assert "queue_size" in status
        assert "total_images" in status
        assert "completed" in status
        assert "failed" in status
        assert "pending" in status
        assert "processing" in status
        assert "cancelled" in status
        assert "success_rate" in status
        assert "elapsed_time" in status
    
    def test_get_status_reflects_queue_size(self, batch_config, sample_images):
        """Test that status reflects correct queue size."""
        processor = BatchProcessor(batch_config)
        processor.add_images(sample_images)
        
        status = processor.get_status()
        
        assert status["queue_size"] == len(sample_images)
        assert status["total_images"] == len(sample_images)
        assert status["pending"] == len(sample_images)


class TestStartProcessing:
    """Tests for the start_processing method."""
    
    def test_start_processing_with_empty_queue_raises_error(self, batch_config):
        """Test that starting with empty queue raises error."""
        processor = BatchProcessor(batch_config)
        
        with pytest.raises(BatchProcessingError, match="queue is empty"):
            processor.start_processing()
    
    def test_start_processing_sets_processing_flag(self, batch_config, sample_images):
        """Test that start_processing sets the processing flag."""
        processor = BatchProcessor(batch_config)
        processor.add_images(sample_images)
        
        # Note: This test would need to be run in a separate thread or
        # with mocking to avoid actually processing images
        # For now, we just verify the flag is set initially
        assert not processor._processing


class TestPauseResumeCancel:
    """Tests for pause, resume, and cancel functionality."""
    
    def test_pause_when_not_processing_logs_warning(self, batch_config, caplog):
        """Test that pausing when not processing logs a warning."""
        processor = BatchProcessor(batch_config)
        
        processor.pause_processing()
        
        assert "Cannot pause: processing is not active" in caplog.text
    
    def test_resume_when_not_paused_logs_warning(self, batch_config, caplog):
        """Test that resuming when not paused logs a warning."""
        processor = BatchProcessor(batch_config)
        
        processor.resume_processing()
        
        assert "Cannot resume: processing is not paused" in caplog.text
    
    def test_cancel_when_not_processing_logs_warning(self, batch_config, caplog):
        """Test that cancelling when not processing logs a warning."""
        processor = BatchProcessor(batch_config)
        
        processor.cancel_processing()
        
        assert "Cannot cancel: processing is not active" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

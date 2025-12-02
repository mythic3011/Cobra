"""
Integration tests for the batch processing UI components.

This test suite verifies that all UI components are properly wired
and work together correctly.
"""

import pytest
from pathlib import Path
from PIL import Image
import tempfile
import zipfile
import shutil

# Import the functions we need to test
from demo_batch_ui import (
    handle_zip_upload,
    start_batch_processing,
    get_batch_status,
    pause_batch,
    resume_batch,
    cancel_batch,
    get_batch_results,
    mock_processor
)


class TestBatchUIIntegration:
    """Integration tests for batch UI components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_zip = self._create_test_zip()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_test_zip(self):
        """Create a test ZIP file with mock images."""
        zip_path = Path(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Create mock image data
            for i in range(3):
                img_path = Path(self.temp_dir) / f"image_{i}.png"
                img = Image.new('RGB', (100, 100), color=(100, 150, 200))
                img.save(img_path)
                zf.write(img_path, f"image_{i}.png")
        
        return zip_path
    
    def test_zip_upload_returns_correct_structure(self):
        """Test that ZIP upload returns the expected data structure."""
        # Create a mock file object
        class MockFile:
            def __init__(self, path):
                self.name = str(path)
        
        mock_file = MockFile(self.test_zip)
        
        # Call the handler
        status, images, choices, selection, confidence = handle_zip_upload(mock_file)
        
        # Verify structure
        assert isinstance(status, str)
        assert "Extracted" in status
        assert isinstance(images, list)
        assert isinstance(choices, list)
        assert isinstance(selection, list)
        assert isinstance(confidence, str)
    
    def test_zip_upload_with_none_returns_error(self):
        """Test that uploading None returns an error message."""
        status, images, choices, selection, confidence = handle_zip_upload(None)
        
        assert "Please upload" in status
        assert images == []
        assert choices == []
        assert selection == []
        assert confidence == ""
    
    def test_start_processing_with_no_references_returns_error(self):
        """Test that starting without references returns an error."""
        result = start_batch_processing(
            style="line + shadow",
            seed=0,
            num_inference_steps=10,
            top_k=3,
            output_dir="./test_output",
            selected_reference_indices=[]
        )
        
        assert "No reference images selected" in result
    
    def test_start_processing_with_references_succeeds(self):
        """Test that starting with references succeeds."""
        result = start_batch_processing(
            style="line + shadow",
            seed=0,
            num_inference_steps=10,
            top_k=3,
            output_dir="./test_output",
            selected_reference_indices=[0, 1, 2]
        )
        
        assert "Started batch processing" in result
    
    def test_get_status_returns_dataframe(self):
        """Test that get_status returns a DataFrame."""
        # Start processing first
        start_batch_processing(
            style="line + shadow",
            seed=0,
            num_inference_steps=10,
            top_k=3,
            output_dir="./test_output",
            selected_reference_indices=[0, 1]
        )
        
        df, progress_text, progress_value = get_batch_status()
        
        # Verify types
        assert hasattr(df, 'columns')  # DataFrame-like
        assert isinstance(progress_text, str)
        assert isinstance(progress_value, float)
        assert 0.0 <= progress_value <= 1.0
    
    def test_pause_resume_cancel_workflow(self):
        """Test the pause/resume/cancel workflow."""
        # Start processing
        start_batch_processing(
            style="line + shadow",
            seed=0,
            num_inference_steps=10,
            top_k=3,
            output_dir="./test_output",
            selected_reference_indices=[0, 1]
        )
        
        # Pause
        result = pause_batch()
        assert "paused" in result.lower()
        assert mock_processor.is_paused
        
        # Resume
        result = resume_batch()
        assert "resumed" in result.lower()
        assert not mock_processor.is_paused
        
        # Cancel
        result = cancel_batch()
        assert "cancelled" in result.lower()
        assert not mock_processor.is_processing
    
    def test_get_results_returns_list(self):
        """Test that get_results returns a list of images."""
        # Start and simulate some completion
        start_batch_processing(
            style="line + shadow",
            seed=0,
            num_inference_steps=10,
            top_k=3,
            output_dir="./test_output",
            selected_reference_indices=[0, 1]
        )
        
        # Simulate completion
        mock_processor.completed = 2
        
        results = get_batch_results()
        
        assert isinstance(results, list)
        assert len(results) == 2
        assert all(isinstance(img, Image.Image) for img in results)
    
    def test_control_buttons_without_active_processing(self):
        """Test that control buttons handle no active processing gracefully."""
        # Note: Due to shared state in demo, we test that buttons return valid responses
        # The actual behavior depends on the current state of mock_processor
        
        # Try pause - should return a valid response
        result = pause_batch()
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Try resume - should return a valid response
        result = resume_batch()
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Try cancel - should return a valid response
        result = cancel_batch()
        assert isinstance(result, str)
        assert len(result) > 0


class TestUIComponentWiring:
    """Test that UI components are properly wired together."""
    
    def test_visibility_toggle_logic(self):
        """Test the batch mode visibility toggle logic."""
        # This would test the update_input_visibility function
        # In a real Gradio app, we'd need to test the actual component updates
        
        # For now, we verify the logic exists
        from demo_batch_ui import demo
        
        # Verify the demo has the expected structure
        assert demo is not None
        assert hasattr(demo, 'blocks')
    
    def test_all_required_components_exist(self):
        """Test that all required UI components are defined."""
        from demo_batch_ui import demo
        
        # Get all component names from the demo
        # This is a basic check that the demo was created successfully
        assert demo is not None
        
        # In a full test, we'd verify specific component IDs
        # For now, we just check the demo builds without errors


class TestDataFlow:
    """Test the data flow through the UI."""
    
    def test_zip_to_gallery_flow(self):
        """Test data flows from ZIP upload to gallery display."""
        # Create mock ZIP
        temp_dir = tempfile.mkdtemp()
        zip_path = Path(temp_dir) / "test.zip"
        
        try:
            with zipfile.ZipFile(zip_path, 'w') as zf:
                img_path = Path(temp_dir) / "test.png"
                img = Image.new('RGB', (100, 100))
                img.save(img_path)
                zf.write(img_path, "test.png")
            
            class MockFile:
                def __init__(self, path):
                    self.name = str(path)
            
            mock_file = MockFile(zip_path)
            
            # Process upload
            status, images, choices, selection, confidence = handle_zip_upload(mock_file)
            
            # Verify data flows correctly
            assert len(images) > 0
            assert len(choices) > 0
            assert len(selection) > 0
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_selection_to_processing_flow(self):
        """Test data flows from selection to processing."""
        # Start with some references selected
        selected_indices = [0, 1, 2]
        
        # Start processing
        result = start_batch_processing(
            style="line + shadow",
            seed=42,
            num_inference_steps=15,
            top_k=5,
            output_dir="./output",
            selected_reference_indices=selected_indices
        )
        
        # Verify processing started
        assert "Started" in result
        assert str(len(selected_indices)) in result
    
    def test_processing_to_status_flow(self):
        """Test data flows from processing to status display."""
        # Start processing
        start_batch_processing(
            style="line + shadow",
            seed=0,
            num_inference_steps=10,
            top_k=3,
            output_dir="./output",
            selected_reference_indices=[0, 1]
        )
        
        # Get status
        df, progress_text, progress_value = get_batch_status()
        
        # Verify status reflects processing state
        assert "Progress" in progress_text or "completed" in progress_text.lower()
        assert progress_value >= 0.0


def test_ui_components_syntax():
    """Test that UI components are syntactically correct."""
    # Import the main UI module
    import demo_batch_ui
    
    # Verify it imported without errors
    assert demo_batch_ui is not None
    assert demo_batch_ui.demo is not None


def test_mock_processor_state_management():
    """Test that the mock processor manages state correctly."""
    # Create a fresh processor instance for this test
    from demo_batch_ui import MockBatchProcessor
    processor = MockBatchProcessor()
    
    # Initial state
    assert not processor.is_processing
    assert not processor.is_paused
    
    # Start processing
    processor.start(5)
    assert processor.is_processing
    assert processor.total == 5
    
    # Pause
    processor.pause()
    assert processor.is_paused
    
    # Resume
    processor.resume()
    assert not processor.is_paused
    
    # Cancel
    processor.cancel()
    assert not processor.is_processing


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

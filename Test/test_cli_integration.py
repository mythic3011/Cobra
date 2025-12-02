"""
Integration test for CLI with batch processor.

This test verifies that the CLI correctly integrates with the
BatchProcessor and can set up processing correctly.
"""

import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from batch_colorize import (
    parse_arguments,
    validate_paths,
    validate_parameters,
    setup_batch_processor
)
from batch_processing.config import BatchConfig
from batch_processing.processor import BatchProcessor


class TestCLIIntegration:
    """Test CLI integration with batch processing system."""
    
    def test_setup_batch_processor_from_args(self):
        """Test that CLI can create a BatchProcessor from arguments."""
        # Create temporary directories
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test directories
            input_dir = temp_path / "input"
            output_dir = temp_path / "output"
            ref_dir = temp_path / "references"
            
            input_dir.mkdir()
            output_dir.mkdir()
            ref_dir.mkdir()
            
            # Copy a test image to input
            test_image = Path("examples/line/example0/input.png")
            if test_image.exists():
                shutil.copy(test_image, input_dir / "test.png")
            
            # Copy reference images
            ref_images = list(Path("examples/shadow/example0").glob("*.png"))
            for ref_img in ref_images[:3]:  # Copy first 3 references
                shutil.copy(ref_img, ref_dir / ref_img.name)
            
            # Mock command-line arguments
            class Args:
                pass
            
            args = Args()
            args.input_dir = str(input_dir)
            args.input_zip = None
            args.output_dir = str(output_dir)
            args.output_zip = None
            args.reference_dir = str(ref_dir)
            args.style = "line + shadow"
            args.seed = 42
            args.steps = 10
            args.top_k = 3
            args.recursive = False
            args.overwrite = False
            args.preview = True
            args.config = None
            args.verbose = False
            args.quiet = False
            
            # Validate paths
            assert validate_paths(args) == True
            
            # Validate parameters
            assert validate_parameters(args) == True
            
            # Setup batch processor
            processor = setup_batch_processor(args)
            
            # Verify processor was created correctly
            assert isinstance(processor, BatchProcessor)
            assert isinstance(processor.config, BatchConfig)
            
            # Verify configuration
            assert processor.config.input_dir == str(input_dir)
            assert processor.config.output_dir == str(output_dir)
            assert processor.config.style == "line + shadow"
            assert processor.config.seed == 42
            assert processor.config.num_inference_steps == 10
            assert processor.config.top_k == 3
            assert processor.config.recursive == False
            assert processor.config.overwrite == False
            assert processor.config.preview_mode == True
            
            # Verify reference images were loaded
            assert len(processor.config.reference_images) > 0
            
            print("✓ CLI successfully integrates with BatchProcessor")
            print(f"✓ Configuration: {processor.config.to_dict()}")
            print(f"✓ Reference images: {len(processor.config.reference_images)}")
    
    def test_zip_input_configuration(self):
        """Test that CLI correctly configures ZIP input."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test directories
            output_dir = temp_path / "output"
            ref_dir = temp_path / "references"
            
            output_dir.mkdir()
            ref_dir.mkdir()
            
            # Copy reference images
            ref_images = list(Path("examples/shadow/example0").glob("*.png"))
            for ref_img in ref_images[:3]:
                shutil.copy(ref_img, ref_dir / ref_img.name)
            
            # Create a dummy ZIP file path (doesn't need to exist for config test)
            zip_path = temp_path / "input.zip"
            zip_path.touch()  # Create empty file
            
            # Mock arguments for ZIP input
            class Args:
                pass
            
            args = Args()
            args.input_dir = None
            args.input_zip = str(zip_path)
            args.output_dir = str(output_dir)
            args.output_zip = None
            args.reference_dir = str(ref_dir)
            args.style = "line"
            args.seed = 0
            args.steps = 5
            args.top_k = 2
            args.recursive = False
            args.overwrite = True
            args.preview = False
            args.config = None
            args.verbose = False
            args.quiet = False
            
            # Setup batch processor
            processor = setup_batch_processor(args)
            
            # Verify ZIP configuration
            assert processor.config.input_is_zip == True
            assert processor.config.output_as_zip == False
            
            print("✓ CLI correctly configures ZIP input")
    
    def test_zip_output_configuration(self):
        """Test that CLI correctly configures ZIP output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test directories
            input_dir = temp_path / "input"
            ref_dir = temp_path / "references"
            
            input_dir.mkdir()
            ref_dir.mkdir()
            
            # Copy a test image
            test_image = Path("examples/line/example0/input.png")
            if test_image.exists():
                shutil.copy(test_image, input_dir / "test.png")
            
            # Copy reference images
            ref_images = list(Path("examples/shadow/example0").glob("*.png"))
            for ref_img in ref_images[:3]:
                shutil.copy(ref_img, ref_dir / ref_img.name)
            
            # Mock arguments for ZIP output
            output_zip = temp_path / "output.zip"
            
            class Args:
                pass
            
            args = Args()
            args.input_dir = str(input_dir)
            args.input_zip = None
            args.output_dir = None
            args.output_zip = str(output_zip)
            args.reference_dir = str(ref_dir)
            args.style = "line + shadow"
            args.seed = 0
            args.steps = 10
            args.top_k = 3
            args.recursive = False
            args.overwrite = False
            args.preview = False
            args.config = None
            args.verbose = False
            args.quiet = False
            
            # Validate paths
            validate_paths(args)
            
            # Setup batch processor
            processor = setup_batch_processor(args)
            
            # Verify ZIP output configuration
            assert processor.config.output_as_zip == True
            assert processor.config.zip_output_name == "output.zip"
            
            print("✓ CLI correctly configures ZIP output")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])

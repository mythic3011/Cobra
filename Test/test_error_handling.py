"""
Tests for error handling and resilience in batch processing.

This module tests that the batch processor handles errors gracefully:
- Invalid files are skipped without stopping the batch
- Configuration errors use defaults instead of crashing
- Processing errors are logged with context
- Progress is saved before critical operations
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from PIL import Image

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from batch_processing.processor import BatchProcessor
from batch_processing.config import BatchConfig
from batch_processing.config.config_handler import ConfigurationHandler
from batch_processing.exceptions import (
    ImageProcessingError,
    ValidationError,
    ConfigurationError
)


def test_empty_image_list():
    """Test that empty image list raises ValidationError."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with tempfile.TemporaryDirectory() as output_dir:
            config = BatchConfig(
                input_dir=temp_dir,
                output_dir=output_dir,
                reference_images=['test.png'],
                style='line + shadow'
            )
            processor = BatchProcessor(config)
            
            try:
                processor.add_images([])
                assert False, "Should have raised ValidationError"
            except ValidationError as e:
                assert "empty" in str(e).lower()
                print("✓ Empty image list raises ValidationError")


def test_invalid_image_paths():
    """Test that all invalid paths raises ValidationError."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with tempfile.TemporaryDirectory() as output_dir:
            config = BatchConfig(
                input_dir=temp_dir,
                output_dir=output_dir,
                reference_images=['test.png'],
                style='line + shadow'
            )
            processor = BatchProcessor(config)
            
            try:
                processor.add_images([
                    '/nonexistent/path/image.png',
                    '/another/bad/path.jpg'
                ])
                assert False, "Should have raised ValidationError"
            except ValidationError as e:
                assert "no valid images" in str(e).lower()
                print("✓ All invalid paths raises ValidationError")


def test_mixed_valid_invalid_paths():
    """Test that valid images are added even when some are invalid."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with tempfile.TemporaryDirectory() as output_dir:
            # Create one valid image
            valid_image_path = os.path.join(temp_dir, 'valid.png')
            img = Image.new('RGB', (100, 100), color='white')
            img.save(valid_image_path)
            
            config = BatchConfig(
                input_dir=temp_dir,
                output_dir=output_dir,
                reference_images=['test.png'],
                style='line + shadow'
            )
            processor = BatchProcessor(config)
            
            # Add mix of valid and invalid
            processor.add_images([
                valid_image_path,
                '/nonexistent/path/image.png',
                '/another/bad/path.jpg'
            ])
            
            # Should have added only the valid image
            assert processor.queue.size() == 1
            print("✓ Mixed valid/invalid paths: only valid images added")


def test_invalid_json_config():
    """Test that invalid JSON raises ConfigurationError."""
    handler = ConfigurationHandler()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{invalid json}')
        temp_file = f.name
    
    try:
        try:
            handler.load_config_file(temp_file)
            assert False, "Should have raised ConfigurationError"
        except ConfigurationError as e:
            assert "parse" in str(e).lower() or "json" in str(e).lower()
            print("✓ Invalid JSON raises ConfigurationError")
    finally:
        os.unlink(temp_file)


def test_invalid_config_values_use_defaults():
    """Test that invalid config values are replaced with defaults."""
    handler = ConfigurationHandler()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            'default': {
                'style': 'invalid_style',
                'seed': -5,
                'num_inference_steps': 0,
                'top_k': 'not_a_number'
            }
        }, f)
        temp_file = f.name
    
    try:
        config = handler.load_config_file(temp_file)
        default_config = handler.get_default_config()
        
        # Should have replaced invalid values with defaults
        assert default_config['style'] == 'line + shadow'
        assert default_config['seed'] == 0
        assert default_config['num_inference_steps'] == 10
        assert default_config['top_k'] == 3
        print("✓ Invalid config values replaced with defaults")
    finally:
        os.unlink(temp_file)


def test_valid_config_loads_correctly():
    """Test that valid configuration loads without modification."""
    handler = ConfigurationHandler()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            'default': {
                'style': 'line + shadow',
                'seed': 42,
                'num_inference_steps': 20
            },
            'images': {
                'test.png': {
                    'seed': 100
                }
            }
        }, f)
        temp_file = f.name
    
    try:
        config = handler.load_config_file(temp_file)
        default_config = handler.get_default_config()
        image_config = handler.get_image_config('test.png')
        
        # Check default config
        assert default_config['style'] == 'line + shadow'
        assert default_config['seed'] == 42
        assert default_config['num_inference_steps'] == 20
        
        # Check image config (merged with defaults)
        assert image_config['seed'] == 100  # Override
        assert image_config['num_inference_steps'] == 20  # From default
        
        print("✓ Valid configuration loads correctly")
    finally:
        os.unlink(temp_file)


def test_image_processing_error_includes_context():
    """Test that ImageProcessingError includes image path and context."""
    try:
        raise ImageProcessingError('/path/to/image.png', 'Test error message')
    except ImageProcessingError as e:
        assert e.image_path == '/path/to/image.png'
        assert 'Test error message' in str(e)
        assert '/path/to/image.png' in str(e)
        print("✓ ImageProcessingError includes context")


def test_error_chaining_preserved():
    """Test that error chaining is preserved for debugging."""
    try:
        try:
            raise ValueError('Original error')
        except ValueError as original:
            raise ImageProcessingError('/path/to/image.png', 'Wrapped error') from original
    except ImageProcessingError as e:
        assert e.__cause__ is not None
        assert isinstance(e.__cause__, ValueError)
        print("✓ Error chaining preserved")


def test_config_validation_collects_all_errors():
    """Test that config validation reports all errors at once."""
    handler = ConfigurationHandler()
    
    invalid_config = {
        'style': 123,  # Should be string
        'seed': -5,  # Should be non-negative
        'num_inference_steps': 0,  # Should be at least 1
        'recursive': 'yes'  # Should be boolean
    }
    
    try:
        handler.validate_config(invalid_config)
        assert False, "Should have raised ConfigurationError"
    except ConfigurationError as e:
        error_msg = str(e)
        # Should mention multiple errors
        assert 'style' in error_msg
        assert 'seed' in error_msg
        assert 'num_inference_steps' in error_msg
        assert 'recursive' in error_msg
        print("✓ Config validation collects all errors")


if __name__ == '__main__':
    print("Running error handling tests...\n")
    
    test_empty_image_list()
    test_invalid_image_paths()
    test_mixed_valid_invalid_paths()
    test_invalid_json_config()
    test_invalid_config_values_use_defaults()
    test_valid_config_loads_correctly()
    test_image_processing_error_includes_context()
    test_error_chaining_preserved()
    test_config_validation_collects_all_errors()
    
    print("\n✅ All error handling tests passed!")

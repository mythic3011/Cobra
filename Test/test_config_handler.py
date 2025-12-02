"""
Tests for configuration management.

This module tests the BatchConfig dataclass and ConfigurationHandler class.
"""

import json
import pytest
import tempfile
from pathlib import Path

from batch_processing.config import BatchConfig, ConfigurationHandler
from batch_processing.exceptions import ConfigurationError


class TestBatchConfig:
    """Tests for BatchConfig dataclass."""
    
    def test_batch_config_creation_with_defaults(self):
        """Test creating BatchConfig with minimal required fields."""
        config = BatchConfig(
            input_dir="/input",
            output_dir="/output",
            reference_images=["ref1.png", "ref2.png"]
        )
        
        assert config.input_dir == "/input"
        assert config.output_dir == "/output"
        assert config.reference_images == ["ref1.png", "ref2.png"]
        assert config.style == "line + shadow"
        assert config.seed == 0
        assert config.num_inference_steps == 10
        assert config.top_k == 3
        assert config.recursive is False
        assert config.overwrite is False
        assert config.preview_mode is False
        assert config.max_concurrent == 1
        assert config.input_is_zip is False
        assert config.output_as_zip is False
        assert config.zip_output_name is None
    
    def test_batch_config_with_all_fields(self):
        """Test creating BatchConfig with all fields specified."""
        config = BatchConfig(
            input_dir="/input",
            output_dir="/output",
            reference_images=["ref1.png"],
            style="line",
            seed=42,
            num_inference_steps=20,
            top_k=5,
            recursive=True,
            overwrite=True,
            preview_mode=True,
            max_concurrent=2,
            input_is_zip=True,
            output_as_zip=True,
            zip_output_name="output.zip"
        )
        
        assert config.style == "line"
        assert config.seed == 42
        assert config.num_inference_steps == 20
        assert config.top_k == 5
        assert config.recursive is True
        assert config.overwrite is True
        assert config.preview_mode is True
        assert config.max_concurrent == 2
        assert config.input_is_zip is True
        assert config.output_as_zip is True
        assert config.zip_output_name == "output.zip"
    
    def test_batch_config_validation_empty_input_dir(self):
        """Test that empty input_dir raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="input_dir cannot be empty"):
            BatchConfig(
                input_dir="",
                output_dir="/output",
                reference_images=["ref.png"]
            )
    
    def test_batch_config_validation_empty_output_dir(self):
        """Test that empty output_dir raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="output_dir cannot be empty"):
            BatchConfig(
                input_dir="/input",
                output_dir="",
                reference_images=["ref.png"]
            )
    
    def test_batch_config_validation_invalid_style(self):
        """Test that invalid style raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="Invalid style"):
            BatchConfig(
                input_dir="/input",
                output_dir="/output",
                reference_images=["ref.png"],
                style="invalid_style"
            )
    
    def test_batch_config_validation_negative_seed(self):
        """Test that negative seed raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="seed must be non-negative"):
            BatchConfig(
                input_dir="/input",
                output_dir="/output",
                reference_images=["ref.png"],
                seed=-1
            )
    
    def test_batch_config_validation_invalid_num_inference_steps(self):
        """Test that num_inference_steps < 1 raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="num_inference_steps must be at least 1"):
            BatchConfig(
                input_dir="/input",
                output_dir="/output",
                reference_images=["ref.png"],
                num_inference_steps=0
            )
    
    def test_batch_config_validation_invalid_top_k(self):
        """Test that top_k < 1 raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="top_k must be at least 1"):
            BatchConfig(
                input_dir="/input",
                output_dir="/output",
                reference_images=["ref.png"],
                top_k=0
            )
    
    def test_batch_config_validation_invalid_max_concurrent(self):
        """Test that max_concurrent < 1 raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="max_concurrent must be at least 1"):
            BatchConfig(
                input_dir="/input",
                output_dir="/output",
                reference_images=["ref.png"],
                max_concurrent=0
            )
    
    def test_batch_config_auto_zip_name(self):
        """Test that zip_output_name is auto-generated when output_as_zip is True."""
        config = BatchConfig(
            input_dir="/input",
            output_dir="/my_output",
            reference_images=["ref.png"],
            output_as_zip=True
        )
        
        assert config.zip_output_name == "my_output_colorized.zip"
    
    def test_batch_config_to_dict(self):
        """Test converting BatchConfig to dictionary."""
        config = BatchConfig(
            input_dir="/input",
            output_dir="/output",
            reference_images=["ref1.png", "ref2.png"],
            seed=42
        )
        
        config_dict = config.to_dict()
        
        assert config_dict["input_dir"] == "/input"
        assert config_dict["output_dir"] == "/output"
        assert config_dict["reference_images"] == ["ref1.png", "ref2.png"]
        assert config_dict["seed"] == 42
        assert "style" in config_dict
        assert "num_inference_steps" in config_dict


class TestConfigurationHandler:
    """Tests for ConfigurationHandler class."""
    
    def test_load_config_file_basic(self):
        """Test loading a basic configuration file."""
        handler = ConfigurationHandler()
        
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "default": {
                    "style": "line",
                    "seed": 42,
                    "num_inference_steps": 20
                },
                "images": {
                    "image1.png": {
                        "seed": 100
                    }
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            result = handler.load_config_file(config_path)
            
            assert "default" in result
            assert "images" in result
            assert result["default"]["style"] == "line"
            assert result["default"]["seed"] == 42
            assert result["images"]["image1.png"]["seed"] == 100
        finally:
            Path(config_path).unlink()
    
    def test_load_config_file_not_found(self):
        """Test that loading non-existent file raises ConfigurationError."""
        handler = ConfigurationHandler()
        
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            handler.load_config_file("/nonexistent/config.json")
    
    def test_load_config_file_invalid_json(self):
        """Test that invalid JSON raises ConfigurationError."""
        handler = ConfigurationHandler()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="Failed to parse JSON"):
                handler.load_config_file(config_path)
        finally:
            Path(config_path).unlink()
    
    def test_get_image_config_with_override(self):
        """Test getting image config with per-image override."""
        handler = ConfigurationHandler()
        
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "default": {
                    "style": "line",
                    "seed": 42,
                    "top_k": 3
                },
                "images": {
                    "special.png": {
                        "seed": 100,
                        "top_k": 5
                    }
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            handler.load_config_file(config_path)
            
            # Get config for image with override
            config = handler.get_image_config("special.png")
            assert config["style"] == "line"  # From default
            assert config["seed"] == 100  # Overridden
            assert config["top_k"] == 5  # Overridden
            
            # Get config for image without override
            config = handler.get_image_config("normal.png")
            assert config["style"] == "line"
            assert config["seed"] == 42
            assert config["top_k"] == 3
        finally:
            Path(config_path).unlink()
    
    def test_get_image_config_with_path(self):
        """Test that get_image_config works with full paths."""
        handler = ConfigurationHandler()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "default": {"seed": 42},
                "images": {
                    "test.png": {"seed": 100}
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            handler.load_config_file(config_path)
            
            # Should work with full path
            config = handler.get_image_config("/some/path/to/test.png")
            assert config["seed"] == 100
        finally:
            Path(config_path).unlink()
    
    def test_validate_config_valid(self):
        """Test validating a valid configuration."""
        handler = ConfigurationHandler()
        
        config = {
            "style": "line",
            "seed": 42,
            "num_inference_steps": 20,
            "top_k": 5,
            "recursive": True,
            "reference_images": ["ref1.png", "ref2.png"]
        }
        
        assert handler.validate_config(config) is True
    
    def test_validate_config_invalid_style(self):
        """Test that invalid style raises ConfigurationError."""
        handler = ConfigurationHandler()
        
        config = {"style": "invalid"}
        
        with pytest.raises(ConfigurationError, match="Invalid style"):
            handler.validate_config(config)
    
    def test_validate_config_invalid_seed(self):
        """Test that invalid seed raises ConfigurationError."""
        handler = ConfigurationHandler()
        
        config = {"seed": -1}
        
        with pytest.raises(ConfigurationError, match="seed must be at least 0"):
            handler.validate_config(config)
    
    def test_validate_config_invalid_type(self):
        """Test that non-dict config raises ConfigurationError."""
        handler = ConfigurationHandler()
        
        with pytest.raises(ConfigurationError, match="must be a dictionary"):
            handler.validate_config("not a dict")
    
    def test_merge_configs(self):
        """Test merging default and override configurations."""
        handler = ConfigurationHandler()
        
        default = {
            "style": "line",
            "seed": 42,
            "top_k": 3
        }
        
        override = {
            "seed": 100,
            "num_inference_steps": 20
        }
        
        merged = handler.merge_configs(default, override)
        
        assert merged["style"] == "line"  # From default
        assert merged["seed"] == 100  # Overridden
        assert merged["top_k"] == 3  # From default
        assert merged["num_inference_steps"] == 20  # From override
    
    def test_merge_configs_list_replacement(self):
        """Test that list values are replaced, not merged."""
        handler = ConfigurationHandler()
        
        default = {
            "reference_images": ["ref1.png", "ref2.png"]
        }
        
        override = {
            "reference_images": ["ref3.png"]
        }
        
        merged = handler.merge_configs(default, override)
        
        assert merged["reference_images"] == ["ref3.png"]
    
    def test_get_default_config(self):
        """Test getting default configuration."""
        handler = ConfigurationHandler()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "default": {
                    "style": "line",
                    "seed": 42
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            handler.load_config_file(config_path)
            default = handler.get_default_config()
            
            assert default["style"] == "line"
            assert default["seed"] == 42
        finally:
            Path(config_path).unlink()
    
    def test_has_image_config(self):
        """Test checking if image has custom configuration."""
        handler = ConfigurationHandler()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "default": {"seed": 42},
                "images": {
                    "special.png": {"seed": 100}
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            handler.load_config_file(config_path)
            
            assert handler.has_image_config("special.png") is True
            assert handler.has_image_config("normal.png") is False
            assert handler.has_image_config("/path/to/special.png") is True
        finally:
            Path(config_path).unlink()
    
    def test_clear_cache(self):
        """Test clearing configuration cache."""
        handler = ConfigurationHandler()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "default": {"seed": 42}
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            handler.load_config_file(config_path)
            assert handler.get_default_config() == {"seed": 42}
            
            handler.clear_cache()
            assert handler.get_default_config() == {}
        finally:
            Path(config_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

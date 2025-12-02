"""
Demo script for configuration management system.

This script demonstrates the key features of the BatchConfig and
ConfigurationHandler classes.
"""

import json
import tempfile
from pathlib import Path

from batch_processing.config import BatchConfig, ConfigurationHandler
from batch_processing.exceptions import ConfigurationError


def demo_batch_config():
    """Demonstrate BatchConfig creation and validation."""
    print("=" * 60)
    print("DEMO: BatchConfig")
    print("=" * 60)
    
    # Create a basic config
    print("\n1. Creating basic BatchConfig:")
    config = BatchConfig(
        input_dir="/path/to/input",
        output_dir="/path/to/output",
        reference_images=["ref1.png", "ref2.png"]
    )
    print(f"   Input: {config.input_dir}")
    print(f"   Output: {config.output_dir}")
    print(f"   References: {config.reference_images}")
    print(f"   Style: {config.style} (default)")
    print(f"   Seed: {config.seed} (default)")
    
    # Create a config with all options
    print("\n2. Creating BatchConfig with all options:")
    config = BatchConfig(
        input_dir="/input",
        output_dir="/output",
        reference_images=["ref.png"],
        style="line",
        seed=42,
        num_inference_steps=20,
        top_k=5,
        recursive=True,
        preview_mode=True,
        output_as_zip=True
    )
    print(f"   Style: {config.style}")
    print(f"   Seed: {config.seed}")
    print(f"   Steps: {config.num_inference_steps}")
    print(f"   Top-K: {config.top_k}")
    print(f"   Recursive: {config.recursive}")
    print(f"   Preview: {config.preview_mode}")
    print(f"   Output as ZIP: {config.output_as_zip}")
    print(f"   ZIP name: {config.zip_output_name} (auto-generated)")
    
    # Demonstrate validation
    print("\n3. Demonstrating validation:")
    try:
        invalid_config = BatchConfig(
            input_dir="",
            output_dir="/output",
            reference_images=["ref.png"]
        )
    except ConfigurationError as e:
        print(f"   ✓ Caught error: {e}")
    
    try:
        invalid_config = BatchConfig(
            input_dir="/input",
            output_dir="/output",
            reference_images=["ref.png"],
            style="invalid_style"
        )
    except ConfigurationError as e:
        print(f"   ✓ Caught error: {e}")
    
    # Convert to dict
    print("\n4. Converting to dictionary:")
    config_dict = config.to_dict()
    print(f"   Keys: {list(config_dict.keys())}")
    print(f"   Sample: seed={config_dict['seed']}, style={config_dict['style']}")


def demo_configuration_handler():
    """Demonstrate ConfigurationHandler usage."""
    print("\n" + "=" * 60)
    print("DEMO: ConfigurationHandler")
    print("=" * 60)
    
    # Create a temporary config file
    config_data = {
        "default": {
            "style": "line + shadow",
            "seed": 0,
            "num_inference_steps": 10,
            "top_k": 3
        },
        "images": {
            "page_001.png": {
                "seed": 42,
                "top_k": 5
            },
            "page_002.png": {
                "seed": 100,
                "num_inference_steps": 20
            },
            "special.png": {
                "style": "line",
                "reference_images": ["custom_ref.png"]
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f, indent=2)
        config_path = f.name
    
    try:
        # Load config file
        print("\n1. Loading configuration file:")
        handler = ConfigurationHandler()
        handler.load_config_file(config_path)
        print(f"   ✓ Loaded from: {config_path}")
        
        # Get default config
        print("\n2. Default configuration:")
        default = handler.get_default_config()
        for key, value in default.items():
            print(f"   {key}: {value}")
        
        # Get image-specific configs
        print("\n3. Image-specific configurations:")
        
        print("\n   page_001.png:")
        config = handler.get_image_config("page_001.png")
        print(f"      style: {config.get('style')} (from default)")
        print(f"      seed: {config.get('seed')} (overridden)")
        print(f"      top_k: {config.get('top_k')} (overridden)")
        
        print("\n   page_002.png:")
        config = handler.get_image_config("page_002.png")
        print(f"      seed: {config.get('seed')} (overridden)")
        print(f"      num_inference_steps: {config.get('num_inference_steps')} (overridden)")
        print(f"      top_k: {config.get('top_k')} (from default)")
        
        print("\n   special.png:")
        config = handler.get_image_config("special.png")
        print(f"      style: {config.get('style')} (overridden)")
        print(f"      reference_images: {config.get('reference_images')} (overridden)")
        
        print("\n   normal.png (no custom config):")
        config = handler.get_image_config("normal.png")
        print(f"      All values from default:")
        for key, value in config.items():
            print(f"         {key}: {value}")
        
        # Check for custom configs
        print("\n4. Checking for custom configurations:")
        images = ["page_001.png", "normal.png", "special.png"]
        for image in images:
            has_config = handler.has_image_config(image)
            status = "✓ Has custom config" if has_config else "✗ Uses defaults"
            print(f"   {image}: {status}")
        
        # Demonstrate validation
        print("\n5. Configuration validation:")
        valid_config = {"style": "line", "seed": 42, "top_k": 5}
        try:
            handler.validate_config(valid_config)
            print(f"   ✓ Valid config: {valid_config}")
        except ConfigurationError as e:
            print(f"   ✗ Error: {e}")
        
        invalid_config = {"style": "invalid", "seed": -1}
        try:
            handler.validate_config(invalid_config)
            print(f"   ✓ Valid config: {invalid_config}")
        except ConfigurationError as e:
            print(f"   ✓ Caught invalid config: {e}")
        
        # Demonstrate merging
        print("\n6. Configuration merging:")
        default = {"style": "line", "seed": 0, "top_k": 3}
        override = {"seed": 42, "num_inference_steps": 20}
        merged = handler.merge_configs(default, override)
        print(f"   Default: {default}")
        print(f"   Override: {override}")
        print(f"   Merged: {merged}")
        
    finally:
        # Clean up temp file
        Path(config_path).unlink()


def demo_error_handling():
    """Demonstrate error handling."""
    print("\n" + "=" * 60)
    print("DEMO: Error Handling")
    print("=" * 60)
    
    handler = ConfigurationHandler()
    
    print("\n1. Non-existent file:")
    try:
        handler.load_config_file("/nonexistent/config.json")
    except ConfigurationError as e:
        print(f"   ✓ Caught: {e}")
    
    print("\n2. Invalid JSON:")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        invalid_path = f.name
    
    try:
        handler.load_config_file(invalid_path)
    except ConfigurationError as e:
        print(f"   ✓ Caught: {e}")
    finally:
        Path(invalid_path).unlink()
    
    print("\n3. Invalid configuration values:")
    errors = [
        ("Empty input_dir", {"input_dir": "", "output_dir": "/out", "reference_images": []}),
        ("Invalid style", {"input_dir": "/in", "output_dir": "/out", "reference_images": [], "style": "bad"}),
        ("Negative seed", {"input_dir": "/in", "output_dir": "/out", "reference_images": [], "seed": -1}),
        ("Zero steps", {"input_dir": "/in", "output_dir": "/out", "reference_images": [], "num_inference_steps": 0}),
    ]
    
    for desc, config_dict in errors:
        try:
            if "input_dir" in config_dict:
                config = BatchConfig(**config_dict)
            else:
                handler.validate_config(config_dict)
        except ConfigurationError as e:
            print(f"   ✓ {desc}: {str(e)[:50]}...")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Configuration Management System Demo")
    print("=" * 60)
    
    demo_batch_config()
    demo_configuration_handler()
    demo_error_handling()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print()

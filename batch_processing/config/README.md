# Configuration Management Module

This module provides configuration management for batch processing operations in the Cobra comic line art colorization system.

## Components

### BatchConfig

A dataclass that holds all configuration parameters for batch processing.

**Required Fields:**
- `input_dir`: Directory containing input images
- `output_dir`: Directory where processed images will be saved
- `reference_images`: List of paths to reference images

**Optional Fields with Defaults:**
- `style`: Colorization style ("line" or "line + shadow", default: "line + shadow")
- `seed`: Random seed (default: 0)
- `num_inference_steps`: Number of diffusion steps (default: 10)
- `top_k`: Number of top reference images (default: 3)
- `recursive`: Scan directories recursively (default: False)
- `overwrite`: Overwrite existing files (default: False)
- `preview_mode`: Process only first image (default: False)
- `max_concurrent`: Max concurrent images (default: 1)
- `input_is_zip`: Input is ZIP file (default: False)
- `output_as_zip`: Package output as ZIP (default: False)
- `zip_output_name`: Output ZIP filename (default: auto-generated)

**Example:**

```python
from batch_processing.config import BatchConfig

config = BatchConfig(
    input_dir="/path/to/input",
    output_dir="/path/to/output",
    reference_images=["ref1.png", "ref2.png"],
    style="line + shadow",
    seed=42,
    num_inference_steps=20,
    top_k=5
)
```

### ConfigurationHandler

A class for loading, validating, and merging configurations from JSON files.

**Key Methods:**

- `load_config_file(path)`: Load configuration from JSON file
- `get_image_config(image_path)`: Get merged config for specific image
- `validate_config(config)`: Validate configuration dictionary
- `merge_configs(default, override)`: Merge two configurations
- `get_default_config()`: Get default configuration
- `has_image_config(image_path)`: Check if image has custom config
- `clear_cache()`: Clear configuration cache

**Example:**

```python
from batch_processing.config import ConfigurationHandler

handler = ConfigurationHandler()
handler.load_config_file("config.json")

# Get config for specific image
config = handler.get_image_config("page_001.png")

# Check if image has custom config
if handler.has_image_config("page_001.png"):
    print("Image has custom configuration")
```

## Configuration File Format

Configuration files should be JSON with the following structure:

```json
{
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
```

### Sections

- **`default`**: Default configuration applied to all images
- **`images`**: Per-image configuration overrides

### Merging Behavior

When getting configuration for an image:
1. Start with default configuration
2. Apply image-specific overrides
3. Override values completely replace defaults (no deep merging)

## Validation

Both `BatchConfig` and `ConfigurationHandler` perform validation:

### BatchConfig Validation

- `input_dir` and `output_dir` cannot be empty
- `style` must be "line" or "line + shadow"
- `seed` must be non-negative
- `num_inference_steps` must be at least 1
- `top_k` must be at least 1
- `max_concurrent` must be at least 1
- Auto-generates `zip_output_name` if `output_as_zip` is True

### ConfigurationHandler Validation

- Validates configuration structure
- Checks parameter types
- Validates parameter ranges
- Ensures valid style values
- Validates reference image lists

## Error Handling

All errors raise `ConfigurationError` from `batch_processing.exceptions`:

```python
from batch_processing.config import BatchConfig
from batch_processing.exceptions import ConfigurationError

try:
    config = BatchConfig(
        input_dir="",
        output_dir="/output",
        reference_images=["ref.png"]
    )
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

## Usage Examples

### Basic Usage

```python
from batch_processing.config import BatchConfig

# Create configuration
config = BatchConfig(
    input_dir="/comics/input",
    output_dir="/comics/output",
    reference_images=["style_ref.png"]
)

# Access configuration
print(f"Processing from: {config.input_dir}")
print(f"Using style: {config.style}")
print(f"Seed: {config.seed}")
```

### Loading from File

```python
from batch_processing.config import ConfigurationHandler

# Load configuration
handler = ConfigurationHandler()
handler.load_config_file("batch_config.json")

# Get configuration for each image
images = ["page_001.png", "page_002.png", "page_003.png"]
for image in images:
    config = handler.get_image_config(image)
    print(f"{image}: seed={config.get('seed')}, top_k={config.get('top_k')}")
```

### Custom Configuration per Image

```python
# config.json
{
  "default": {
    "style": "line + shadow",
    "seed": 0,
    "top_k": 3
  },
  "images": {
    "cover.png": {
      "seed": 42,
      "top_k": 10,
      "num_inference_steps": 50
    }
  }
}

# Python code
handler = ConfigurationHandler()
handler.load_config_file("config.json")

# Cover page gets special treatment
cover_config = handler.get_image_config("cover.png")
# seed=42, top_k=10, num_inference_steps=50, style="line + shadow"

# Other pages use defaults
page_config = handler.get_image_config("page_001.png")
# seed=0, top_k=3, style="line + shadow"
```

### ZIP Processing

```python
from batch_processing.config import BatchConfig

# Configure for ZIP input and output
config = BatchConfig(
    input_dir="comics.zip",
    output_dir="/output",
    reference_images=["ref.png"],
    input_is_zip=True,
    output_as_zip=True,
    zip_output_name="colorized_comics.zip"
)

print(f"Input ZIP: {config.input_is_zip}")
print(f"Output ZIP: {config.output_as_zip}")
print(f"Output name: {config.zip_output_name}")
```

### Validation

```python
from batch_processing.config import ConfigurationHandler
from batch_processing.exceptions import ConfigurationError

handler = ConfigurationHandler()

# Validate configuration
config = {
    "style": "line",
    "seed": 42,
    "num_inference_steps": 20,
    "top_k": 5
}

try:
    handler.validate_config(config)
    print("Configuration is valid")
except ConfigurationError as e:
    print(f"Invalid configuration: {e}")
```

## Integration

The configuration module integrates with other batch processing components:

- **Queue System**: `ImageQueueItem` accepts optional config dict
- **Batch Processor**: Uses `BatchConfig` for initialization
- **CLI Interface**: Parses arguments into `BatchConfig`
- **Gradio UI**: Creates `BatchConfig` from form inputs

## Testing

Run tests with:

```bash
uv run pytest test_config_handler.py -v
```

Or run the demo:

```bash
uv run python demo_config.py
```

## Requirements Satisfied

This module satisfies the following requirements from the spec:

- **Requirement 7.1**: Configuration file parsing
- **Requirement 7.2**: Per-image configuration application
- **Requirement 7.3**: Default configuration fallback
- **Requirement 7.4**: Configuration error handling
- **Requirement 3.1, 3.2, 3.3**: ZIP options support

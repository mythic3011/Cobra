# File I/O Module

This module provides file and directory operations for batch processing, with a focus on ZIP file handling and image classification integration.

## Features

### ZIP File Handling

- **Validation**: Check if a file is a valid ZIP archive
- **Extraction**: Extract images from ZIP files with nested ZIP support (one level deep)
- **Output Packaging**: Create ZIP archives from processed images
- **Automatic Cleanup**: Manage temporary extraction directories
- **Structure Preservation**: Optionally preserve directory structure in output ZIPs
- **Metadata Inclusion**: Add processing metadata to output ZIPs

### Image Classification Integration

- **Automatic Separation**: Separate line art from colored reference images
- **Smart Detection**: Use color analysis to classify images automatically

## Usage Examples

### Basic ZIP Extraction

```python
from batch_processing.io import extract_zip_file, cleanup_temp_directory

# Extract images from ZIP
extract_dir, image_paths = extract_zip_file("input.zip")

try:
    # Process images...
    for image_path in image_paths:
        print(f"Processing {image_path}")
finally:
    # Always cleanup
    cleanup_temp_directory(extract_dir)
```

### ZIP Validation

```python
from batch_processing.io import is_zip_file

if is_zip_file("myfile.zip"):
    print("Valid ZIP file")
else:
    print("Invalid or corrupted ZIP")
```

### Creating Output ZIP

```python
from batch_processing.io import create_output_zip

# Basic usage
zip_path = create_output_zip(
    output_dir="./processed_images",
    zip_name="results"
)

# With metadata
metadata = {
    "batch_id": "batch_001",
    "total_images": 10,
    "processing_time": 120.5
}
zip_path = create_output_zip(
    output_dir="./processed_images",
    zip_name="results",
    metadata=metadata,
    preserve_structure=True
)
```

### Separating Line Art from References

```python
from batch_processing.io import (
    extract_zip_file,
    separate_line_art_and_references,
    cleanup_temp_directory
)

# Extract ZIP
extract_dir, all_images = extract_zip_file("comic_chapter.zip")

try:
    # Automatically separate line art from colored references
    line_art, references = separate_line_art_and_references(all_images)
    
    print(f"Found {len(line_art)} pages to colorize")
    print(f"Found {len(references)} reference images")
    
    # Process line art using references...
    
finally:
    cleanup_temp_directory(extract_dir)
```

### Complete Workflow

```python
from batch_processing.io import (
    extract_zip_file,
    separate_line_art_and_references,
    create_output_zip,
    cleanup_temp_directory
)

# 1. Extract input ZIP
extract_dir, all_images = extract_zip_file("input.zip")

try:
    # 2. Classify and separate images
    line_art_images, reference_images = separate_line_art_and_references(all_images)
    
    # 3. Process line art (your colorization logic here)
    output_dir = "./output"
    for line_art_path in line_art_images:
        # colorize_image(line_art_path, reference_images, output_dir)
        pass
    
    # 4. Package results
    metadata = {
        "total_processed": len(line_art_images),
        "references_used": len(reference_images)
    }
    output_zip = create_output_zip(output_dir, "colorized", metadata=metadata)
    
    print(f"Results saved to: {output_zip}")
    
finally:
    # 5. Cleanup
    cleanup_temp_directory(extract_dir)
```

## Nested ZIP Support

The module supports nested ZIP files up to one level deep:

```python
# If input.zip contains:
#   - page1.png
#   - page2.png
#   - references.zip (containing ref1.png, ref2.png)
#
# extract_zip_file will extract all 4 images

extract_dir, images = extract_zip_file("input.zip")
# images will contain: [page1.png, page2.png, ref1.png, ref2.png]
```

## Supported Image Formats

The following image formats are supported:
- PNG (`.png`)
- JPEG (`.jpg`, `.jpeg`)
- WebP (`.webp`)

## Error Handling

The module provides specific exceptions for different error scenarios:

```python
from batch_processing.exceptions import (
    ZIPExtractionError,
    ValidationError
)

try:
    extract_dir, images = extract_zip_file("myfile.zip")
except ValidationError:
    print("Invalid ZIP file")
except ZIPExtractionError as e:
    print(f"Extraction failed: {e}")
```

## Metadata Format

When creating output ZIPs with metadata, the following fields are automatically added:

```json
{
  "created_at": "2025-12-02T10:30:45.123456",
  "cobra_version": "batch_processing_v1",
  "batch_id": "your_custom_id",
  "total_images": 10,
  ...
}
```

## Directory Structure Preservation

When `preserve_structure=True` (default), the output ZIP maintains the directory structure:

```
Input:
  output/
    chapter1/
      page1.png
      page2.png
    chapter2/
      page1.png

Output ZIP:
  chapter1/page1.png
  chapter1/page2.png
  chapter2/page1.png
  processing_metadata.json
```

When `preserve_structure=False`, all files are placed at the root level:

```
Output ZIP:
  page1.png
  page2.png
  page1.png  (or page1_1.png if collision)
  processing_metadata.json
```

## Automatic Cleanup

The `cleanup_temp_directory` function safely removes temporary directories:

- Logs warnings instead of raising exceptions
- Handles permission errors gracefully
- Recursively removes all contents
- Safe to call on non-existent directories

## Performance Considerations

- ZIP extraction creates temporary directories that should be cleaned up
- Large ZIP files may require significant disk space during extraction
- Nested ZIP extraction is limited to one level to prevent excessive recursion
- Image classification caches results to avoid reprocessing

## Testing

Run the test suite:

```bash
# Unit tests
uv run python test_zip_handler.py

# Integration tests
uv run python test_zip_workflow.py
```

## API Reference

### `is_zip_file(path: str) -> bool`

Validate if a file is a valid ZIP archive.

**Parameters:**
- `path`: Path to the file to check

**Returns:**
- `True` if valid ZIP file, `False` otherwise

### `extract_zip_file(zip_path: str, extract_dir: Optional[str] = None) -> Tuple[str, List[str]]`

Extract all image files from a ZIP archive.

**Parameters:**
- `zip_path`: Path to the ZIP file
- `extract_dir`: Optional extraction directory (creates temp dir if None)

**Returns:**
- Tuple of (extraction_directory, list_of_image_paths)

**Raises:**
- `ValidationError`: If ZIP file is invalid
- `ZIPExtractionError`: If extraction fails

### `cleanup_temp_directory(directory: str) -> None`

Clean up a temporary extraction directory.

**Parameters:**
- `directory`: Path to the directory to remove

### `create_output_zip(output_dir: str, zip_name: str, metadata: Optional[dict] = None, preserve_structure: bool = True) -> str`

Package processed images into a ZIP file.

**Parameters:**
- `output_dir`: Directory containing processed images
- `zip_name`: Name for output ZIP (without .zip extension)
- `metadata`: Optional metadata dictionary
- `preserve_structure`: Whether to preserve directory structure

**Returns:**
- Path to created ZIP file

**Raises:**
- `ValidationError`: If output directory is invalid
- `ZIPExtractionError`: If ZIP creation fails

### `separate_line_art_and_references(image_paths: List[str], classifier=None) -> Tuple[List[str], List[str]]`

Separate images into line art and colored references.

**Parameters:**
- `image_paths`: List of image file paths
- `classifier`: Optional ImageClassifier instance

**Returns:**
- Tuple of (line_art_paths, reference_paths)

## Integration with Other Modules

This module integrates with:

- **classification**: Uses `ImageClassifier` for automatic image separation
- **exceptions**: Provides specific error types for error handling
- **logging_config**: Logs all operations for debugging and monitoring

# ZIP Handling Quick Start Guide

## 5-Minute Quick Start

### Scenario 1: Extract and Process a ZIP File

```python
from batch_processing.io import (
    extract_zip_file,
    separate_line_art_and_references,
    cleanup_temp_directory
)

# Extract ZIP
extract_dir, all_images = extract_zip_file("comic_chapter.zip")

try:
    # Separate line art from references
    line_art, references = separate_line_art_and_references(all_images)
    
    print(f"Found {len(line_art)} pages to colorize")
    print(f"Using {len(references)} reference images")
    
    # Your processing code here...
    
finally:
    # Always cleanup!
    cleanup_temp_directory(extract_dir)
```

### Scenario 2: Create an Output ZIP

```python
from batch_processing.io import create_output_zip

# After processing images to ./output directory
zip_path = create_output_zip(
    output_dir="./output",
    zip_name="colorized_results",
    metadata={
        "batch_id": "batch_001",
        "total_images": 10
    }
)

print(f"Results saved to: {zip_path}")
```

### Scenario 3: Complete Workflow

```python
from batch_processing.io import (
    extract_zip_file,
    separate_line_art_and_references,
    create_output_zip,
    cleanup_temp_directory
)

# 1. Extract
extract_dir, all_images = extract_zip_file("input.zip")

try:
    # 2. Classify
    line_art, refs = separate_line_art_and_references(all_images)
    
    # 3. Process (your code)
    output_dir = "./output"
    for img in line_art:
        # colorize(img, refs, output_dir)
        pass
    
    # 4. Package
    result_zip = create_output_zip(output_dir, "results")
    print(f"Done! {result_zip}")
    
finally:
    # 5. Cleanup
    cleanup_temp_directory(extract_dir)
```

## Common Patterns

### Check if File is a ZIP

```python
from batch_processing.io import is_zip_file

if is_zip_file("myfile.zip"):
    # Process as ZIP
    pass
else:
    # Process as regular file
    pass
```

### Extract to Specific Directory

```python
extract_dir, images = extract_zip_file(
    "input.zip",
    extract_dir="./my_extraction_folder"
)
```

### Create ZIP Without Structure

```python
# All files at root level in ZIP
zip_path = create_output_zip(
    output_dir="./output",
    zip_name="flat_results",
    preserve_structure=False
)
```

### Add Custom Metadata

```python
metadata = {
    "batch_id": "batch_123",
    "user": "artist_name",
    "style": "manga",
    "processing_time": 120.5,
    "settings": {
        "seed": 42,
        "steps": 10
    }
}

zip_path = create_output_zip(
    output_dir="./output",
    zip_name="results",
    metadata=metadata
)
```

## Error Handling

```python
from batch_processing.io import extract_zip_file
from batch_processing.exceptions import (
    ValidationError,
    ZIPExtractionError
)

try:
    extract_dir, images = extract_zip_file("input.zip")
except ValidationError:
    print("Invalid or corrupted ZIP file")
except ZIPExtractionError as e:
    print(f"Extraction failed: {e}")
```

## Tips

1. **Always cleanup**: Use try/finally to ensure cleanup happens
2. **Check validity**: Use `is_zip_file()` before extraction
3. **Handle errors**: Catch specific exceptions for better error messages
4. **Use metadata**: Include processing info in output ZIPs for traceability
5. **Preserve structure**: Keep directory structure for organized results

## Supported Formats

- PNG (`.png`)
- JPEG (`.jpg`, `.jpeg`)
- WebP (`.webp`)

## Nested ZIP Support

Nested ZIPs are automatically extracted (one level deep):

```
input.zip
├── page1.png
├── page2.png
└── references.zip
    ├── ref1.png
    └── ref2.png
```

All 4 images will be extracted automatically!

## Need More Help?

- See [README.md](README.md) for detailed documentation
- Run tests: `uv run python test_zip_handler.py`
- Check examples: `uv run python test_zip_workflow.py`

# CLI Quick Start Guide

## Overview

The Cobra batch colorization CLI allows you to colorize multiple comic line art images from the command line without requiring the GUI.

## Installation

Ensure you have the Cobra project set up with all dependencies installed:

```bash
# Install dependencies
uv sync
```

## Basic Usage

### Minimal Command

The simplest way to colorize a batch of images:

```bash
python batch_colorize.py \
  --input-dir ./input_images \
  --output-dir ./output_images \
  --reference-dir ./reference_images
```

This will:
- Process all images in `./input_images`
- Save colorized images to `./output_images`
- Use images in `./reference_images` as style references
- Use default settings (style: "line + shadow", seed: 0, steps: 10, top-k: 3)

### Get Help

Display all available options:

```bash
python batch_colorize.py --help
```

## Common Scenarios

### 1. Custom Parameters

Adjust colorization parameters for better results:

```bash
python batch_colorize.py \
  --input-dir ./input \
  --output-dir ./output \
  --reference-dir ./references \
  --style "line + shadow" \
  --seed 42 \
  --steps 20 \
  --top-k 5
```

**Parameters:**
- `--style`: "line" or "line + shadow" (default: "line + shadow")
- `--seed`: Random seed for reproducibility (default: 0)
- `--steps`: Number of inference steps, higher = better quality but slower (default: 10)
- `--top-k`: Number of reference images to use (default: 3)

### 2. Recursive Directory Scanning

Process images in subdirectories:

```bash
python batch_colorize.py \
  --input-dir ./comics \
  --output-dir ./colorized \
  --reference-dir ./references \
  --recursive
```

This will find all images in `./comics` and all its subdirectories.

### 3. Process ZIP File

Process images from a ZIP file:

```bash
python batch_colorize.py \
  --input-zip ./comic_pages.zip \
  --output-dir ./colorized \
  --reference-dir ./references
```

The CLI will automatically extract the ZIP and process all images inside.

### 4. Output as ZIP

Package all colorized images into a ZIP file:

```bash
python batch_colorize.py \
  --input-dir ./input \
  --output-zip ./colorized_output.zip \
  --reference-dir ./references
```

### 5. Preview Mode

Test settings on the first image before processing the entire batch:

```bash
python batch_colorize.py \
  --input-dir ./input \
  --output-dir ./output \
  --reference-dir ./references \
  --preview
```

This processes only the first image, allowing you to verify settings before committing to the full batch.

### 6. Overwrite Existing Files

By default, the CLI creates numbered variants if output files already exist. To overwrite instead:

```bash
python batch_colorize.py \
  --input-dir ./input \
  --output-dir ./output \
  --reference-dir ./references \
  --overwrite
```

### 7. Verbose Output

See detailed logging information:

```bash
python batch_colorize.py \
  --input-dir ./input \
  --output-dir ./output \
  --reference-dir ./references \
  --verbose
```

### 8. Quiet Mode

Suppress all output except errors:

```bash
python batch_colorize.py \
  --input-dir ./input \
  --output-dir ./output \
  --reference-dir ./references \
  --quiet
```

### 9. Per-Image Configuration

Use a JSON configuration file for per-image settings:

```bash
python batch_colorize.py \
  --input-dir ./input \
  --output-dir ./output \
  --reference-dir ./references \
  --config batch_config.json
```

**Example `batch_config.json`:**

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
      "num_inference_steps": 20
    },
    "page_002.png": {
      "style": "line",
      "top_k": 5
    }
  }
}
```

## Exit Codes

The CLI returns different exit codes to indicate the result:

- **0**: Success - all images processed successfully
- **1**: Validation or configuration error
- **2**: Partial failure - some images failed to process
- **130**: User interrupt (Ctrl+C)

You can use these in scripts:

```bash
python batch_colorize.py --input-dir ./input --output-dir ./output --reference-dir ./refs

if [ $? -eq 0 ]; then
  echo "All images processed successfully!"
elif [ $? -eq 2 ]; then
  echo "Some images failed, check logs"
else
  echo "Processing failed"
fi
```

## Tips and Best Practices

### 1. Start with Preview Mode

Always test your settings on one image first:

```bash
# Test settings
python batch_colorize.py --input-dir ./input --output-dir ./test --reference-dir ./refs --preview

# If satisfied, run full batch
python batch_colorize.py --input-dir ./input --output-dir ./output --reference-dir ./refs
```

### 2. Use Appropriate Steps

- **Fast preview**: `--steps 5` (lower quality, faster)
- **Standard**: `--steps 10` (default, good balance)
- **High quality**: `--steps 20` (better quality, slower)
- **Maximum quality**: `--steps 50` (best quality, very slow)

### 3. Organize Reference Images

Keep your reference images organized:

```
references/
  ├── character_refs/
  │   ├── hero_colored.png
  │   └── villain_colored.png
  └── background_refs/
      ├── city_colored.png
      └── forest_colored.png
```

Then use: `--reference-dir ./references/character_refs`

### 4. Use Consistent Seeds

For reproducible results across multiple runs:

```bash
python batch_colorize.py \
  --input-dir ./input \
  --output-dir ./output \
  --reference-dir ./refs \
  --seed 42
```

### 5. Monitor Progress

Use verbose mode to see detailed progress:

```bash
python batch_colorize.py \
  --input-dir ./input \
  --output-dir ./output \
  --reference-dir ./refs \
  --verbose 2>&1 | tee batch_log.txt
```

This saves all output to `batch_log.txt` while displaying it.

## Troubleshooting

### "No valid images found"

**Problem**: The input directory doesn't contain supported image formats.

**Solution**: Ensure your images are PNG, JPG, JPEG, or WebP format.

### "Reference directory does not exist"

**Problem**: The specified reference directory path is incorrect.

**Solution**: Check the path and ensure it exists:

```bash
ls -la ./reference_dir
```

### "Seed must be non-negative"

**Problem**: You specified a negative seed value.

**Solution**: Use a non-negative integer:

```bash
--seed 0  # or any positive number
```

### Out of Memory Errors

**Problem**: Processing large images or too many at once.

**Solution**: 
1. Process in smaller batches
2. Reduce image resolution before processing
3. Close other GPU-intensive applications

### Slow Processing

**Problem**: Processing takes too long.

**Solution**:
1. Reduce `--steps` (e.g., `--steps 5`)
2. Reduce `--top-k` (e.g., `--top-k 1`)
3. Use preview mode to test settings first

## Examples

### Example 1: Quick Test

```bash
# Process one example image
python batch_colorize.py \
  --input-dir examples/line/example0 \
  --output-dir /tmp/test_output \
  --reference-dir examples/shadow/example0 \
  --preview
```

### Example 2: Production Batch

```bash
# Process entire comic chapter
python batch_colorize.py \
  --input-dir ./chapter1_lineart \
  --output-dir ./chapter1_colorized \
  --reference-dir ./character_references \
  --style "line + shadow" \
  --seed 42 \
  --steps 15 \
  --top-k 5 \
  --recursive \
  --verbose
```

### Example 3: ZIP Workflow

```bash
# Process ZIP and output ZIP
python batch_colorize.py \
  --input-zip ./chapter1_lineart.zip \
  --output-zip ./chapter1_colorized.zip \
  --reference-dir ./references \
  --steps 20
```

## Integration with Scripts

### Bash Script Example

```bash
#!/bin/bash

# Batch colorize multiple chapters
for chapter in chapter1 chapter2 chapter3; do
  echo "Processing $chapter..."
  
  python batch_colorize.py \
    --input-dir ./input/$chapter \
    --output-dir ./output/$chapter \
    --reference-dir ./references \
    --seed 42 \
    --steps 15
  
  if [ $? -eq 0 ]; then
    echo "$chapter completed successfully"
  else
    echo "$chapter failed"
    exit 1
  fi
done

echo "All chapters processed!"
```

### Python Script Example

```python
import subprocess
import sys

def colorize_batch(input_dir, output_dir, ref_dir, **kwargs):
    """Run CLI colorization from Python."""
    cmd = [
        sys.executable, "batch_colorize.py",
        "--input-dir", input_dir,
        "--output-dir", output_dir,
        "--reference-dir", ref_dir,
    ]
    
    # Add optional parameters
    if "seed" in kwargs:
        cmd.extend(["--seed", str(kwargs["seed"])])
    if "steps" in kwargs:
        cmd.extend(["--steps", str(kwargs["steps"])])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

# Use it
success = colorize_batch(
    "./input",
    "./output",
    "./references",
    seed=42,
    steps=15
)

if success:
    print("Batch completed successfully!")
else:
    print("Batch failed!")
```

## Next Steps

1. **Test with examples**: Try the CLI with the provided example images
2. **Experiment with parameters**: Find the best settings for your use case
3. **Automate workflows**: Integrate the CLI into your comic production pipeline
4. **Monitor results**: Check output quality and adjust parameters as needed

## Getting Help

- Run `python batch_colorize.py --help` for all options
- Check `Test/CLI_IMPLEMENTATION_SUMMARY.md` for technical details
- Review `Test/demo_cli.py` for usage examples
- Run `uv run pytest Test/test_cli.py -v` to verify installation

## Summary

The CLI provides a powerful, flexible way to batch colorize comic line art:

✅ Simple command-line interface
✅ Comprehensive parameter control
✅ ZIP file support
✅ Preview mode for testing
✅ Robust error handling
✅ Scriptable and automatable

Start with preview mode, find your optimal settings, then scale up to full batches!

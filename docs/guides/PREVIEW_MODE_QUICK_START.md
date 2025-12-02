# Preview Mode Quick Start Guide

## What is Preview Mode?

Preview mode allows you to process just the first image in your batch to verify your settings are correct before processing the entire batch. This saves time and resources by letting you catch configuration issues early.

## When to Use Preview Mode

✅ **Use preview mode when:**
- Processing a large batch for the first time
- Trying new reference images
- Experimenting with different settings
- Unsure if your configuration will produce good results
- Working with expensive/slow processing settings

❌ **Skip preview mode when:**
- You've already tested your settings
- Processing a small batch (< 5 images)
- Using proven configurations
- Time is critical

## How to Use Preview Mode

### Option 1: CLI (Command Line)

```bash
# Enable preview mode with --preview flag
python batch_colorize.py \
  --input-dir ./my_images \
  --output-dir ./colorized \
  --reference-dir ./references \
  --style "line + shadow" \
  --steps 10 \
  --preview

# The script will:
# 1. Process only the first image
# 2. Show you the result
# 3. Ask if you want to continue
# 4. Process remaining images if you approve
```

### Option 2: Python API

```python
from batch_processing import BatchProcessor, BatchConfig

# Create config with preview_mode=True
config = BatchConfig(
    input_dir="./input",
    output_dir="./output",
    reference_images=["ref1.png", "ref2.png"],
    style="line + shadow",
    num_inference_steps=10,
    preview_mode=True  # Enable preview mode
)

# Create processor and add images
processor = BatchProcessor(config)
processor.add_images([
    "page1.png",
    "page2.png",
    "page3.png"
])

# Start processing - only processes first image
processor.start_processing()

# Check if waiting for approval
if processor.is_waiting_for_preview_approval():
    # Get the preview result
    result = processor.get_preview_result()
    print(f"Preview saved to: {result['output_path']}")
    
    # Review the output image...
    # Then decide:
    
    # Option A: Approve and continue with remaining images
    processor.approve_preview()
    # Remaining images will be processed automatically
    
    # Option B: Reject and adjust settings
    processor.reject_preview()
    # Now you can modify config and try again
    config.num_inference_steps = 20
    processor.start_processing()
```

### Option 3: Gradio UI

1. Enable "Preview Mode" checkbox in the batch processing tab
2. Upload your images and configure settings
3. Click "Start Batch Processing"
4. Review the first processed image
5. Click "Approve Preview" to continue or "Reject Preview" to adjust settings

## Preview Mode Workflow

```
┌─────────────────────────────────────────┐
│  1. Enable Preview Mode                 │
│     Set preview_mode=True in config     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. Add Images to Queue                 │
│     processor.add_images([...])         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  3. Start Processing                    │
│     processor.start_processing()        │
│     → Processes ONLY first image        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  4. Review Preview Result               │
│     result = processor.get_preview_     │
│              result()                   │
│     → Check output image quality        │
└──────────────┬──────────────────────────┘
               │
               ▼
        ┌──────┴──────┐
        │             │
        ▼             ▼
┌──────────────┐  ┌──────────────┐
│  5a. APPROVE │  │  5b. REJECT  │
│  Continue    │  │  Adjust      │
│  with batch  │  │  settings    │
└──────┬───────┘  └──────┬───────┘
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  Process     │  │  Modify      │
│  remaining   │  │  config and  │
│  images      │  │  retry       │
└──────────────┘  └──────────────┘
```

## API Reference

### Check Preview Mode Status

```python
# Is preview mode enabled?
if processor.is_preview_mode():
    print("Preview mode is enabled")

# Is processor waiting for approval?
if processor.is_waiting_for_preview_approval():
    print("Waiting for user to approve/reject preview")
```

### Get Preview Result

```python
result = processor.get_preview_result()

if result:
    print(f"Input: {result['input_path']}")
    print(f"Output: {result['output_path']}")
    print(f"Status: {result['status']}")
    
    # If processing failed
    if 'error' in result:
        print(f"Error: {result['error']}")
```

### Approve Preview

```python
try:
    processor.approve_preview()
    print("Preview approved - processing remaining images")
except BatchProcessingError as e:
    print(f"Cannot approve: {e}")
```

### Reject Preview

```python
try:
    processor.reject_preview()
    print("Preview rejected - ready for settings adjustment")
    
    # Adjust settings
    config.num_inference_steps = 20
    config.top_k = 5
    
    # Try again
    processor.start_processing()
    
except BatchProcessingError as e:
    print(f"Cannot reject: {e}")
```

## Common Scenarios

### Scenario 1: Settings Too Aggressive

```python
# Initial attempt with high quality settings
config = BatchConfig(
    input_dir="./input",
    output_dir="./output",
    reference_images=["ref.png"],
    num_inference_steps=50,  # Very high
    preview_mode=True
)

processor = BatchProcessor(config)
processor.add_images(image_paths)
processor.start_processing()

# Preview takes too long or uses too much memory
if processor.is_waiting_for_preview_approval():
    processor.reject_preview()
    
    # Reduce settings
    config.num_inference_steps = 10
    processor.start_processing()
    
    # Much faster! Approve and continue
    processor.approve_preview()
```

### Scenario 2: Wrong Reference Images

```python
# Try with one set of references
config = BatchConfig(
    input_dir="./input",
    output_dir="./output",
    reference_images=["ref1.png", "ref2.png"],
    preview_mode=True
)

processor = BatchProcessor(config)
processor.add_images(image_paths)
processor.start_processing()

# Preview doesn't look good
if processor.is_waiting_for_preview_approval():
    result = processor.get_preview_result()
    # Review result['output_path']...
    
    # Not satisfied - try different references
    processor.reject_preview()
    config.reference_images = ["ref3.png", "ref4.png"]
    processor.start_processing()
    
    # Better! Approve
    processor.approve_preview()
```

### Scenario 3: Batch Testing

```python
# Test multiple configurations quickly
configs_to_test = [
    {"steps": 5, "top_k": 1},
    {"steps": 10, "top_k": 3},
    {"steps": 20, "top_k": 5},
]

for test_config in configs_to_test:
    config = BatchConfig(
        input_dir="./input",
        output_dir=f"./output_{test_config['steps']}steps",
        reference_images=["ref.png"],
        num_inference_steps=test_config['steps'],
        top_k=test_config['top_k'],
        preview_mode=True
    )
    
    processor = BatchProcessor(config)
    processor.add_images([image_paths[0]])  # Just one image
    processor.start_processing()
    
    # Review each preview
    result = processor.get_preview_result()
    print(f"Config {test_config}: {result['output_path']}")
    
    # Don't approve - just testing
    processor.reject_preview()

# After reviewing all previews, choose best config and run full batch
```

## Tips and Best Practices

### 1. Always Use Preview for New Batches

Even if you think your settings are correct, preview mode catches issues early:
- Wrong reference images
- Incorrect style mode
- Memory issues
- Path problems

### 2. Choose a Representative Preview Image

The first image in your batch should be representative:
- ✅ Typical complexity
- ✅ Average size
- ✅ Common content type
- ❌ Don't use the simplest image
- ❌ Don't use an outlier

### 3. Check Multiple Aspects

When reviewing the preview, check:
- Color accuracy
- Line preservation
- Style consistency
- Processing time
- Memory usage
- Output quality

### 4. Iterate Quickly

Don't be afraid to reject and retry:
```python
# Quick iteration loop
while not satisfied:
    processor.start_processing()
    result = processor.get_preview_result()
    
    if review_result(result):
        processor.approve_preview()
        satisfied = True
    else:
        processor.reject_preview()
        adjust_settings(config)
```

### 5. Document Your Settings

Once you find good settings, save them:
```python
# Save successful config
if processor.is_waiting_for_preview_approval():
    result = processor.get_preview_result()
    if looks_good(result):
        save_config(config, "successful_config.json")
        processor.approve_preview()
```

## Troubleshooting

### "Cannot approve preview: preview mode is not enabled"

**Problem**: Trying to approve when preview mode is disabled

**Solution**: Enable preview mode in config:
```python
config.preview_mode = True
```

### "Cannot approve preview: no preview has been processed"

**Problem**: Trying to approve before processing preview

**Solution**: Call `start_processing()` first:
```python
processor.start_processing()
# Wait for processing to complete
processor.approve_preview()
```

### Preview Never Completes

**Problem**: Preview processing hangs or takes too long

**Solution**: 
1. Check if colorization pipeline is loaded
2. Reduce `num_inference_steps`
3. Check GPU memory availability
4. Review logs for errors

### Can't Reject Preview

**Problem**: `reject_preview()` raises error

**Solution**: Ensure preview has been processed:
```python
if processor.is_waiting_for_preview_approval():
    processor.reject_preview()
```

## Performance Considerations

### Preview Mode Overhead

Preview mode adds minimal overhead:
- ✅ No extra memory usage
- ✅ No extra model loading
- ✅ Just processes one image first
- ✅ State management is lightweight

### When Preview Saves Time

Preview mode saves time when:
- Settings are wrong (catch early)
- References are incorrect (fix before batch)
- Memory issues exist (adjust before crash)
- Quality is poor (iterate quickly)

**Example**: 
- Without preview: Process 100 images with wrong settings = 2 hours wasted
- With preview: Catch issue in 1 minute, fix, then process = 1 minute + 2 hours = time saved!

## Summary

Preview mode is a powerful feature that:
- ✅ Saves time by catching issues early
- ✅ Reduces wasted resources
- ✅ Increases user confidence
- ✅ Enables rapid iteration
- ✅ Has minimal overhead

**Best Practice**: Always use preview mode for new batches or when experimenting with settings!

## See Also

- [Batch Processing Quick Start](BATCH_PROCESSOR_QUICK_START.md)
- [CLI Quick Start](CLI_QUICK_START.md)
- [Batch UI Quick Start](BATCH_UI_QUICK_START.md)
- [Preview Mode Implementation Summary](Test/PREVIEW_MODE_IMPLEMENTATION_SUMMARY.md)

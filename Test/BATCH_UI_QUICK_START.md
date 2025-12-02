# Batch Processing UI - Quick Start Guide

## Overview

The Cobra batch processing UI allows you to colorize multiple comic line art images at once using ZIP files or directories as input.

## Quick Start

### 1. Launch the Application

```bash
python app_batch.py
```

The application will open in your default web browser.

### 2. Navigate to Batch Processing Tab

Click on the **"Batch Processing"** tab at the top of the interface.

### 3. Choose Your Input Method

**Option A: ZIP File (Recommended)**
- Select "ZIP File" from the Input Mode radio buttons
- Click "Upload ZIP File"
- Choose a ZIP file containing:
  - Line art images (to be colorized)
  - Colored reference images (for style guidance)
- Click "📂 Process Input"

**Option B: Directory**
- Select "Directory" from the Input Mode radio buttons
- Enter the path to your image directory
- Optionally check "Scan subdirectories recursively"
- Click "📂 Process Input"

### 4. Review and Select References

After processing input, you'll see:
- A gallery of detected colored reference images
- Checkboxes to select which references to use
- Confidence scores for each reference

**Selection Options:**
- ✓ **Select All**: Use all detected references
- ✗ **Deselect All**: Clear all selections
- ⭐ **Auto-Select Best**: Automatically select high-confidence references

### 5. Configure Processing Settings

Adjust the following parameters:
- **Style**: Choose "line + shadow" or "line"
- **Output Directory**: Where to save results (default: `./batch_output`)
- **Random Seed**: For reproducible results (default: 0)
- **Inference Steps**: More steps = better quality (default: 10)
- **Top K References**: Number of references to use per image (default: 3)

### 6. Start Processing

Click **"✓ Confirm Selection and Start Processing"**

The system will:
- Validate your selections
- Create the batch processor
- Start colorizing images in the background

### 7. Monitor Progress

Watch the **Processing Status** section:
- **Status Table**: Shows each image's current state
- **Progress Text**: Displays completion count
- **Control Buttons**: Pause, resume, or cancel as needed

### 8. View Results

Once processing completes:
- Click **"🔄 Refresh Results"** to see colorized images
- Review the results in the gallery
- Click **"📥 Download All (ZIP)"** to package all results

## Example Workflow

### Scenario: Colorizing a Comic Chapter

1. **Prepare Your Files**
   ```
   chapter1.zip
   ├── page01_lineart.png
   ├── page02_lineart.png
   ├── page03_lineart.png
   ├── character_ref.png (colored)
   └── background_ref.png (colored)
   ```

2. **Upload ZIP**
   - Upload `chapter1.zip`
   - System detects 3 line art images and 2 colored references

3. **Select References**
   - Review the 2 detected references
   - Both show high confidence (>85%)
   - Click "✓ Select All"

4. **Configure**
   - Style: "line + shadow"
   - Seed: 42
   - Steps: 10
   - Top K: 3

5. **Process**
   - Click "Confirm Selection and Start Processing"
   - Watch progress: 1/3, 2/3, 3/3 completed

6. **Download**
   - Click "Refresh Results" to see all 3 colorized pages
   - Click "Download All (ZIP)" to get `batch_results.zip`

## Tips and Best Practices

### For Best Results

1. **Reference Images**
   - Use 2-5 high-quality colored reference images
   - References should match the style you want
   - Higher confidence references generally work better

2. **Line Art Quality**
   - Clean, clear line art works best
   - Avoid heavily shaded or textured images
   - Black and white or grayscale preferred

3. **Processing Settings**
   - Start with default settings (seed=0, steps=10, top_k=3)
   - Increase steps for higher quality (but slower processing)
   - Adjust top_k based on reference variety

### Troubleshooting

**Problem: No references detected**
- Solution: Ensure your ZIP contains colored images
- Check that images are in supported formats (PNG, JPG, JPEG, WebP)
- Try images with more color saturation

**Problem: Processing is slow**
- Solution: Reduce inference steps
- Process fewer images at once
- Use fewer reference images

**Problem: Results don't match reference style**
- Solution: Increase top_k value
- Use more similar reference images
- Try different seed values

**Problem: Out of memory errors**
- Solution: Process smaller batches
- Reduce image resolution
- Close other applications

## Keyboard Shortcuts

- **Tab**: Navigate between input fields
- **Enter**: Submit forms (when focused)
- **Space**: Toggle checkboxes (when focused)

## Advanced Features

### Auto-Select Best References

The "Auto-Select Best" button automatically selects references with:
- Confidence ≥ 70%
- High color saturation
- Diverse color palette
- Low edge density

### Pause and Resume

- **Pause**: Completes current image, then stops
- **Resume**: Continues from next unprocessed image
- **Cancel**: Stops immediately, marks remaining as cancelled

### Status Monitoring

The status table shows:
- **Pending**: Waiting to be processed
- **Processing**: Currently being colorized
- **Completed**: Successfully finished
- **Failed**: Error occurred (check logs)
- **Cancelled**: Stopped by user

## File Organization

### Input Structure

```
input/
├── line_art/
│   ├── page01.png
│   ├── page02.png
│   └── page03.png
└── references/
    ├── ref1.png
    └── ref2.png
```

### Output Structure

```
batch_output/
├── page01_colorized.png
├── page02_colorized.png
├── page03_colorized.png
└── batch_results.zip (optional)
```

## Demo Mode

To test the UI without loading the full model:

```bash
python demo_batch_ui.py
```

This provides:
- Mock data for testing
- All UI interactions
- No model loading required
- Fast startup time

## Support

For issues or questions:
1. Check the logs in the console
2. Review the status table for error messages
3. Try the demo mode to isolate UI issues
4. Refer to the main documentation

## Next Steps

- Experiment with different reference images
- Try various inference parameters
- Process larger batches
- Integrate into your workflow

Happy colorizing! 🎨

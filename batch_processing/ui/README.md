# Reference Preview and Filtering UI

This module provides Gradio UI components for previewing and filtering reference images in batch processing workflows.

## Overview

When processing ZIP files containing both line art and colored images, the system automatically classifies images and allows users to review and select which colored images to use as style references for colorization.

## Components

### ReferencePreviewGallery

Main class for managing reference image preview and selection.

```python
from batch_processing.ui import ReferencePreviewGallery

# Create gallery instance
gallery = ReferencePreviewGallery()

# Load reference images with classifications
images, choices, selected = gallery.load_references(
    reference_paths=['ref1.png', 'ref2.png'],
    classifications={
        'ref1.png': ImageType(type='colored', confidence=0.85, metrics={}),
        'ref2.png': ImageType(type='colored', confidence=0.92, metrics={})
    }
)

# Selection operations
all_selected = gallery.select_all(choices)
none_selected = gallery.deselect_all()
best_selected = gallery.auto_select_best(choices, threshold=0.7)

# Update selection
gallery.update_selection([0, 2, 4])

# Get confidence display
confidence_text = gallery.get_confidence_display([0, 2])
```

### filter_references

Function to filter reference images based on user selection.

```python
from batch_processing.ui import filter_references

all_refs = ['/path/ref1.png', '/path/ref2.png', '/path/ref3.png']
selected_indices = [0, 2]

filtered = filter_references(all_refs, selected_indices)
# Returns: ['/path/ref1.png', '/path/ref3.png']
```

### create_reference_preview_ui

Convenience function to create a complete reference preview UI with all components wired together.

```python
from batch_processing.ui import create_reference_preview_ui

# Create complete UI
components = create_reference_preview_ui()

# Access individual components
gallery = components['gallery']
checkbox_group = components['checkbox_group']
gallery_manager = components['gallery_manager']
```

## Usage in Gradio Interface

### Basic Integration

```python
import gradio as gr
from batch_processing.ui import ReferencePreviewGallery, filter_references
from batch_processing.classification.classifier import ImageClassifier
from batch_processing.io.file_handler import separate_line_art_and_references

# Initialize components
classifier = ImageClassifier()
gallery_manager = ReferencePreviewGallery()

def process_zip_upload(zip_file):
    """Handle ZIP file upload and classification."""
    # Extract and classify images
    all_images = extract_images_from_zip(zip_file)
    line_art, references, classifications = separate_line_art_and_references(
        all_images, classifier
    )
    
    # Load into gallery
    images, choices, selected = gallery_manager.load_references(
        references, classifications
    )
    
    return images, gr.update(choices=choices, value=selected)

def confirm_selection(selected_indices):
    """Filter references based on user selection."""
    filtered = filter_references(
        gallery_manager.reference_images,
        selected_indices
    )
    return f"Selected {len(filtered)} references for colorization"

# Create Gradio interface
with gr.Blocks() as demo:
    zip_upload = gr.File(label="Upload ZIP")
    
    gallery = gr.Gallery(label="Reference Images")
    checkbox_group = gr.CheckboxGroup(label="Select References")
    
    with gr.Row():
        select_all_btn = gr.Button("Select All")
        deselect_all_btn = gr.Button("Deselect All")
    
    confirm_btn = gr.Button("Confirm Selection")
    result = gr.Textbox(label="Result")
    
    # Wire up events
    zip_upload.change(
        fn=process_zip_upload,
        inputs=[zip_upload],
        outputs=[gallery, checkbox_group]
    )
    
    select_all_btn.click(
        fn=lambda choices: list(range(len(choices))),
        inputs=[checkbox_group],
        outputs=[checkbox_group]
    )
    
    deselect_all_btn.click(
        fn=lambda: [],
        outputs=[checkbox_group]
    )
    
    confirm_btn.click(
        fn=confirm_selection,
        inputs=[checkbox_group],
        outputs=[result]
    )

demo.launch()
```

### Advanced Integration with Confidence Display

```python
import gradio as gr
from batch_processing.ui import ReferencePreviewGallery

gallery_manager = ReferencePreviewGallery()

def update_confidence_display(selected_indices):
    """Update confidence information for selected images."""
    return gallery_manager.get_confidence_display(selected_indices)

with gr.Blocks() as demo:
    # ... gallery and checkbox components ...
    
    confidence_display = gr.Markdown("Select images to see confidence")
    
    # Update confidence when selection changes
    checkbox_group.change(
        fn=update_confidence_display,
        inputs=[checkbox_group],
        outputs=[confidence_display]
    )
```

## Features

### Automatic Classification Display

The gallery automatically displays classification confidence for each reference image:

```
0: character_ref.png (confidence: 92.5%)
1: background_ref.png (confidence: 87.3%)
2: color_palette.png (confidence: 95.1%)
```

### Selection Controls

- **Select All**: Select all available reference images
- **Deselect All**: Clear all selections
- **Auto-Select Best**: Automatically select only high-confidence references (default threshold: 0.7)

### Confidence Information

Detailed metrics for each selected reference:

```markdown
### Selected References Confidence:

**0. character_ref.png**
- Confidence: 92.5%
- Saturation: 0.847
- Unique Colors: 15234
- Edge Density: 0.123

**1. background_ref.png**
- Confidence: 87.3%
- Saturation: 0.765
- Unique Colors: 12456
- Edge Density: 0.089
```

## Workflow

1. **Upload ZIP**: User uploads ZIP file containing mixed images
2. **Automatic Classification**: System classifies images as line art or colored references
3. **Preview Display**: Colored references are displayed in gallery with confidence scores
4. **User Selection**: User reviews and selects/deselects references
5. **Filtering**: System filters to only use selected references for colorization
6. **Processing**: Batch processor uses filtered references to colorize line art

## Example Scenario

```python
# User uploads comic_chapter1.zip containing:
# - page01_lineart.png (line art)
# - page02_lineart.png (line art)
# - character_colored.png (colored reference)
# - background_colored.png (colored reference)
# - wrong_style.png (colored but wrong style)

# System automatically:
# 1. Classifies 2 line art images
# 2. Classifies 3 colored references
# 3. Displays 3 colored references in preview gallery

# User:
# 1. Reviews the 3 colored references
# 2. Deselects "wrong_style.png" (not matching desired style)
# 3. Confirms selection of 2 references

# System:
# 1. Filters to use only selected 2 references
# 2. Processes 2 line art images using the 2 selected references
# 3. Outputs 2 colorized pages matching the selected style
```

## Testing

Run the test suite:

```bash
uv run pytest test_reference_preview.py -v
```

Run the demo:

```bash
# Basic demo (command line)
uv run python demo_reference_preview.py

# Gradio UI demo
uv run python demo_reference_preview.py --ui
```

## API Reference

### ReferencePreviewGallery

#### Methods

- `__init__()`: Initialize the gallery
- `create_gallery_component()`: Create Gradio components
- `load_references(reference_paths, classifications)`: Load images into gallery
- `select_all(choices)`: Select all images
- `deselect_all()`: Deselect all images
- `auto_select_best(choices, threshold=0.7)`: Auto-select high-confidence images
- `update_selection(selected_indices)`: Update current selection
- `get_confidence_display(selected_indices)`: Get confidence information as markdown

#### Attributes

- `reference_images`: List of reference image paths
- `classifications`: Dictionary mapping paths to ImageType
- `selected_indices`: Set of currently selected indices

### filter_references

```python
def filter_references(
    all_reference_paths: List[str],
    selected_indices: List[int]
) -> List[str]
```

Filter reference images based on user selection.

**Parameters:**
- `all_reference_paths`: Complete list of reference image paths
- `selected_indices`: List of indices that were selected

**Returns:**
- List of selected reference image paths

**Raises:**
- `ValidationError`: If indices are invalid

### create_reference_preview_ui

```python
def create_reference_preview_ui() -> Dict[str, gr.components.Component]
```

Create a complete reference preview and filtering UI.

**Returns:**
- Dictionary mapping component names to Gradio components:
  - `gallery`: Gallery component
  - `checkbox_group`: CheckboxGroup component
  - `button_row`: Row containing control buttons
  - `confidence_display`: Markdown component for confidence info
  - `select_all_btn`: Select all button
  - `deselect_all_btn`: Deselect all button
  - `auto_select_btn`: Auto-select button
  - `gallery_manager`: ReferencePreviewGallery instance

## Requirements

- gradio
- PIL (Pillow)
- batch_processing.classification.classifier
- batch_processing.logging_config
- batch_processing.exceptions

## See Also

- [Image Classification](../classification/README.md)
- [File I/O Operations](../io/README.md)
- [Batch Processor](../processor.py)

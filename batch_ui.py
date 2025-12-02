"""
Batch processing UI components for Cobra.

This module contains the create_batch_processing_ui() function that generates
the Gradio interface for batch processing functionality.
"""

from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
import pandas as pd
from PIL import Image
import gradio as gr

# Import batch processing components
from batch_processing.config import BatchConfig
from batch_processing.processor import BatchProcessor
from batch_processing.io.zip_handler import (
    is_zip_file,
    extract_zip_file,
    cleanup_temp_directory,
    separate_line_art_and_references,
    create_output_zip
)
from batch_processing.classification.classifier import ImageClassifier
from batch_processing.ui.reference_preview import (
    ReferencePreviewGallery,
    filter_references
)
from batch_processing.core.status import ProcessingState

# Global state for batch processing
batch_processor: Optional[BatchProcessor] = None
temp_extract_dir: Optional[str] = None
classifier = ImageClassifier()
reference_gallery_manager = ReferencePreviewGallery()

# Store detected references for filtering
detected_line_art: List[str] = []
detected_references: List[str] = []
reference_classifications: Dict[str, Any] = {}


def handle_zip_upload(zip_file) -> Tuple[str, List, str, List, str]:
    """
    Handle ZIP file upload, extract images, and classify them.
    
    Args:
        zip_file: Uploaded ZIP file from Gradio
        
    Returns:
        Tuple of (status_message, gallery_images, selected_count, 
                  selected_indices, image_details)
    """
    global temp_extract_dir, detected_line_art, detected_references, reference_classifications
    
    if zip_file is None:
        return "Please upload a ZIP file", [], "0 selected", [], "No images loaded"
    
    try:
        # Clean up previous extraction if exists
        if temp_extract_dir and Path(temp_extract_dir).exists():
            cleanup_temp_directory(temp_extract_dir)
        
        # Extract ZIP file
        temp_extract_dir, all_images = extract_zip_file(zip_file.name)
        
        if not all_images:
            return "No images found in ZIP file", [], "0 selected", [], "No images found"
        
        # Classify images
        line_art, references = separate_line_art_and_references(all_images, classifier)
        
        # Get classifications for references
        reference_classifications = {
            path: classifier.classify(path) for path in references
        }
        
        # Sort references by confidence (descending - best first)
        sorted_refs = sorted(
            references,
            key=lambda x: reference_classifications.get(x).confidence if reference_classifications.get(x) else 0,
            reverse=True
        )
        
        detected_line_art = line_art
        detected_references = sorted_refs  # Store sorted references
        
        # Load images for gallery with labels showing confidence
        images_with_labels = []
        for ref in sorted_refs:
            img = Image.open(ref)
            classification = reference_classifications.get(ref)
            confidence = classification.confidence if classification else 0
            
            # Add label with filename and confidence
            filename = Path(ref).name
            label = f"{filename}\n✓ {confidence:.0%} confidence"
            images_with_labels.append((img, label))
        
        # Select all by default
        default_selection = list(range(len(sorted_refs)))
        
        # Generate details text
        details_text = f"""
**Found {len(sorted_refs)} colored reference images**

✓ Sorted by confidence (best first)
✓ All images selected by default

**Click images to toggle selection**

**Classification Criteria:**
- High color saturation (>15%)
- Diverse color palette (>1000 colors)
- Lower edge density (<30%)
"""
        
        status_msg = (
            f"✓ Extracted {len(all_images)} images from ZIP\n"
            f"📄 Found {len(line_art)} line art images to colorize\n"
            f"🎨 Found {len(sorted_refs)} colored references (sorted by confidence)"
        )
        
        selected_count_text = f"{len(sorted_refs)} selected (all)"
        
        return status_msg, images_with_labels, selected_count_text, default_selection, details_text
        
    except Exception as e:
        return f"Error processing ZIP file: {str(e)}", [], "0 selected", [], f"Error: {str(e)}"


def handle_directory_input(directory_path: str, recursive: bool) -> Tuple[str, int]:
    """
    Handle directory path input and scan for images.
    
    Args:
        directory_path: Path to directory containing images
        recursive: Whether to scan recursively
        
    Returns:
        Tuple of (status_message, image_count)
    """
    global detected_line_art
    
    if not directory_path:
        return "Please enter a directory path", 0
    
    dir_path = Path(directory_path)
    if not dir_path.exists():
        return f"Directory does not exist: {directory_path}", 0
    
    if not dir_path.is_dir():
        return f"Path is not a directory: {directory_path}", 0
    
    try:
        # Scan for images
        from batch_processing.io.file_handler import scan_directory
        
        image_files = scan_directory(directory_path, recursive=recursive)
        detected_line_art = image_files
        
        status_msg = f"✓ Found {len(image_files)} images in directory"
        if recursive:
            status_msg += " (recursive scan)"
        
        return status_msg, len(image_files)
        
    except Exception as e:
        return f"Error scanning directory: {str(e)}", 0


def start_batch_processing(
    style: str,
    seed: int,
    num_inference_steps: int,
    top_k: int,
    output_dir: str,
    selected_reference_names: List[str]
) -> str:
    """
    Start batch processing with selected configuration.
    
    Args:
        style: Style mode ("line" or "line + shadow")
        seed: Random seed
        num_inference_steps: Number of inference steps
        top_k: Top K references to use
        output_dir: Output directory for results
        selected_reference_names: Selected reference image filenames
        
    Returns:
        Status message
    """
    global batch_processor, detected_line_art, detected_references
    
    if not detected_line_art:
        return "❌ No images to process. Please upload a ZIP file or select a directory first."
    
    if not output_dir:
        output_dir = "./batch_output"
    
    try:
        # Map selected filenames back to full paths
        if detected_references and selected_reference_names:
            selected_references = [
                ref for ref in detected_references 
                if Path(ref).name in selected_reference_names
            ]
        else:
            selected_references = []
        
        if not selected_references:
            return "❌ No reference images selected. Please select at least one reference image."
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Use temp extraction directory or first image's directory as input_dir
        # (required by BatchConfig but not actually used when adding images directly)
        input_dir_placeholder = str(Path(detected_line_art[0]).parent) if detected_line_art else "."
        
        # Create batch configuration
        config = BatchConfig(
            input_dir=input_dir_placeholder,
            output_dir=output_dir,
            reference_images=selected_references,
            style=style,
            seed=seed,
            num_inference_steps=num_inference_steps,
            top_k=top_k,
            recursive=False,
            overwrite=False,
            preview_mode=False,
            max_concurrent=1
        )
        
        # Create batch processor
        batch_processor = BatchProcessor(config)
        
        # Add images to queue
        batch_processor.add_images(detected_line_art)
        
        # Start processing in a separate thread to avoid blocking UI
        import threading
        
        def process_thread():
            try:
                batch_processor.start_processing()
            except Exception as e:
                print(f"Batch processing error: {e}")
        
        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()
        
        return f"✓ Started batch processing {len(detected_line_art)} images with {len(selected_references)} references"
        
    except Exception as e:
        return f"❌ Error starting batch processing: {str(e)}"


def get_batch_status() -> Tuple[pd.DataFrame, str, float]:
    """
    Get current batch processing status.
    
    Returns:
        Tuple of (status_dataframe, progress_text, progress_value)
    """
    global batch_processor
    
    if batch_processor is None:
        empty_df = pd.DataFrame(columns=["Image", "Status", "Progress", "Output"])
        return empty_df, "No batch processing active", 0.0
    
    try:
        # Get status from processor
        status = batch_processor.get_status()
        summary = status["summary"]
        
        # Get all statuses
        all_statuses = batch_processor.status_tracker.get_all_statuses()
        
        # Create dataframe
        rows = []
        for image_id, img_status in all_statuses.items():
            # Find the queue item to get the filename
            filename = "Unknown"
            for item in [batch_processor.queue.peek()]:
                if item and item.id == image_id:
                    filename = Path(item.input_path).name
                    break
            
            rows.append({
                "Image": filename,
                "Status": img_status.state,
                "Progress": f"{img_status.progress:.0f}%" if hasattr(img_status, 'progress') else "N/A",
                "Output": Path(img_status.output_path).name if img_status.output_path else "N/A"
            })
        
        df = pd.DataFrame(rows)
        
        # Create progress text
        total = summary.total
        completed = summary.completed
        failed = summary.failed
        
        progress_text = f"Progress: {completed}/{total} completed"
        if failed > 0:
            progress_text += f", {failed} failed"
        
        # Calculate progress value
        progress_value = (completed / total) if total > 0 else 0.0
        
        return df, progress_text, progress_value
        
    except Exception as e:
        empty_df = pd.DataFrame(columns=["Image", "Status", "Progress", "Output"])
        return empty_df, f"Error getting status: {str(e)}", 0.0


def pause_batch() -> str:
    """Pause batch processing."""
    global batch_processor
    
    if batch_processor is None:
        return "No batch processing active"
    
    batch_processor.pause_processing()
    return "⏸️ Batch processing paused"


def resume_batch() -> str:
    """Resume batch processing."""
    global batch_processor
    
    if batch_processor is None:
        return "No batch processing active"
    
    batch_processor.resume_processing()
    return "▶️ Batch processing resumed"


def cancel_batch() -> str:
    """Cancel batch processing."""
    global batch_processor
    
    if batch_processor is None:
        return "No batch processing active"
    
    batch_processor.cancel_processing()
    return "⏹️ Batch processing cancelled"


def get_batch_results() -> List[Image.Image]:
    """
    Get all processed images for display in results gallery.
    
    Returns:
        List of PIL Images
    """
    global batch_processor
    
    if batch_processor is None:
        return []
    
    try:
        # Get all completed images
        all_statuses = batch_processor.status_tracker.get_all_statuses()
        
        result_images = []
        for img_status in all_statuses.values():
            if img_status.state == ProcessingState.COMPLETED.value and img_status.output_path:
                if Path(img_status.output_path).exists():
                    result_images.append(Image.open(img_status.output_path))
        
        return result_images
        
    except Exception as e:
        print(f"Error getting batch results: {e}")
        return []


def create_batch_processing_ui():
    """Create the batch processing UI components."""
    # Add custom CSS for better gallery display
    gr.HTML("""
    <style>
    #reference_gallery .grid-wrap {
        gap: 1rem;
    }
    #reference_gallery .thumbnail-item {
        position: relative;
        border: 3px solid transparent;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    #reference_gallery .thumbnail-item:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    #reference_gallery .thumbnail-item.selected {
        border-color: #10b981;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.3);
    }
    </style>
    """)
    
    gr.Markdown("### Batch Image Colorization")
    gr.Markdown(
        """
        **📋 Batch Processing Workflow:**
        
        1. **Upload Input**: Choose a ZIP file containing your images or select a directory
        2. **Review References**: The system will automatically detect colored reference images
        3. **Select References**: Choose which reference images to use for colorization
        4. **Configure Settings**: Set your colorization parameters (style, seed, steps, etc.)
        5. **Start Processing**: Click to begin batch colorization
        6. **Monitor Progress**: Watch the status table for real-time updates
        7. **View Results**: See all colorized images in the results gallery
        
        💡 **Tip**: Upload a ZIP file with both line art and colored images for automatic reference detection!
        """
    )
    
    # Input Selection
    with gr.Row():
        with gr.Column():
            gr.Markdown("#### 📂 Input Selection")
            
            # Batch mode toggle
            batch_mode = gr.Radio(
                choices=["ZIP File", "Directory"],
                value="ZIP File",
                label="Input Mode",
                info="Choose how to provide input images"
            )
            
            # ZIP file upload
            zip_upload = gr.File(
                label="Upload ZIP File",
                file_types=[".zip"],
                type="filepath",
                visible=True
            )
            
            # Directory path input
            dir_path = gr.Textbox(
                label="Directory Path",
                placeholder="/path/to/images",
                visible=False
            )
            
            # Recursive scanning checkbox
            recursive_scan = gr.Checkbox(
                label="Scan subdirectories recursively",
                value=False,
                visible=False
            )
            
            # Process input button
            process_input_btn = gr.Button("📂 Process Input", variant="primary")
            
            # Status message
            input_status = gr.Textbox(
                label="Status",
                interactive=False,
                lines=3
            )
        
        with gr.Column():
            gr.Markdown("#### ⚙️ Processing Configuration")
            
            # Style selection
            batch_style = gr.Dropdown(
                label="Style",
                choices=["line + shadow", "line"],
                value="line + shadow"
            )
            
            # Output directory
            output_dir = gr.Textbox(
                label="Output Directory",
                value="./batch_output",
                placeholder="/path/to/output"
            )
            
            # Inference parameters
            batch_seed = gr.Slider(
                label="Random Seed",
                minimum=0,
                maximum=100000,
                value=0,
                step=1
            )
            
            batch_steps = gr.Slider(
                label="Inference Steps",
                minimum=1,
                maximum=100,
                value=10,
                step=1
            )
            
            batch_top_k = gr.Slider(
                label="Top K References",
                minimum=1,
                maximum=50,
                value=3,
                step=1
            )
    
    # Reference preview integration - Improved UI
    gr.Markdown("---")
    gr.Markdown("### 🎨 Reference Image Preview and Selection")
    gr.Markdown(
        """
        **Click on images to select/deselect them for colorization.**
        
        💡 Hover over images to see why they were classified as colored references.
        """
    )
    
    with gr.Row():
        with gr.Column(scale=3):
            # Reference gallery with selection and checkboxes
            reference_gallery = gr.Gallery(
                label="📸 Detected Reference Images (Sorted by Confidence - Best First)",
                show_label=True,
                elem_id="reference_gallery",
                columns=4,
                rows=2,
                height="auto",
                object_fit="contain",
                selected_index=None,
                allow_preview=True,
                show_download_button=False,
                show_share_button=False
            )
            
            gr.Markdown(
                """
                💡 **How to select:**
                - ✅ Click on an image to toggle selection
                - 🟢 Selected images have green checkmark
                - ⚪ Unselected images are dimmed
                - Images are sorted by confidence (best quality first)
                """
            )
        
        with gr.Column(scale=1):
            # Info panel
            gr.Markdown("#### Selection Info")
            selected_count = gr.Textbox(
                label="Selected References",
                value="0 selected",
                interactive=False
            )
            
            # Image details on hover/click
            image_details = gr.Markdown(
                """
                **Click an image to see details:**
                - Filename
                - Color saturation
                - Unique colors
                - Edge density
                - Classification confidence
                """
            )
            
            # Quick action buttons
            gr.Markdown("#### Quick Actions")
            select_all_btn = gr.Button("✓ Select All", size="sm", variant="secondary")
            deselect_all_btn = gr.Button("✗ Deselect All", size="sm", variant="secondary")
    
    # Hidden state to track selected indices
    selected_indices_state = gr.State([])
    
    # Confirmation button
    with gr.Row():
        confirm_refs_btn = gr.Button(
            "✓ Start Processing with Selected References",
            variant="primary",
            size="lg"
        )
    
    # Batch status display
    gr.Markdown("---")
    gr.Markdown("### 📊 Processing Status")
    
    with gr.Row():
        # Status table
        status_table = gr.Dataframe(
            headers=["Image", "Status", "Progress", "Output"],
            datatype=["str", "str", "str", "str"],
            label="Batch Status",
            interactive=False
        )
    
    with gr.Row():
        # Progress text
        progress_text = gr.Textbox(
            label="Progress",
            value="No batch processing active",
            interactive=False
        )
    
    with gr.Row():
        # Control buttons
        pause_btn = gr.Button("⏸️ Pause", size="sm")
        resume_btn = gr.Button("▶️ Resume", size="sm")
        cancel_btn = gr.Button("⏹️ Cancel", size="sm")
        refresh_status_btn = gr.Button("🔄 Refresh Status", size="sm")
    
    # Batch results gallery
    gr.Markdown("---")
    gr.Markdown("### 🖼️ Batch Results")
    
    with gr.Row():
        results_gallery = gr.Gallery(
            label="Processed Images",
            show_label=True,
            elem_id="results_gallery",
            columns=4,
            rows=3,
            height="auto",
            object_fit="contain"
        )
    
    with gr.Row():
        refresh_results_btn = gr.Button("🔄 Refresh Results", size="sm")
        download_all_btn = gr.Button("📥 Download All (ZIP)", size="sm")
    
    # Wire up batch processing workflow
    
    # Toggle visibility based on batch mode
    def update_input_visibility(mode):
        if mode == "ZIP File":
            return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
        else:  # Directory
            return gr.update(visible=False), gr.update(visible=True), gr.update(visible=True)
    
    batch_mode.change(
        fn=update_input_visibility,
        inputs=[batch_mode],
        outputs=[zip_upload, dir_path, recursive_scan]
    )
    
    # Process ZIP upload
    def process_zip_wrapper(zip_file):
        return handle_zip_upload(zip_file)
    
    # Process directory input
    def process_dir_wrapper(dir_path, recursive):
        status_msg, count = handle_directory_input(dir_path, recursive)
        # Return empty values for gallery components
        return status_msg, [], [], [], ""
    
    # Connect process input button
    def process_input_handler(mode, zip_file, dir_path, recursive):
        if mode == "ZIP File":
            status, images, sel_count, sel_indices, details = handle_zip_upload(zip_file)
            return status, images, sel_count, sel_indices, details
        else:
            status, count = handle_directory_input(dir_path, recursive)
            return status, [], "0 selected", [], "No images loaded"
    
    process_input_btn.click(
        fn=process_input_handler,
        inputs=[batch_mode, zip_upload, dir_path, recursive_scan],
        outputs=[input_status, reference_gallery, selected_count, selected_indices_state, image_details]
    )
    
    # Handle gallery selection (click to toggle)
    def handle_gallery_select(evt: gr.SelectData, current_selection):
        """Toggle selection when clicking on an image."""
        global detected_references, reference_classifications
        
        selected_idx = evt.index
        
        if selected_idx is None or not detected_references:
            return current_selection, f"{len(current_selection) if current_selection else 0} selected", "Click an image to see details"
        
        # Toggle selection
        new_selection = current_selection.copy() if current_selection else []
        action = "deselected"
        if selected_idx in new_selection:
            new_selection.remove(selected_idx)
            action = "deselected"
        else:
            new_selection.append(selected_idx)
            action = "selected"
        
        # Get details for clicked image
        if selected_idx < len(detected_references):
            ref_path = detected_references[selected_idx]
            ref_name = Path(ref_path).name
            classification = reference_classifications.get(ref_path)
            
            if classification:
                metrics = classification.metrics
                
                # Create visual status indicator
                status_icon = "🟢 SELECTED" if selected_idx in new_selection else "⚪ NOT SELECTED"
                
                # Calculate quality score
                quality_checks = [
                    metrics.get('saturation', 0) > 0.15,
                    metrics.get('color_count', 0) > 1000,
                    metrics.get('edge_density', 0) < 0.3
                ]
                quality_score = sum(quality_checks)
                quality_rating = "⭐" * quality_score + "☆" * (3 - quality_score)
                
                details = f"""
### {ref_name}

**Status:** {status_icon}
**Quality:** {quality_rating} ({quality_score}/3 criteria met)
**Confidence:** {classification.confidence:.1%}

---

**📊 Classification Metrics:**

| Metric | Value | Status |
|--------|-------|--------|
| Color Saturation | {metrics.get('saturation', 0):.1%} | {'✅ Pass' if metrics.get('saturation', 0) > 0.15 else '❌ Fail'} (>15%) |
| Unique Colors | {metrics.get('color_count', 0):,} | {'✅ Pass' if metrics.get('color_count', 0) > 1000 else '❌ Fail'} (>1000) |
| Edge Density | {metrics.get('edge_density', 0):.1%} | {'✅ Pass' if metrics.get('edge_density', 0) < 0.3 else '❌ Fail'} (<30%) |

---

**💡 Why this is a good reference:**
- {'✅' if metrics.get('saturation', 0) > 0.15 else '⚠️'} Rich, vibrant colors
- {'✅' if metrics.get('color_count', 0) > 1000 else '⚠️'} Diverse color palette
- {'✅' if metrics.get('edge_density', 0) < 0.3 else '⚠️'} Filled areas (not just lines)

**Action:** Just {action} this image
"""
            else:
                details = f"**{ref_name}**\n\nNo classification data available."
        else:
            details = "Click an image to see details"
        
        # Create count text with percentage
        count_text = f"{len(new_selection)}/{len(detected_references)} selected"
        if detected_references:
            percentage = (len(new_selection) / len(detected_references)) * 100
            count_text += f" ({percentage:.0f}%)"
        
        return new_selection, count_text, details
    
    reference_gallery.select(
        fn=handle_gallery_select,
        inputs=[selected_indices_state],
        outputs=[selected_indices_state, selected_count, image_details]
    )
    
    # Connect selection buttons
    def select_all_handler():
        global detected_references
        if detected_references:
            all_indices = list(range(len(detected_references)))
            return all_indices, f"{len(all_indices)} selected (all)", "All images selected"
        return [], "0 selected", "No images available"
    
    def deselect_all_handler():
        return [], "0 selected", "All images deselected"
    
    select_all_btn.click(
        fn=select_all_handler,
        outputs=[selected_indices_state, selected_count, image_details]
    )
    
    deselect_all_btn.click(
        fn=deselect_all_handler,
        outputs=[selected_indices_state, selected_count, image_details]
    )
    
    # Connect start processing button
    def start_processing_wrapper(style, seed, steps, top_k, output_dir, selected_indices):
        """Wrapper to convert indices to filenames for processing."""
        global detected_references
        
        if not selected_indices:
            return "❌ No reference images selected. Please select at least one reference image."
        
        # Convert indices to filenames
        selected_names = [Path(detected_references[i]).name for i in selected_indices if i < len(detected_references)]
        
        return start_batch_processing(style, seed, steps, top_k, output_dir, selected_names)
    
    confirm_refs_btn.click(
        fn=start_processing_wrapper,
        inputs=[
            batch_style,
            batch_seed,
            batch_steps,
            batch_top_k,
            output_dir,
            selected_indices_state
        ],
        outputs=[progress_text]
    )
    
    # Connect control buttons
    pause_btn.click(fn=pause_batch, outputs=[progress_text])
    resume_btn.click(fn=resume_batch, outputs=[progress_text])
    cancel_btn.click(fn=cancel_batch, outputs=[progress_text])
    
    # Connect refresh buttons
    refresh_status_btn.click(
        fn=lambda: get_batch_status()[:2],  # Only return dataframe and text, not progress value
        outputs=[status_table, progress_text]
    )
    
    refresh_results_btn.click(
        fn=get_batch_results,
        outputs=[results_gallery]
    )
    
    # Download all as ZIP
    def create_results_zip():
        global batch_processor
        if batch_processor is None:
            return "No batch processing results available"
        
        try:
            zip_path = create_output_zip(
                output_dir=batch_processor.config.output_dir,
                zip_name="batch_results",
                metadata={
                    "style": batch_processor.config.style,
                    "seed": batch_processor.config.seed,
                    "steps": batch_processor.config.num_inference_steps,
                    "top_k": batch_processor.config.top_k
                }
            )
            return f"✓ Created ZIP file: {zip_path}"
        except Exception as e:
            return f"❌ Error creating ZIP: {str(e)}"
    
    download_all_btn.click(
        fn=create_results_zip,
        outputs=[progress_text]
    )

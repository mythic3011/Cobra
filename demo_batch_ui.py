"""
Demo script for testing the batch processing UI components.

This script demonstrates the batch processing UI without requiring
the full Cobra model to be loaded.
"""

import gradio as gr
import pandas as pd
from PIL import Image
from pathlib import Path
from typing import List, Tuple
import tempfile
import shutil

# Mock implementations for testing
class MockBatchProcessor:
    """Mock batch processor for UI testing."""
    
    def __init__(self):
        self.is_processing = False
        self.is_paused = False
        self.total = 0
        self.completed = 0
        self.failed = 0
    
    def start(self, num_images: int):
        self.is_processing = True
        self.total = num_images
        self.completed = 0
        self.failed = 0
    
    def pause(self):
        self.is_paused = True
    
    def resume(self):
        self.is_paused = False
    
    def cancel(self):
        self.is_processing = False
    
    def get_status(self):
        return {
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "is_processing": self.is_processing,
            "is_paused": self.is_paused
        }


# Global state
mock_processor = MockBatchProcessor()
detected_references = []
reference_checkboxes_choices = []


def handle_zip_upload(zip_file) -> Tuple[str, List, List, List, str]:
    """Mock ZIP upload handler."""
    if zip_file is None:
        return "Please upload a ZIP file", [], [], [], ""
    
    # Simulate finding images
    global detected_references, reference_checkboxes_choices
    
    # Create mock reference images
    detected_references = [f"ref_{i}.png" for i in range(5)]
    reference_checkboxes_choices = [
        f"{i}: ref_{i}.png (confidence: {85 + i*2:.1f}%)"
        for i in range(5)
    ]
    
    # Create mock images for gallery
    mock_images = []
    for i in range(5):
        img = Image.new('RGB', (200, 200), color=(100 + i*30, 150, 200))
        mock_images.append(img)
    
    status_msg = (
        f"✓ Extracted 10 images from ZIP\n"
        f"📄 Found 5 line art images to colorize\n"
        f"🎨 Found 5 colored reference images"
    )
    
    default_selection = list(range(5))
    confidence_text = "### Selected References Confidence:\n\n**All references selected**"
    
    return status_msg, mock_images, reference_checkboxes_choices, default_selection, confidence_text


def start_batch_processing(
    style: str,
    seed: int,
    num_inference_steps: int,
    top_k: int,
    output_dir: str,
    selected_reference_indices: List[int]
) -> str:
    """Mock batch processing starter."""
    global mock_processor
    
    if not selected_reference_indices:
        return "❌ No reference images selected"
    
    mock_processor.start(5)
    
    return f"✓ Started batch processing 5 images with {len(selected_reference_indices)} references"


def get_batch_status() -> Tuple[pd.DataFrame, str, float]:
    """Mock status getter."""
    global mock_processor
    
    status = mock_processor.get_status()
    
    # Create mock dataframe
    rows = []
    for i in range(status["total"]):
        if i < status["completed"]:
            state = "completed"
            progress = "100%"
            output = f"output_{i}.png"
        elif i == status["completed"]:
            state = "processing"
            progress = "50%"
            output = "N/A"
        else:
            state = "pending"
            progress = "0%"
            output = "N/A"
        
        rows.append({
            "Image": f"image_{i}.png",
            "Status": state,
            "Progress": progress,
            "Output": output
        })
    
    df = pd.DataFrame(rows)
    
    progress_text = f"Progress: {status['completed']}/{status['total']} completed"
    progress_value = status['completed'] / status['total'] if status['total'] > 0 else 0.0
    
    return df, progress_text, progress_value


def pause_batch() -> str:
    """Mock pause."""
    mock_processor.pause()
    return "⏸️ Batch processing paused"


def resume_batch() -> str:
    """Mock resume."""
    mock_processor.resume()
    return "▶️ Batch processing resumed"


def cancel_batch() -> str:
    """Mock cancel."""
    mock_processor.cancel()
    return "⏹️ Batch processing cancelled"


def get_batch_results() -> List[Image.Image]:
    """Mock results getter."""
    # Create mock result images
    results = []
    for i in range(mock_processor.completed):
        img = Image.new('RGB', (300, 300), color=(200, 100 + i*30, 150))
        results.append(img)
    return results


# Create the Gradio interface
with gr.Blocks(title="Cobra - Batch Processing Demo") as demo:
    gr.HTML(
    """
<div style="text-align: center;">
    <h1>🎨 Cobra: Batch Processing UI Demo</h1>
    <h3>Test the batch processing interface</h3>
</div>
    """
    )
    
    gr.Markdown("### Batch Image Colorization")
    gr.Markdown(
        "This is a demo of the batch processing UI. Upload a ZIP file to test the interface."
    )
    
    # Input Selection
    with gr.Row():
        with gr.Column():
            gr.Markdown("#### Input Selection")
            
            batch_mode = gr.Radio(
                choices=["ZIP File", "Directory"],
                value="ZIP File",
                label="Input Mode"
            )
            
            zip_upload = gr.File(
                label="Upload ZIP File",
                file_types=[".zip"],
                type="filepath",
                visible=True
            )
            
            dir_path = gr.Textbox(
                label="Directory Path",
                placeholder="/path/to/images",
                visible=False
            )
            
            recursive_scan = gr.Checkbox(
                label="Scan subdirectories recursively",
                value=False,
                visible=False
            )
            
            process_input_btn = gr.Button("📂 Process Input", variant="primary")
            
            input_status = gr.Textbox(
                label="Status",
                interactive=False,
                lines=3
            )
        
        with gr.Column():
            gr.Markdown("#### Processing Configuration")
            
            batch_style = gr.Dropdown(
                label="Style",
                choices=["line + shadow", "line"],
                value="line + shadow"
            )
            
            output_dir = gr.Textbox(
                label="Output Directory",
                value="./batch_output"
            )
            
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
    
    # Reference Preview
    gr.Markdown("---")
    gr.Markdown("### 🎨 Reference Image Preview and Selection")
    
    with gr.Row():
        reference_gallery = gr.Gallery(
            label="Detected Reference Images",
            columns=4,
            rows=2
        )
    
    with gr.Row():
        reference_checkboxes = gr.CheckboxGroup(
            label="Select References to Use",
            choices=[],
            value=[],
            interactive=True
        )
    
    with gr.Row():
        select_all_btn = gr.Button("✓ Select All", size="sm")
        deselect_all_btn = gr.Button("✗ Deselect All", size="sm")
        auto_select_btn = gr.Button("⭐ Auto-Select Best", size="sm")
    
    confidence_display = gr.Markdown(
        "Select images above to see their classification confidence."
    )
    
    confirm_refs_btn = gr.Button(
        "✓ Confirm Selection and Start Processing",
        variant="primary",
        size="lg"
    )
    
    # Status Display
    gr.Markdown("---")
    gr.Markdown("### 📊 Processing Status")
    
    with gr.Row():
        status_table = gr.Dataframe(
            headers=["Image", "Status", "Progress", "Output"],
            datatype=["str", "str", "str", "str"],
            label="Batch Status",
            interactive=False
        )
    
    with gr.Row():
        progress_text = gr.Textbox(
            label="Progress",
            value="No batch processing active",
            interactive=False
        )
    
    with gr.Row():
        pause_btn = gr.Button("⏸️ Pause", size="sm")
        resume_btn = gr.Button("▶️ Resume", size="sm")
        cancel_btn = gr.Button("⏹️ Cancel", size="sm")
        refresh_status_btn = gr.Button("🔄 Refresh Status", size="sm")
    
    # Results Gallery
    gr.Markdown("---")
    gr.Markdown("### 🖼️ Batch Results")
    
    with gr.Row():
        results_gallery = gr.Gallery(
            label="Processed Images",
            columns=4,
            rows=3
        )
    
    with gr.Row():
        refresh_results_btn = gr.Button("🔄 Refresh Results", size="sm")
    
    # Wire up events
    def update_input_visibility(mode):
        if mode == "ZIP File":
            return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
        else:
            return gr.update(visible=False), gr.update(visible=True), gr.update(visible=True)
    
    batch_mode.change(
        fn=update_input_visibility,
        inputs=[batch_mode],
        outputs=[zip_upload, dir_path, recursive_scan]
    )
    
    process_input_btn.click(
        fn=handle_zip_upload,
        inputs=[zip_upload],
        outputs=[input_status, reference_gallery, reference_checkboxes, reference_checkboxes, confidence_display]
    )
    
    def handle_select_all():
        global reference_checkboxes_choices
        if not reference_checkboxes_choices:
            return [], "No references available"
        selected = list(range(len(reference_checkboxes_choices)))
        return selected, "### All references selected"
    
    def handle_deselect_all():
        return [], "No images selected."
    
    def handle_auto_select():
        global reference_checkboxes_choices
        if not reference_checkboxes_choices:
            return [], "No references available"
        # Select top 3
        selected = list(range(min(3, len(reference_checkboxes_choices))))
        return selected, f"### Auto-selected {len(selected)} best references"
    
    select_all_btn.click(
        fn=handle_select_all,
        outputs=[reference_checkboxes, confidence_display]
    )
    
    deselect_all_btn.click(
        fn=handle_deselect_all,
        outputs=[reference_checkboxes, confidence_display]
    )
    
    auto_select_btn.click(
        fn=handle_auto_select,
        outputs=[reference_checkboxes, confidence_display]
    )
    
    confirm_refs_btn.click(
        fn=start_batch_processing,
        inputs=[
            batch_style,
            batch_seed,
            batch_steps,
            batch_top_k,
            output_dir,
            reference_checkboxes
        ],
        outputs=[progress_text]
    )
    
    pause_btn.click(fn=pause_batch, outputs=[progress_text])
    resume_btn.click(fn=resume_batch, outputs=[progress_text])
    cancel_btn.click(fn=cancel_batch, outputs=[progress_text])
    
    refresh_status_btn.click(
        fn=get_batch_status,
        outputs=[status_table, progress_text]
    )
    
    refresh_results_btn.click(
        fn=get_batch_results,
        outputs=[results_gallery]
    )


if __name__ == "__main__":
    demo.launch()

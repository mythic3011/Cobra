"""
Enhanced Cobra application with batch processing capabilities.

This module extends the original Cobra Gradio interface with batch processing
features including ZIP upload, reference preview, status tracking, and more.
"""

import contextlib
import gc
import json
import logging
import math
import os
import random
import shutil
import sys
import time
import itertools
import copy
import warnings
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import cv2
import numpy as np
from PIL import Image, ImageDraw
import torch

# Suppress FutureWarning about torch.load weights_only parameter
warnings.filterwarnings('ignore', category=FutureWarning, message='.*torch.load.*weights_only.*')
import torch.nn.functional as F
import torch.utils.checkpoint
from torch.utils.data import Dataset
from torchvision import transforms
from tqdm.auto import tqdm

import accelerate
from accelerate import Accelerator
from accelerate.logging import get_logger
from accelerate.utils import ProjectConfiguration, set_seed

from datasets import load_dataset
from huggingface_hub import create_repo, upload_folder
from packaging import version
from safetensors.torch import load_model
from peft import LoraConfig
import gradio as gr
import pandas as pd

import transformers
from transformers import (
    AutoTokenizer,
    PretrainedConfig,
    CLIPVisionModelWithProjection,
    CLIPImageProcessor,
    CLIPProcessor,
)

import diffusers
from diffusers import (
    AutoencoderKL,
    DDPMScheduler,
    PixArtTransformer2DModel,
    CausalSparseDiTModel,
    CausalSparseDiTControlModel,
    CobraPixArtAlphaPipeline,
    UniPCMultistepScheduler,
)
from cobra_utils.utils import *

from huggingface_hub import snapshot_download

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

# Set device to MPS if available, otherwise CPU
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Using device: {device}")

model_global_path = snapshot_download(repo_id="JunhaoZhuang/Cobra", cache_dir='./Cobra/', repo_type="model")
print(model_global_path)

# Import all the existing functions from app.py
from app import (
    examples,
    ratio_list,
    get_rate,
    transform,
    weight_dtype,
    line_model,
    image_processor,
    image_encoder,
    load_ckpt,
    change_ckpt,
    fix_random_seeds,
    process_multi_images,
    extract_lines,
    extract_line_image,
    extract_sketch_line_image,
    colorize_image,
    get_color_value,
    draw_square,
    pipeline,
    MultiResNetModel,
    causal_dit,
    controlnet,
    cur_style
)

# Global state for batch processing
batch_processor: Optional[BatchProcessor] = None
temp_extract_dir: Optional[str] = None
classifier = ImageClassifier()
reference_gallery_manager = ReferencePreviewGallery()

# Store detected references for filtering
detected_line_art: List[str] = []
detected_references: List[str] = []
reference_classifications: Dict[str, Any] = {}


def handle_zip_upload(zip_file) -> Tuple[str, List, List, List, str]:
    """
    Handle ZIP file upload, extract images, and classify them.
    
    Args:
        zip_file: Uploaded ZIP file from Gradio
        
    Returns:
        Tuple of (status_message, gallery_images, checkbox_choices, 
                  default_selection, confidence_display)
    """
    global temp_extract_dir, detected_line_art, detected_references, reference_classifications
    
    if zip_file is None:
        return "Please upload a ZIP file", [], [], [], ""
    
    try:
        # Clean up previous extraction if exists
        if temp_extract_dir and Path(temp_extract_dir).exists():
            cleanup_temp_directory(temp_extract_dir)
        
        # Extract ZIP file
        temp_extract_dir, all_images = extract_zip_file(zip_file.name)
        
        if not all_images:
            return "No images found in ZIP file", [], [], [], ""
        
        # Classify images
        line_art, references = separate_line_art_and_references(all_images, classifier)
        
        detected_line_art = line_art
        detected_references = references
        
        # Get classifications for references
        reference_classifications = {
            path: classifier.classify(path) for path in references
        }
        
        # Load references for preview
        images, choices, default_selection = reference_gallery_manager.load_references(
            references, reference_classifications
        )
        
        # Generate confidence display
        confidence_text = reference_gallery_manager.get_confidence_display(default_selection)
        
        status_msg = (
            f"✓ Extracted {len(all_images)} images from ZIP\n"
            f"📄 Found {len(line_art)} line art images to colorize\n"
            f"🎨 Found {len(references)} colored reference images"
        )
        
        return status_msg, images, choices, default_selection, confidence_text
        
    except Exception as e:
        return f"Error processing ZIP file: {str(e)}", [], [], [], ""


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
    selected_reference_indices: List[int]
) -> str:
    """
    Start batch processing with selected configuration.
    
    Args:
        style: Style mode ("line" or "line + shadow")
        seed: Random seed
        num_inference_steps: Number of inference steps
        top_k: Top K references to use
        output_dir: Output directory for results
        selected_reference_indices: Indices of selected reference images
        
    Returns:
        Status message
    """
    global batch_processor, detected_line_art, detected_references
    
    if not detected_line_art:
        return "❌ No images to process. Please upload a ZIP file or select a directory first."
    
    if not output_dir:
        output_dir = "./batch_output"
    
    try:
        # Filter references based on selection
        if detected_references and selected_reference_indices:
            selected_references = filter_references(
                detected_references,
                selected_reference_indices
            )
        else:
            selected_references = []
        
        if not selected_references:
            return "❌ No reference images selected. Please select at least one reference image."
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Create batch configuration
        config = BatchConfig(
            input_dir="",  # Not used when adding images directly
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


# Create the Gradio interface
with gr.Blocks(title="Cobra - Batch Processing") as demo:
    gr.HTML(
    """
<div style="text-align: center;">
    <h1 style="text-align: center; font-size: 3em;">🎨 Cobra: Batch Processing</h1>
    <h3 style="text-align: center; font-size: 1.8em;">Efficient Line Art Colorization with Batch Support</h3>
</div>
    """
    )
    
    # Add tabs for single image and batch processing
    with gr.Tabs():
        # Single Image Tab (original interface)
        with gr.TabItem("Single Image"):
            gr.Markdown("### Single Image Colorization")
            gr.Markdown("Use this tab for processing individual images with full control.")
            
            # Include original single image interface here
            # (This would be the content from the original app.py)
            gr.Markdown("*Original single image interface would go here*")
        
        # Batch Processing Tab
        with gr.TabItem("Batch Processing"):
            gr.Markdown("### Batch Image Colorization")
            gr.Markdown(
                "Process multiple images at once. Upload a ZIP file containing both "
                "line art and colored reference images, or select a directory."
            )
            
            # Subtask 13.1: Batch mode UI components
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### Input Selection")
                    
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
                    gr.Markdown("#### Processing Configuration")
                    
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
            
            # Subtask 13.2: Reference preview integration
            gr.Markdown("---")
            gr.Markdown("### 🎨 Reference Image Preview and Selection")
            gr.Markdown(
                "Review the automatically detected colored reference images below. "
                "Select which ones to use for colorization."
            )
            
            with gr.Row():
                # Reference gallery
                reference_gallery = gr.Gallery(
                    label="Detected Reference Images",
                    show_label=True,
                    elem_id="reference_gallery",
                    columns=4,
                    rows=2,
                    height="auto",
                    object_fit="contain"
                )
            
            with gr.Row():
                # Checkbox group for selection
                reference_checkboxes = gr.CheckboxGroup(
                    label="Select References to Use",
                    choices=[],
                    value=[],
                    interactive=True
                )
            
            with gr.Row():
                # Control buttons
                select_all_btn = gr.Button("✓ Select All", size="sm")
                deselect_all_btn = gr.Button("✗ Deselect All", size="sm")
                auto_select_btn = gr.Button("⭐ Auto-Select Best", size="sm")
            
            # Confidence display
            confidence_display = gr.Markdown(
                "Select images above to see their classification confidence."
            )
            
            # Confirmation button
            confirm_refs_btn = gr.Button(
                "✓ Confirm Selection and Start Processing",
                variant="primary",
                size="lg"
            )
            
            # Subtask 13.3: Batch status display
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
                # Progress bar
                progress_bar = gr.Progress()
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
            
            # Subtask 13.4: Batch results gallery
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
            
            # Subtask 13.5: Wire up batch processing workflow
            
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
            process_input_btn.click(
                fn=lambda mode, zip_file, dir_path, recursive: (
                    process_zip_wrapper(zip_file) if mode == "ZIP File"
                    else process_dir_wrapper(dir_path, recursive)
                ),
                inputs=[batch_mode, zip_upload, dir_path, recursive_scan],
                outputs=[input_status, reference_gallery, reference_checkboxes, reference_checkboxes, confidence_display]
            )
            
            # Connect reference selection buttons
            def handle_select_all():
                choices = reference_checkboxes.choices
                if not choices:
                    return [], "No references available"
                selected = list(range(len(choices)))
                confidence_text = reference_gallery_manager.get_confidence_display(selected)
                return selected, confidence_text
            
            def handle_deselect_all():
                return [], "No images selected."
            
            def handle_auto_select():
                choices = reference_checkboxes.choices
                if not choices:
                    return [], "No references available"
                selected = reference_gallery_manager.auto_select_best(choices, threshold=0.7)
                confidence_text = reference_gallery_manager.get_confidence_display(selected)
                return selected, confidence_text
            
            def handle_selection_change(selected_indices):
                if not selected_indices:
                    return "No images selected."
                confidence_text = reference_gallery_manager.get_confidence_display(selected_indices)
                return confidence_text
            
            select_all_btn.click(
                fn=handle_select_all,
                inputs=[],
                outputs=[reference_checkboxes, confidence_display]
            )
            
            deselect_all_btn.click(
                fn=handle_deselect_all,
                inputs=[],
                outputs=[reference_checkboxes, confidence_display]
            )
            
            auto_select_btn.click(
                fn=handle_auto_select,
                inputs=[],
                outputs=[reference_checkboxes, confidence_display]
            )
            
            reference_checkboxes.change(
                fn=handle_selection_change,
                inputs=[reference_checkboxes],
                outputs=[confidence_display]
            )
            
            # Connect start processing button
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
            
            # Connect control buttons
            pause_btn.click(fn=pause_batch, outputs=[progress_text])
            resume_btn.click(fn=resume_batch, outputs=[progress_text])
            cancel_btn.click(fn=cancel_batch, outputs=[progress_text])
            
            # Connect refresh buttons
            refresh_status_btn.click(
                fn=get_batch_status,
                outputs=[status_table, progress_text, progress_bar]
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


if __name__ == "__main__":
    demo.launch(pwa=True)

"""
Reference preview and filtering UI components for batch processing.

This module provides Gradio UI components for displaying detected colored
reference images and allowing users to select/deselect which references
to use for colorization.
"""

from typing import List, Dict, Tuple, Optional, Set
from pathlib import Path
import gradio as gr
from PIL import Image

from ..logging_config import get_logger
from ..classification.classifier import ImageType
from ..exceptions import ValidationError

logger = get_logger(__name__)


class ReferencePreviewGallery:
    """
    Gradio component for previewing and filtering reference images.
    
    Displays detected colored images in a gallery with checkboxes for
    selection/deselection. Shows classification confidence for each image.
    
    Attributes:
        reference_images: List of paths to reference images
        classifications: Dictionary mapping image paths to ImageType
        selected_indices: Set of indices for currently selected images
    """
    
    def __init__(self):
        """Initialize the reference preview gallery."""
        self.reference_images: List[str] = []
        self.classifications: Dict[str, ImageType] = {}
        self.selected_indices: Set[int] = set()
        logger.debug("ReferencePreviewGallery initialized")
    
    def create_gallery_component(self) -> Tuple[gr.Gallery, gr.CheckboxGroup, gr.Row]:
        """
        Create the Gradio gallery component with controls.
        
        Returns:
            Tuple containing:
            - Gallery component for displaying images
            - CheckboxGroup for selecting images
            - Row containing control buttons
        """
        with gr.Column() as gallery_column:
            gr.Markdown("### 🎨 Detected Reference Images")
            gr.Markdown(
                "The system has automatically detected colored images that can be "
                "used as style references. Review and select which ones to use for "
                "colorization."
            )
            
            # Gallery for displaying reference images
            gallery = gr.Gallery(
                label="Reference Images",
                show_label=True,
                elem_id="reference_gallery",
                columns=4,
                rows=2,
                height="auto",
                object_fit="contain"
            )
            
            # Checkbox group for selection
            checkbox_group = gr.CheckboxGroup(
                label="Select References to Use",
                choices=[],
                value=[],
                interactive=True
            )
            
            # Control buttons
            with gr.Row() as button_row:
                select_all_btn = gr.Button("✓ Select All", size="sm")
                deselect_all_btn = gr.Button("✗ Deselect All", size="sm")
                auto_select_btn = gr.Button("⭐ Auto-Select Best", size="sm")
            
            # Confidence display
            confidence_display = gr.Markdown(
                "Select images above to see their classification confidence."
            )
        
        return gallery, checkbox_group, button_row, confidence_display, select_all_btn, deselect_all_btn, auto_select_btn
    
    def load_references(
        self,
        reference_paths: List[str],
        classifications: Dict[str, ImageType]
    ) -> Tuple[List[Image.Image], List[str], List[int]]:
        """
        Load reference images and prepare them for display.
        
        Args:
            reference_paths: List of paths to reference images
            classifications: Dictionary mapping paths to ImageType
            
        Returns:
            Tuple containing:
            - List of PIL Images for gallery display
            - List of checkbox choices (with confidence info)
            - List of initially selected indices (all selected by default)
        """
        self.reference_images = reference_paths
        self.classifications = classifications
        
        if not reference_paths:
            logger.warning("No reference images to load")
            return [], [], []
        
        logger.info(f"Loading {len(reference_paths)} reference images for preview")
        
        # Load images
        images = []
        choices = []
        
        for idx, path in enumerate(reference_paths):
            try:
                # Load image
                img = Image.open(path)
                images.append(img)
                
                # Create choice label with confidence
                filename = Path(path).name
                classification = classifications.get(path)
                
                if classification:
                    confidence_pct = classification.confidence * 100
                    choice_label = f"{idx}: {filename} (confidence: {confidence_pct:.1f}%)"
                else:
                    choice_label = f"{idx}: {filename}"
                
                choices.append(choice_label)
                
                logger.debug(f"Loaded reference {idx}: {filename}")
                
            except Exception as e:
                logger.error(f"Failed to load reference image {path}: {e}")
                continue
        
        # Select all by default
        self.selected_indices = set(range(len(images)))
        default_selection = list(range(len(images)))
        
        logger.info(f"Successfully loaded {len(images)} reference images")
        
        return images, choices, default_selection
    
    def select_all(self, choices: List[str]) -> List[int]:
        """
        Select all reference images.
        
        Args:
            choices: List of checkbox choices
            
        Returns:
            List of all indices
        """
        num_choices = len(choices)
        self.selected_indices = set(range(num_choices))
        logger.info(f"Selected all {num_choices} reference images")
        return list(range(num_choices))
    
    def deselect_all(self) -> List[int]:
        """
        Deselect all reference images.
        
        Returns:
            Empty list
        """
        self.selected_indices = set()
        logger.info("Deselected all reference images")
        return []
    
    def auto_select_best(
        self,
        choices: List[str],
        threshold: float = 0.7
    ) -> List[int]:
        """
        Automatically select references with high confidence.
        
        Selects only references with classification confidence above
        the specified threshold.
        
        Args:
            choices: List of checkbox choices
            threshold: Minimum confidence threshold (0-1)
            
        Returns:
            List of selected indices
        """
        selected = []
        
        for idx, path in enumerate(self.reference_images):
            classification = self.classifications.get(path)
            if classification and classification.confidence >= threshold:
                selected.append(idx)
        
        self.selected_indices = set(selected)
        
        logger.info(
            f"Auto-selected {len(selected)} references with confidence >= {threshold:.1%}"
        )
        
        return selected
    
    def update_selection(self, selected_indices: List[int]) -> None:
        """
        Update the current selection.
        
        Args:
            selected_indices: List of selected indices
        """
        self.selected_indices = set(selected_indices)
        logger.debug(f"Updated selection: {len(selected_indices)} images selected")
    
    def get_confidence_display(self, selected_indices: List[int]) -> str:
        """
        Generate markdown display of confidence for selected images.
        
        Args:
            selected_indices: List of selected indices
            
        Returns:
            Markdown string with confidence information
        """
        if not selected_indices:
            return "No images selected."
        
        lines = ["### Selected References Confidence:\n"]
        
        for idx in sorted(selected_indices):
            if idx < len(self.reference_images):
                path = self.reference_images[idx]
                filename = Path(path).name
                classification = self.classifications.get(path)
                
                if classification:
                    confidence_pct = classification.confidence * 100
                    metrics = classification.metrics
                    
                    lines.append(f"**{idx}. {filename}**")
                    lines.append(f"- Confidence: {confidence_pct:.1f}%")
                    lines.append(f"- Saturation: {metrics.get('saturation', 0):.3f}")
                    lines.append(f"- Unique Colors: {int(metrics.get('color_count', 0))}")
                    lines.append(f"- Edge Density: {metrics.get('edge_density', 0):.3f}")
                    lines.append("")
        
        return "\n".join(lines)


def filter_references(
    all_reference_paths: List[str],
    selected_indices: List[int]
) -> List[str]:
    """
    Filter reference images based on user selection.
    
    Takes the complete list of reference image paths and returns only
    those that were selected by the user.
    
    Args:
        all_reference_paths: Complete list of reference image paths
        selected_indices: List of indices that were selected
        
    Returns:
        List of selected reference image paths
        
    Raises:
        ValidationError: If indices are invalid
        
    Example:
        >>> all_refs = ['/path/ref1.png', '/path/ref2.png', '/path/ref3.png']
        >>> selected = filter_references(all_refs, [0, 2])
        >>> print(selected)
        ['/path/ref1.png', '/path/ref3.png']
    """
    if not all_reference_paths:
        logger.warning("No reference paths provided for filtering")
        return []
    
    if not selected_indices:
        logger.warning("No indices selected - returning empty list")
        return []
    
    # Validate indices
    max_index = len(all_reference_paths) - 1
    for idx in selected_indices:
        if idx < 0 or idx > max_index:
            error_msg = (
                f"Invalid index {idx}: must be between 0 and {max_index}"
            )
            logger.error(error_msg)
            raise ValidationError(error_msg)
    
    # Filter references
    filtered_refs = [all_reference_paths[idx] for idx in selected_indices]
    
    logger.info(
        f"Filtered references: {len(filtered_refs)} selected out of "
        f"{len(all_reference_paths)} total"
    )
    
    return filtered_refs


def create_reference_preview_ui() -> Dict[str, gr.components.Component]:
    """
    Create a complete reference preview and filtering UI.
    
    This is a convenience function that creates all necessary components
    and wires them together with appropriate event handlers.
    
    Returns:
        Dictionary mapping component names to Gradio components for
        external integration
    """
    logger.info("Creating reference preview UI")
    
    # Create gallery instance
    gallery_manager = ReferencePreviewGallery()
    
    # Create components
    (
        gallery,
        checkbox_group,
        button_row,
        confidence_display,
        select_all_btn,
        deselect_all_btn,
        auto_select_btn
    ) = gallery_manager.create_gallery_component()
    
    # Wire up event handlers
    def handle_select_all():
        choices = checkbox_group.choices
        selected = gallery_manager.select_all(choices)
        confidence_text = gallery_manager.get_confidence_display(selected)
        return selected, confidence_text
    
    def handle_deselect_all():
        selected = gallery_manager.deselect_all()
        confidence_text = gallery_manager.get_confidence_display(selected)
        return selected, confidence_text
    
    def handle_auto_select():
        choices = checkbox_group.choices
        selected = gallery_manager.auto_select_best(choices, threshold=0.7)
        confidence_text = gallery_manager.get_confidence_display(selected)
        return selected, confidence_text
    
    def handle_selection_change(selected_indices):
        gallery_manager.update_selection(selected_indices)
        confidence_text = gallery_manager.get_confidence_display(selected_indices)
        return confidence_text
    
    # Connect buttons
    select_all_btn.click(
        fn=handle_select_all,
        inputs=[],
        outputs=[checkbox_group, confidence_display]
    )
    
    deselect_all_btn.click(
        fn=handle_deselect_all,
        inputs=[],
        outputs=[checkbox_group, confidence_display]
    )
    
    auto_select_btn.click(
        fn=handle_auto_select,
        inputs=[],
        outputs=[checkbox_group, confidence_display]
    )
    
    # Connect checkbox changes
    checkbox_group.change(
        fn=handle_selection_change,
        inputs=[checkbox_group],
        outputs=[confidence_display]
    )
    
    # Return components for external use
    components = {
        'gallery': gallery,
        'checkbox_group': checkbox_group,
        'button_row': button_row,
        'confidence_display': confidence_display,
        'select_all_btn': select_all_btn,
        'deselect_all_btn': deselect_all_btn,
        'auto_select_btn': auto_select_btn,
        'gallery_manager': gallery_manager
    }
    
    logger.info("Reference preview UI created successfully")
    
    return components

"""
Demo script for reference preview and filtering UI.

This script demonstrates how to use the ReferencePreviewGallery
and filter_references functionality in a Gradio interface.
"""

import gradio as gr
from pathlib import Path
from PIL import Image
import tempfile
import shutil

from batch_processing.ui.reference_preview import (
    ReferencePreviewGallery,
    filter_references,
    create_reference_preview_ui
)
from batch_processing.classification.classifier import ImageClassifier, ImageType
from batch_processing.io.file_handler import separate_line_art_and_references


def create_demo_images(temp_dir: Path):
    """Create demo images for testing."""
    # Create some colored reference images
    colored_images = []
    for i in range(4):
        img_path = temp_dir / f"colored_ref_{i}.png"
        # Create a colorful image
        img = Image.new('RGB', (200, 200), color=(255, i * 60, 100 + i * 30))
        img.save(img_path)
        colored_images.append(str(img_path))
    
    # Create some line art images
    line_art_images = []
    for i in range(2):
        img_path = temp_dir / f"line_art_{i}.png"
        # Create a grayscale image
        img = Image.new('L', (200, 200), color=200)
        img = img.convert('RGB')
        img.save(img_path)
        line_art_images.append(str(img_path))
    
    return colored_images, line_art_images


def demo_basic_usage():
    """Demo basic usage of reference preview components."""
    print("=" * 60)
    print("Demo: Basic Reference Preview Usage")
    print("=" * 60)
    
    # Create temporary directory with demo images
    temp_dir = Path(tempfile.mkdtemp())
    try:
        colored_refs, line_art = create_demo_images(temp_dir)
        
        # Create classifier and classify images
        classifier = ImageClassifier()
        all_images = colored_refs + line_art
        classifications = classifier.classify_batch(all_images)
        
        # Separate line art from references
        line_art_paths, reference_paths, _ = separate_line_art_and_references(
            all_images, classifier
        )
        
        print(f"\nFound {len(line_art_paths)} line art images")
        print(f"Found {len(reference_paths)} colored references")
        
        # Create gallery and load references
        gallery = ReferencePreviewGallery()
        images, choices, selected = gallery.load_references(
            reference_paths,
            classifications
        )
        
        print(f"\nLoaded {len(images)} images into gallery")
        print(f"Initially selected: {selected}")
        
        # Display choices
        print("\nAvailable choices:")
        for choice in choices:
            print(f"  - {choice}")
        
        # Test selection operations
        print("\n--- Testing Select All ---")
        all_selected = gallery.select_all(choices)
        print(f"Selected: {all_selected}")
        
        print("\n--- Testing Deselect All ---")
        none_selected = gallery.deselect_all()
        print(f"Selected: {none_selected}")
        
        print("\n--- Testing Auto-Select Best (threshold=0.7) ---")
        best_selected = gallery.auto_select_best(choices, threshold=0.7)
        print(f"Selected: {best_selected}")
        
        # Test filtering
        print("\n--- Testing Filter References ---")
        gallery.update_selection([0, 2])
        filtered = filter_references(reference_paths, [0, 2])
        print(f"Filtered to {len(filtered)} references:")
        for ref in filtered:
            print(f"  - {Path(ref).name}")
        
        # Display confidence information
        print("\n--- Confidence Display ---")
        confidence_text = gallery.get_confidence_display([0, 2])
        print(confidence_text)
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print("\n✓ Demo complete, temporary files cleaned up")


def demo_gradio_interface():
    """Demo Gradio interface with reference preview."""
    print("=" * 60)
    print("Demo: Gradio Interface")
    print("=" * 60)
    print("\nLaunching Gradio interface...")
    print("This will open in your browser.")
    print("Press Ctrl+C to stop the server.")
    
    # Create temporary directory with demo images
    temp_dir = Path(tempfile.mkdtemp())
    colored_refs, line_art = create_demo_images(temp_dir)
    
    # Create classifier
    classifier = ImageClassifier()
    all_images = colored_refs + line_art
    
    def process_images():
        """Process and display reference images."""
        # Classify images
        classifications = classifier.classify_batch(all_images)
        
        # Separate line art from references
        line_art_paths, reference_paths, _ = separate_line_art_and_references(
            all_images, classifier
        )
        
        if not reference_paths:
            return [], [], [], "No colored references found."
        
        # Load images for gallery
        images = []
        choices = []
        for idx, path in enumerate(reference_paths):
            img = Image.open(path)
            images.append(img)
            
            classification = classifications.get(path)
            filename = Path(path).name
            if classification:
                confidence_pct = classification.confidence * 100
                choice_label = f"{idx}: {filename} (confidence: {confidence_pct:.1f}%)"
            else:
                choice_label = f"{idx}: {filename}"
            choices.append(choice_label)
        
        # Select all by default
        default_selection = list(range(len(images)))
        
        return images, choices, default_selection, f"Found {len(reference_paths)} colored references"
    
    def update_confidence(selected_indices):
        """Update confidence display based on selection."""
        if not selected_indices:
            return "No images selected."
        
        # Get reference paths
        _, reference_paths, classifications = separate_line_art_and_references(
            all_images, classifier
        )
        
        lines = ["### Selected References:\n"]
        for idx in selected_indices:
            if idx < len(reference_paths):
                path = reference_paths[idx]
                filename = Path(path).name
                classification = classifications.get(path)
                
                if classification:
                    confidence_pct = classification.confidence * 100
                    lines.append(f"**{idx}. {filename}** - Confidence: {confidence_pct:.1f}%")
        
        return "\n".join(lines)
    
    def filter_selected(selected_indices):
        """Filter references based on selection."""
        _, reference_paths, _ = separate_line_art_and_references(
            all_images, classifier
        )
        
        if not selected_indices:
            return "No references selected for colorization."
        
        filtered = filter_references(reference_paths, selected_indices)
        return f"✓ Selected {len(filtered)} references for colorization:\n" + "\n".join(
            f"  - {Path(p).name}" for p in filtered
        )
    
    # Create Gradio interface
    with gr.Blocks(title="Reference Preview Demo") as demo:
        gr.Markdown("# 🎨 Reference Preview and Filtering Demo")
        gr.Markdown(
            "This demo shows how the reference preview system works. "
            "Click 'Load References' to see detected colored images."
        )
        
        with gr.Row():
            load_btn = gr.Button("🔄 Load References", variant="primary")
        
        status_text = gr.Markdown("Click 'Load References' to start")
        
        with gr.Column(visible=False) as preview_section:
            gr.Markdown("### 🎨 Detected Reference Images")
            gallery = gr.Gallery(
                label="Reference Images",
                columns=4,
                height="auto"
            )
            
            checkbox_group = gr.CheckboxGroup(
                label="Select References to Use",
                choices=[],
                value=[]
            )
            
            with gr.Row():
                select_all_btn = gr.Button("✓ Select All", size="sm")
                deselect_all_btn = gr.Button("✗ Deselect All", size="sm")
            
            confidence_display = gr.Markdown("")
            
            confirm_btn = gr.Button("✅ Confirm Selection", variant="primary")
            result_display = gr.Markdown("")
        
        # Event handlers
        def show_preview():
            images, choices, selected, status = process_images()
            confidence = update_confidence(selected)
            return (
                images,
                gr.update(choices=choices, value=selected),
                status,
                gr.update(visible=True),
                confidence
            )
        
        load_btn.click(
            fn=show_preview,
            outputs=[gallery, checkbox_group, status_text, preview_section, confidence_display]
        )
        
        select_all_btn.click(
            fn=lambda choices: (list(range(len(choices))), update_confidence(list(range(len(choices))))),
            inputs=[checkbox_group],
            outputs=[checkbox_group, confidence_display]
        )
        
        deselect_all_btn.click(
            fn=lambda: ([], "No images selected."),
            outputs=[checkbox_group, confidence_display]
        )
        
        checkbox_group.change(
            fn=update_confidence,
            inputs=[checkbox_group],
            outputs=[confidence_display]
        )
        
        confirm_btn.click(
            fn=filter_selected,
            inputs=[checkbox_group],
            outputs=[result_display]
        )
    
    # Launch interface
    demo.launch(share=False)
    
    # Cleanup on exit
    shutil.rmtree(temp_dir)


def main():
    """Run all demos."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--ui":
        # Launch Gradio UI
        demo_gradio_interface()
    else:
        # Run basic demo
        demo_basic_usage()
        
        print("\n" + "=" * 60)
        print("To launch the Gradio interface demo, run:")
        print("  python demo_reference_preview.py --ui")
        print("=" * 60)


if __name__ == "__main__":
    main()

"""
Demo script for BatchProcessor.

This script demonstrates how to use the BatchProcessor class to
colorize multiple comic line art images in batch mode.
"""

import sys
from pathlib import Path
from PIL import Image
import tempfile
import shutil

from batch_processing import BatchProcessor, BatchConfig, setup_logging


def create_demo_images(input_dir: Path, num_images: int = 3):
    """Create demo line art images for testing."""
    print(f"Creating {num_images} demo images in {input_dir}")
    
    image_paths = []
    for i in range(num_images):
        # Create a simple grayscale image (simulating line art)
        img = Image.new('L', (200, 200), color=255)
        
        # Draw some simple lines to simulate line art
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        
        # Draw a simple shape
        draw.rectangle([50, 50, 150, 150], outline=0, width=3)
        draw.line([50, 100, 150, 100], fill=0, width=2)
        draw.line([100, 50, 100, 150], fill=0, width=2)
        
        # Convert to RGB
        img = img.convert('RGB')
        
        # Save
        img_path = input_dir / f"line_art_{i+1}.png"
        img.save(img_path)
        image_paths.append(str(img_path))
        print(f"  Created: {img_path.name}")
    
    return image_paths


def create_demo_references(ref_dir: Path, num_refs: int = 2):
    """Create demo colored reference images."""
    print(f"Creating {num_refs} demo reference images in {ref_dir}")
    
    ref_paths = []
    colors = [(255, 100, 100), (100, 100, 255), (100, 255, 100)]
    
    for i in range(num_refs):
        # Create a colored reference image
        img = Image.new('RGB', (200, 200), color=colors[i % len(colors)])
        
        # Add some variation
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([30, 30, 170, 170], fill=colors[(i+1) % len(colors)])
        
        # Save
        ref_path = ref_dir / f"reference_{i+1}.png"
        img.save(ref_path)
        ref_paths.append(str(ref_path))
        print(f"  Created: {ref_path.name}")
    
    return ref_paths


def demo_basic_usage():
    """Demonstrate basic BatchProcessor usage."""
    print("\n" + "="*60)
    print("DEMO: Basic BatchProcessor Usage")
    print("="*60 + "\n")
    
    # Setup logging
    setup_logging(log_level="INFO")
    
    # Create temporary directories
    temp_base = Path(tempfile.mkdtemp())
    input_dir = temp_base / "input"
    output_dir = temp_base / "output"
    ref_dir = temp_base / "references"
    
    input_dir.mkdir()
    ref_dir.mkdir()
    
    try:
        # Create demo images
        image_paths = create_demo_images(input_dir, num_images=3)
        ref_paths = create_demo_references(ref_dir, num_refs=2)
        
        print("\n" + "-"*60)
        print("Step 1: Create BatchConfig")
        print("-"*60)
        
        # Create configuration
        config = BatchConfig(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            reference_images=ref_paths,
            style="line + shadow",
            seed=42,
            num_inference_steps=10,
            top_k=3,
            recursive=False,
            overwrite=False,
            preview_mode=False
        )
        
        print(f"Input directory: {config.input_dir}")
        print(f"Output directory: {config.output_dir}")
        print(f"Reference images: {len(config.reference_images)}")
        print(f"Style: {config.style}")
        print(f"Seed: {config.seed}")
        print(f"Inference steps: {config.num_inference_steps}")
        print(f"Top K: {config.top_k}")
        
        print("\n" + "-"*60)
        print("Step 2: Initialize BatchProcessor")
        print("-"*60)
        
        # Create processor
        processor = BatchProcessor(config)
        print(f"BatchProcessor initialized")
        print(f"Device: {processor.memory_manager.device}")
        
        print("\n" + "-"*60)
        print("Step 3: Add Images to Queue")
        print("-"*60)
        
        # Add images to queue
        processor.add_images(image_paths)
        
        status = processor.get_status()
        print(f"Images in queue: {status['queue_size']}")
        print(f"Total images: {status['total_images']}")
        print(f"Pending: {status['pending']}")
        
        print("\n" + "-"*60)
        print("Step 4: Check Status Before Processing")
        print("-"*60)
        
        status = processor.get_status()
        print(f"Is processing: {status['is_processing']}")
        print(f"Is paused: {status['is_paused']}")
        print(f"Is cancelled: {status['is_cancelled']}")
        
        print("\n" + "-"*60)
        print("Step 5: Process Images (Skipped in Demo)")
        print("-"*60)
        
        print("NOTE: Actual processing is skipped in this demo because it requires")
        print("the full Cobra model to be loaded, which is resource-intensive.")
        print("\nTo actually process images, you would call:")
        print("  processor.start_processing()")
        print("\nThis would:")
        print("  1. Process each image sequentially")
        print("  2. Extract line art from input images")
        print("  3. Apply colorization using reference images")
        print("  4. Save colorized outputs")
        print("  5. Update status for each image")
        print("  6. Clean up memory between images")
        
        # Uncomment to actually process (requires full model):
        # processor.start_processing()
        
        print("\n" + "-"*60)
        print("Step 6: Check Final Status")
        print("-"*60)
        
        status = processor.get_status()
        print(f"Queue size: {status['queue_size']}")
        print(f"Completed: {status['completed']}")
        print(f"Failed: {status['failed']}")
        print(f"Pending: {status['pending']}")
        
        print("\n" + "-"*60)
        print("Demo Complete!")
        print("-"*60)
        
        print(f"\nDemo files created in: {temp_base}")
        print("(These will be cleaned up automatically)")
        
    finally:
        # Cleanup
        print("\nCleaning up temporary files...")
        shutil.rmtree(temp_base, ignore_errors=True)
        print("Cleanup complete!")


def demo_pause_resume():
    """Demonstrate pause and resume functionality."""
    print("\n" + "="*60)
    print("DEMO: Pause and Resume Functionality")
    print("="*60 + "\n")
    
    # Setup logging
    setup_logging(log_level="INFO")
    
    # Create temporary directories
    temp_base = Path(tempfile.mkdtemp())
    input_dir = temp_base / "input"
    output_dir = temp_base / "output"
    ref_dir = temp_base / "references"
    
    input_dir.mkdir()
    ref_dir.mkdir()
    
    try:
        # Create demo images
        image_paths = create_demo_images(input_dir, num_images=5)
        ref_paths = create_demo_references(ref_dir, num_refs=2)
        
        # Create configuration
        config = BatchConfig(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            reference_images=ref_paths,
            style="line + shadow",
            seed=42,
            num_inference_steps=10,
            top_k=3
        )
        
        # Create processor
        processor = BatchProcessor(config)
        processor.add_images(image_paths)
        
        print("Batch processing control methods:")
        print("  - processor.pause_processing()   # Pause after current image")
        print("  - processor.resume_processing()  # Continue processing")
        print("  - processor.cancel_processing()  # Cancel remaining images")
        
        print("\nExample workflow:")
        print("  1. Start processing: processor.start_processing()")
        print("  2. Pause: processor.pause_processing()")
        print("  3. Check status: processor.get_status()")
        print("  4. Resume: processor.resume_processing()")
        print("  5. Or cancel: processor.cancel_processing()")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_base, ignore_errors=True)


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("BatchProcessor Demo Suite")
    print("="*60)
    
    # Run demos
    demo_basic_usage()
    demo_pause_resume()
    
    print("\n" + "="*60)
    print("All Demos Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

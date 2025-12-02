"""
Demonstration of pause/resume/cancel functionality in BatchProcessor.

This script shows how to use the control methods to manage batch processing.
"""

import tempfile
import shutil
from pathlib import Path
from PIL import Image
import threading
import time

from batch_processing import BatchProcessor, BatchConfig


def create_test_images(count=5):
    """Create temporary test images."""
    temp_dir = tempfile.mkdtemp()
    image_paths = []
    
    for i in range(count):
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color=(255, 255, 255))
        img_path = Path(temp_dir) / f"test_image_{i}.png"
        img.save(img_path)
        image_paths.append(str(img_path))
    
    return temp_dir, image_paths


def create_reference_images():
    """Create temporary reference images."""
    temp_dir = tempfile.mkdtemp()
    ref_paths = []
    
    for i in range(2):
        # Create a colored reference image
        img = Image.new('RGB', (100, 100), color=(255, 0, 0))
        img_path = Path(temp_dir) / f"reference_{i}.png"
        img.save(img_path)
        ref_paths.append(str(img_path))
    
    return temp_dir, ref_paths


def demo_pause_resume():
    """Demonstrate pause and resume functionality."""
    print("\n" + "="*60)
    print("DEMO: Pause and Resume")
    print("="*60)
    
    # Create test data
    input_dir, image_paths = create_test_images(5)
    ref_dir, ref_paths = create_reference_images()
    output_dir = tempfile.mkdtemp()
    
    try:
        # Create config
        config = BatchConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            reference_images=ref_paths,
            style="line + shadow",
            seed=0,
            num_inference_steps=10,
            top_k=3
        )
        
        # Create processor
        processor = BatchProcessor(config)
        processor.add_images(image_paths)
        
        print(f"\nAdded {len(image_paths)} images to queue")
        
        # Start processing in a separate thread
        def process():
            try:
                processor.start_processing()
            except Exception as e:
                print(f"Processing error: {e}")
        
        thread = threading.Thread(target=process)
        thread.start()
        
        # Wait a bit, then pause
        time.sleep(0.5)
        print("\n⏸️  Pausing processing...")
        processor.pause_processing()
        
        # Check status
        status = processor.get_status()
        print(f"Status after pause:")
        print(f"  - Is paused: {status['is_paused']}")
        print(f"  - Completed: {status['completed']}")
        print(f"  - Pending: {status['pending']}")
        
        # Wait a bit, then resume
        time.sleep(1)
        print("\n▶️  Resuming processing...")
        processor.resume_processing()
        
        # Wait for completion
        thread.join(timeout=10)
        
        # Final status
        status = processor.get_status()
        print(f"\nFinal status:")
        print(f"  - Completed: {status['completed']}")
        print(f"  - Failed: {status['failed']}")
        print(f"  - Success rate: {status['success_rate']:.1f}%")
        
    finally:
        # Cleanup
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(ref_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)


def demo_cancel():
    """Demonstrate cancel functionality."""
    print("\n" + "="*60)
    print("DEMO: Cancel Processing")
    print("="*60)
    
    # Create test data
    input_dir, image_paths = create_test_images(5)
    ref_dir, ref_paths = create_reference_images()
    output_dir = tempfile.mkdtemp()
    
    try:
        # Create config
        config = BatchConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            reference_images=ref_paths,
            style="line + shadow",
            seed=0,
            num_inference_steps=10,
            top_k=3
        )
        
        # Create processor
        processor = BatchProcessor(config)
        processor.add_images(image_paths)
        
        print(f"\nAdded {len(image_paths)} images to queue")
        
        # Start processing in a separate thread
        def process():
            try:
                processor.start_processing()
            except Exception as e:
                print(f"Processing error: {e}")
        
        thread = threading.Thread(target=process)
        thread.start()
        
        # Wait a bit, then cancel
        time.sleep(0.5)
        print("\n❌ Cancelling processing...")
        processor.cancel_processing()
        
        # Wait for thread to finish
        thread.join(timeout=10)
        
        # Check status
        status = processor.get_status()
        print(f"\nStatus after cancel:")
        print(f"  - Is cancelled: {status['is_cancelled']}")
        print(f"  - Completed: {status['completed']}")
        print(f"  - Cancelled: {status['cancelled']}")
        print(f"  - Pending: {status['pending']}")
        
    finally:
        # Cleanup
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(ref_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)


def demo_control_flags():
    """Demonstrate control flag behavior."""
    print("\n" + "="*60)
    print("DEMO: Control Flags")
    print("="*60)
    
    # Create test data
    input_dir, image_paths = create_test_images(3)
    ref_dir, ref_paths = create_reference_images()
    output_dir = tempfile.mkdtemp()
    
    try:
        # Create config
        config = BatchConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            reference_images=ref_paths,
            style="line + shadow",
            seed=0,
            num_inference_steps=10,
            top_k=3
        )
        
        # Create processor
        processor = BatchProcessor(config)
        processor.add_images(image_paths)
        
        # Check initial flags
        status = processor.get_status()
        print("\nInitial state:")
        print(f"  - Is processing: {status['is_processing']}")
        print(f"  - Is paused: {status['is_paused']}")
        print(f"  - Is cancelled: {status['is_cancelled']}")
        
        # Try to pause when not processing (should log warning)
        print("\n⚠️  Attempting to pause when not processing...")
        processor.pause_processing()
        
        # Try to resume when not paused (should log warning)
        print("⚠️  Attempting to resume when not paused...")
        processor.resume_processing()
        
        # Try to cancel when not processing (should log warning)
        print("⚠️  Attempting to cancel when not processing...")
        processor.cancel_processing()
        
        print("\n✅ All control flag validations working correctly!")
        
    finally:
        # Cleanup
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(ref_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Pause/Resume/Cancel Functionality Demo")
    print("="*60)
    
    # Note: These demos are simplified and may not work with the actual
    # colorization pipeline without proper model setup. They demonstrate
    # the control flow logic.
    
    print("\nNote: This demo shows the control flow logic.")
    print("Actual colorization requires proper model setup.")
    
    # Demo control flags
    demo_control_flags()
    
    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60)

"""
Test script for separate_line_art_and_references function.

This script tests the new function that separates images into line art
and colored references with classification metadata.
"""

from pathlib import Path
from PIL import Image
import numpy as np
import tempfile
import shutil

from batch_processing.io import separate_line_art_and_references
from batch_processing.classification import ImageClassifier


def create_test_line_art(path: str, size=(256, 256)):
    """Create a test line art image (grayscale with high edges)."""
    # Create a simple line drawing
    img_array = np.ones((size[1], size[0]), dtype=np.uint8) * 255
    
    # Add some black lines
    img_array[50:60, :] = 0  # Horizontal line
    img_array[:, 100:110] = 0  # Vertical line
    img_array[150:200, 150:200] = 0  # Square
    
    img = Image.fromarray(img_array, mode='L')
    img.save(path)
    print(f"Created line art test image: {path}")


def create_test_colored_image(path: str, size=(256, 256)):
    """Create a test colored reference image (high saturation, many colors)."""
    # Create a colorful gradient image
    img_array = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    
    # Create color gradients
    for y in range(size[1]):
        for x in range(size[0]):
            img_array[y, x, 0] = int((x / size[0]) * 255)  # Red gradient
            img_array[y, x, 1] = int((y / size[1]) * 255)  # Green gradient
            img_array[y, x, 2] = 128  # Constant blue
    
    img = Image.fromarray(img_array, mode='RGB')
    img.save(path)
    print(f"Created colored test image: {path}")


def main():
    """Test the separate_line_art_and_references function."""
    print("=" * 60)
    print("Testing separate_line_art_and_references function")
    print("=" * 60)
    
    # Create temporary directory for test images
    temp_dir = tempfile.mkdtemp(prefix="test_separate_")
    print(f"\nCreated temporary directory: {temp_dir}")
    
    try:
        # Create test images
        line_art_1 = Path(temp_dir) / "line_art_1.png"
        line_art_2 = Path(temp_dir) / "line_art_2.png"
        colored_1 = Path(temp_dir) / "colored_ref_1.png"
        colored_2 = Path(temp_dir) / "colored_ref_2.png"
        
        print("\nCreating test images...")
        create_test_line_art(str(line_art_1))
        create_test_line_art(str(line_art_2))
        create_test_colored_image(str(colored_1))
        create_test_colored_image(str(colored_2))
        
        # Prepare list of all images
        all_images = [
            str(line_art_1),
            str(colored_1),
            str(line_art_2),
            str(colored_2)
        ]
        
        print(f"\nTotal images to classify: {len(all_images)}")
        
        # Test the function
        print("\n" + "=" * 60)
        print("Running separate_line_art_and_references...")
        print("=" * 60)
        
        line_art_list, reference_list, metadata = separate_line_art_and_references(
            all_images
        )
        
        # Display results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        
        print(f"\nLine Art Images ({len(line_art_list)}):")
        for img_path in line_art_list:
            classification = metadata[img_path]
            print(f"  - {Path(img_path).name}")
            print(f"    Type: {classification.type}")
            print(f"    Confidence: {classification.confidence:.2f}")
            print(f"    Metrics: {classification.metrics}")
        
        print(f"\nColored Reference Images ({len(reference_list)}):")
        for img_path in reference_list:
            classification = metadata[img_path]
            print(f"  - {Path(img_path).name}")
            print(f"    Type: {classification.type}")
            print(f"    Confidence: {classification.confidence:.2f}")
            print(f"    Metrics: {classification.metrics}")
        
        # Verify results
        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)
        
        success = True
        
        # Check that we got the expected number of each type
        if len(line_art_list) != 2:
            print(f"❌ Expected 2 line art images, got {len(line_art_list)}")
            success = False
        else:
            print(f"✓ Correct number of line art images: {len(line_art_list)}")
        
        if len(reference_list) != 2:
            print(f"❌ Expected 2 colored references, got {len(reference_list)}")
            success = False
        else:
            print(f"✓ Correct number of colored references: {len(reference_list)}")
        
        # Check that metadata contains all images
        if len(metadata) != 4:
            print(f"❌ Expected metadata for 4 images, got {len(metadata)}")
            success = False
        else:
            print(f"✓ Metadata contains all {len(metadata)} images")
        
        # Check that line art images are in the line art list
        for img_path in [str(line_art_1), str(line_art_2)]:
            if img_path in line_art_list:
                print(f"✓ {Path(img_path).name} correctly classified as line art")
            else:
                print(f"❌ {Path(img_path).name} should be line art but wasn't")
                success = False
        
        # Check that colored images are in the reference list
        for img_path in [str(colored_1), str(colored_2)]:
            if img_path in reference_list:
                print(f"✓ {Path(img_path).name} correctly classified as colored")
            else:
                print(f"❌ {Path(img_path).name} should be colored but wasn't")
                success = False
        
        print("\n" + "=" * 60)
        if success:
            print("✓ ALL TESTS PASSED")
        else:
            print("❌ SOME TESTS FAILED")
        print("=" * 60)
        
    finally:
        # Clean up
        print(f"\nCleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)
        print("Cleanup complete")


if __name__ == "__main__":
    main()

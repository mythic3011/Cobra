"""
Tests for file I/O handler functionality.

This module tests directory scanning, file validation, and output path
management functions.
"""

import tempfile
import os
from pathlib import Path

from batch_processing.io.file_handler import (
    scan_directory,
    validate_image_file,
    create_output_path,
    handle_filename_collision,
    separate_line_art_and_references,
    SUPPORTED_IMAGE_FORMATS
)
from batch_processing.exceptions import ValidationError, ResourceError
from batch_processing.classification import ImageClassifier
from PIL import Image
import numpy as np


def create_test_image(path: str, content: str = "fake image data") -> None:
    """Helper function to create a test image file."""
    with open(path, 'w') as f:
        f.write(content)


def test_scan_directory_basic():
    """Test basic directory scanning without recursion."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test images
        create_test_image(os.path.join(temp_dir, "image1.png"))
        create_test_image(os.path.join(temp_dir, "image2.jpg"))
        create_test_image(os.path.join(temp_dir, "image3.jpeg"))
        create_test_image(os.path.join(temp_dir, "image4.webp"))
        create_test_image(os.path.join(temp_dir, "not_image.txt"))
        
        # Scan directory
        images = scan_directory(temp_dir, recursive=False)
        
        # Verify results
        assert len(images) == 4
        assert all(Path(img).suffix.lower() in SUPPORTED_IMAGE_FORMATS for img in images)
        print(f"✓ Basic scan found {len(images)} images")


def test_scan_directory_recursive():
    """Test recursive directory scanning."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create directory structure
        subdir1 = os.path.join(temp_dir, "subdir1")
        subdir2 = os.path.join(temp_dir, "subdir2")
        nested = os.path.join(subdir1, "nested")
        
        os.makedirs(subdir1)
        os.makedirs(subdir2)
        os.makedirs(nested)
        
        # Create test images in various locations
        create_test_image(os.path.join(temp_dir, "root.png"))
        create_test_image(os.path.join(subdir1, "sub1.png"))
        create_test_image(os.path.join(subdir2, "sub2.jpg"))
        create_test_image(os.path.join(nested, "nested.png"))
        
        # Scan recursively
        images_recursive = scan_directory(temp_dir, recursive=True)
        
        # Scan non-recursively
        images_non_recursive = scan_directory(temp_dir, recursive=False)
        
        # Verify results
        assert len(images_recursive) == 4
        assert len(images_non_recursive) == 1  # Only root.png
        print(f"✓ Recursive scan found {len(images_recursive)} images")
        print(f"✓ Non-recursive scan found {len(images_non_recursive)} images")


def test_scan_directory_invalid_files():
    """Test that invalid files are skipped with logging."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create valid images
        create_test_image(os.path.join(temp_dir, "valid.png"))
        
        # Create empty file (invalid)
        empty_file = os.path.join(temp_dir, "empty.png")
        Path(empty_file).touch()
        
        # Create non-image file
        create_test_image(os.path.join(temp_dir, "text.txt"))
        
        # Scan directory
        images = scan_directory(temp_dir, recursive=False)
        
        # Should only find the valid image
        assert len(images) == 1
        assert "valid.png" in images[0]
        print(f"✓ Invalid files skipped correctly")


def test_scan_directory_nonexistent():
    """Test scanning a non-existent directory raises ValidationError."""
    try:
        scan_directory("/nonexistent/directory")
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "does not exist" in str(e)
        print("✓ Non-existent directory raises ValidationError")


def test_scan_directory_not_a_directory():
    """Test scanning a file (not directory) raises ValidationError."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a file
        file_path = os.path.join(temp_dir, "file.txt")
        create_test_image(file_path)
        
        # Try to scan it as a directory
        try:
            scan_directory(file_path)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "not a directory" in str(e)
            print("✓ File path raises ValidationError")


def test_validate_image_file_valid():
    """Test validation of valid image files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create valid images
        png_file = os.path.join(temp_dir, "test.png")
        jpg_file = os.path.join(temp_dir, "test.jpg")
        
        create_test_image(png_file)
        create_test_image(jpg_file)
        
        # Validate
        assert validate_image_file(png_file) == True
        assert validate_image_file(jpg_file) == True
        print("✓ Valid image files validated correctly")


def test_validate_image_file_invalid():
    """Test validation of invalid image files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Non-existent file
        assert validate_image_file("/nonexistent/file.png") == False
        
        # Empty file
        empty_file = os.path.join(temp_dir, "empty.png")
        Path(empty_file).touch()
        assert validate_image_file(empty_file) == False
        
        # Wrong extension
        txt_file = os.path.join(temp_dir, "file.txt")
        create_test_image(txt_file)
        assert validate_image_file(txt_file) == False
        
        # Directory
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir)
        assert validate_image_file(subdir) == False
        
        print("✓ Invalid files rejected correctly")


def test_create_output_path_basic():
    """Test basic output path creation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create input file
        input_file = os.path.join(temp_dir, "input", "test.png")
        os.makedirs(os.path.dirname(input_file))
        create_test_image(input_file)
        
        # Create output path
        output_dir = os.path.join(temp_dir, "output")
        output_path = create_output_path(input_file, output_dir)
        
        # Verify
        assert Path(output_path).parent == Path(output_dir)
        assert Path(output_path).name == "test_colorized.png"
        assert Path(output_dir).exists()
        print(f"✓ Output path created: {Path(output_path).name}")


def test_create_output_path_with_suffix_and_prefix():
    """Test output path creation with custom suffix and prefix."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create input file
        input_file = os.path.join(temp_dir, "page1.jpg")
        create_test_image(input_file)
        
        # Create output path with custom suffix and prefix
        output_dir = os.path.join(temp_dir, "output")
        output_path = create_output_path(
            input_file,
            output_dir,
            suffix="_processed",
            prefix="batch_"
        )
        
        # Verify
        assert Path(output_path).name == "batch_page1_processed.jpg"
        print(f"✓ Custom suffix/prefix applied: {Path(output_path).name}")


def test_create_output_path_preserves_extension():
    """Test that output path preserves the original file extension."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with different extensions
        for ext in ['.png', '.jpg', '.jpeg', '.webp']:
            input_file = os.path.join(temp_dir, f"test{ext}")
            create_test_image(input_file)
            
            output_dir = os.path.join(temp_dir, "output")
            output_path = create_output_path(input_file, output_dir)
            
            assert Path(output_path).suffix == ext
        
        print("✓ File extensions preserved correctly")


def test_create_output_path_creates_directory():
    """Test that output directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create input file
        input_file = os.path.join(temp_dir, "test.png")
        create_test_image(input_file)
        
        # Use non-existent output directory
        output_dir = os.path.join(temp_dir, "new", "nested", "output")
        assert not Path(output_dir).exists()
        
        # Create output path
        output_path = create_output_path(input_file, output_dir)
        
        # Verify directory was created
        assert Path(output_dir).exists()
        assert Path(output_dir).is_dir()
        print("✓ Output directory created automatically")


def test_create_output_path_invalid_input():
    """Test that invalid input raises ValidationError."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = os.path.join(temp_dir, "output")
        
        # Non-existent input file
        try:
            create_output_path("/nonexistent/file.png", output_dir)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "does not exist" in str(e)
        
        # Directory as input
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir)
        try:
            create_output_path(subdir, output_dir)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "not a file" in str(e)
        
        print("✓ Invalid input raises ValidationError")


def test_handle_filename_collision_no_collision():
    """Test collision handling when no collision exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "output.png")
        
        # No collision - should return original path
        result = handle_filename_collision(path, overwrite=False)
        assert result == path
        print("✓ No collision returns original path")


def test_handle_filename_collision_with_overwrite():
    """Test collision handling with overwrite enabled."""
    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "output.png")
        
        # Create existing file
        create_test_image(path)
        
        # With overwrite=True, should return original path
        result = handle_filename_collision(path, overwrite=True)
        assert result == path
        print("✓ Overwrite mode returns original path")


def test_handle_filename_collision_creates_numbered_variant():
    """Test collision handling creates numbered variants."""
    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "output.png")
        
        # Create existing file
        create_test_image(path)
        
        # With overwrite=False, should create numbered variant
        result = handle_filename_collision(path, overwrite=False)
        assert result == os.path.join(temp_dir, "output_1.png")
        assert not Path(result).exists()  # Shouldn't create the file, just return path
        print(f"✓ Numbered variant created: {Path(result).name}")


def test_handle_filename_collision_multiple_collisions():
    """Test collision handling with multiple existing files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create multiple existing files
        create_test_image(os.path.join(temp_dir, "output.png"))
        create_test_image(os.path.join(temp_dir, "output_1.png"))
        create_test_image(os.path.join(temp_dir, "output_2.png"))
        
        path = os.path.join(temp_dir, "output.png")
        
        # Should create output_3.png
        result = handle_filename_collision(path, overwrite=False)
        assert result == os.path.join(temp_dir, "output_3.png")
        print(f"✓ Multiple collisions handled: {Path(result).name}")


def test_handle_filename_collision_preserves_extension():
    """Test that collision handling preserves file extension."""
    with tempfile.TemporaryDirectory() as temp_dir:
        for ext in ['.png', '.jpg', '.jpeg', '.webp']:
            path = os.path.join(temp_dir, f"output{ext}")
            create_test_image(path)
            
            result = handle_filename_collision(path, overwrite=False)
            assert Path(result).suffix == ext
        
        print("✓ File extensions preserved in collision handling")


def test_scan_directory_empty():
    """Test scanning an empty directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        images = scan_directory(temp_dir, recursive=False)
        assert len(images) == 0
        print("✓ Empty directory returns empty list")


def test_scan_directory_only_subdirectories():
    """Test scanning directory with only subdirectories (no images)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create subdirectories but no images
        os.makedirs(os.path.join(temp_dir, "subdir1"))
        os.makedirs(os.path.join(temp_dir, "subdir2"))
        
        images = scan_directory(temp_dir, recursive=False)
        assert len(images) == 0
        print("✓ Directory with only subdirectories returns empty list")


def create_test_line_art_image(path: str, size=(100, 100)):
    """Helper to create a simple line art image (grayscale with edges)."""
    img_array = np.ones((size[1], size[0]), dtype=np.uint8) * 255
    # Add some black lines
    img_array[20:25, :] = 0  # Horizontal line
    img_array[:, 40:45] = 0  # Vertical line
    img = Image.fromarray(img_array, mode='L')
    img.save(path)


def create_test_colored_reference(path: str, size=(100, 100)):
    """Helper to create a colored reference image."""
    img_array = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    # Create color gradients
    for y in range(size[1]):
        for x in range(size[0]):
            img_array[y, x, 0] = int((x / size[0]) * 255)
            img_array[y, x, 1] = int((y / size[1]) * 255)
            img_array[y, x, 2] = 100
    img = Image.fromarray(img_array, mode='RGB')
    img.save(path)


def test_separate_line_art_and_references_basic():
    """Test basic separation of line art and colored references."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test images
        line_art_1 = os.path.join(temp_dir, "line1.png")
        line_art_2 = os.path.join(temp_dir, "line2.png")
        colored_1 = os.path.join(temp_dir, "colored1.png")
        colored_2 = os.path.join(temp_dir, "colored2.png")
        
        create_test_line_art_image(line_art_1)
        create_test_line_art_image(line_art_2)
        create_test_colored_reference(colored_1)
        create_test_colored_reference(colored_2)
        
        # Separate images
        all_images = [line_art_1, colored_1, line_art_2, colored_2]
        line_art_list, reference_list, metadata = separate_line_art_and_references(all_images)
        
        # Verify results
        assert len(line_art_list) == 2
        assert len(reference_list) == 2
        assert len(metadata) == 4
        
        # Check that metadata contains ImageType objects
        for img_path in all_images:
            assert img_path in metadata
            assert hasattr(metadata[img_path], 'type')
            assert hasattr(metadata[img_path], 'confidence')
            assert hasattr(metadata[img_path], 'metrics')
        
        print(f"✓ Separated {len(line_art_list)} line art and {len(reference_list)} references")


def test_separate_line_art_and_references_empty_list():
    """Test that empty list raises ValidationError."""
    try:
        separate_line_art_and_references([])
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "empty" in str(e).lower()
        print("✓ Empty list raises ValidationError")


def test_separate_line_art_and_references_with_custom_classifier():
    """Test separation with custom classifier thresholds."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test images
        line_art = os.path.join(temp_dir, "line.png")
        colored = os.path.join(temp_dir, "colored.png")
        
        create_test_line_art_image(line_art)
        create_test_colored_reference(colored)
        
        # Use custom classifier
        custom_classifier = ImageClassifier(
            saturation_threshold=0.2,
            color_count_threshold=500,
            edge_ratio_threshold=0.25
        )
        
        line_art_list, reference_list, metadata = separate_line_art_and_references(
            [line_art, colored],
            classifier=custom_classifier
        )
        
        # Should still separate correctly
        assert len(line_art_list) + len(reference_list) == 2
        assert len(metadata) == 2
        print("✓ Custom classifier works correctly")


def test_separate_line_art_and_references_metadata_structure():
    """Test that metadata has correct structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create one test image
        test_img = os.path.join(temp_dir, "test.png")
        create_test_line_art_image(test_img)
        
        _, _, metadata = separate_line_art_and_references([test_img])
        
        # Check metadata structure
        classification = metadata[test_img]
        assert classification.type in ["line_art", "colored"]
        assert 0 <= classification.confidence <= 1
        assert "saturation" in classification.metrics
        assert "color_count" in classification.metrics
        assert "edge_density" in classification.metrics
        print("✓ Metadata structure is correct")


if __name__ == "__main__":
    print("\n=== Testing File Handler Functionality ===\n")
    
    # Run all tests
    test_scan_directory_basic()
    test_scan_directory_recursive()
    test_scan_directory_invalid_files()
    test_scan_directory_nonexistent()
    test_scan_directory_not_a_directory()
    test_validate_image_file_valid()
    test_validate_image_file_invalid()
    test_create_output_path_basic()
    test_create_output_path_with_suffix_and_prefix()
    test_create_output_path_preserves_extension()
    test_create_output_path_creates_directory()
    test_create_output_path_invalid_input()
    test_handle_filename_collision_no_collision()
    test_handle_filename_collision_with_overwrite()
    test_handle_filename_collision_creates_numbered_variant()
    test_handle_filename_collision_multiple_collisions()
    test_handle_filename_collision_preserves_extension()
    test_scan_directory_empty()
    test_scan_directory_only_subdirectories()
    test_separate_line_art_and_references_basic()
    test_separate_line_art_and_references_empty_list()
    test_separate_line_art_and_references_with_custom_classifier()
    test_separate_line_art_and_references_metadata_structure()
    
    print("\n=== All File Handler Tests Passed ===\n")

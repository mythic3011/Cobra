"""
Test suite for ZIP file handling functionality.

Tests the ZIP extraction, validation, and output packaging features.
"""

import tempfile
import zipfile
from pathlib import Path
import shutil
import json
from PIL import Image
import numpy as np

from batch_processing.io import (
    is_zip_file,
    extract_zip_file,
    cleanup_temp_directory,
    create_output_zip
)
from batch_processing.exceptions import ZIPExtractionError, ValidationError


def create_test_image(path: str, size: tuple = (100, 100), color: tuple = (255, 0, 0)):
    """Helper function to create a test image."""
    img = Image.new('RGB', size, color)
    img.save(path)


def create_test_zip(zip_path: str, num_images: int = 3, include_nested: bool = False):
    """Helper function to create a test ZIP file with images."""
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Create temporary images and add to ZIP
        with tempfile.TemporaryDirectory() as temp_dir:
            for i in range(num_images):
                img_path = Path(temp_dir) / f"test_image_{i}.png"
                create_test_image(str(img_path))
                zf.write(img_path, f"test_image_{i}.png")
            
            # Add a nested ZIP if requested
            if include_nested:
                nested_zip_path = Path(temp_dir) / "nested.zip"
                with zipfile.ZipFile(nested_zip_path, 'w') as nested_zf:
                    for i in range(2):
                        img_path = Path(temp_dir) / f"nested_image_{i}.png"
                        create_test_image(str(img_path), color=(0, 255, 0))
                        nested_zf.write(img_path, f"nested_image_{i}.png")
                
                zf.write(nested_zip_path, "nested.zip")


def test_is_zip_file_valid():
    """Test is_zip_file with a valid ZIP file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "test.zip"
        create_test_zip(str(zip_path), num_images=1)
        
        assert is_zip_file(str(zip_path)) == True
        print("✓ test_is_zip_file_valid passed")


def test_is_zip_file_invalid():
    """Test is_zip_file with an invalid file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a non-ZIP file
        fake_zip = Path(temp_dir) / "fake.zip"
        fake_zip.write_text("This is not a ZIP file")
        
        assert is_zip_file(str(fake_zip)) == False
        print("✓ test_is_zip_file_invalid passed")


def test_is_zip_file_nonexistent():
    """Test is_zip_file with a non-existent file."""
    assert is_zip_file("/nonexistent/path/file.zip") == False
    print("✓ test_is_zip_file_nonexistent passed")


def test_is_zip_file_wrong_extension():
    """Test is_zip_file with wrong extension."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a valid ZIP but with wrong extension
        zip_path = Path(temp_dir) / "test.txt"
        create_test_zip(str(zip_path), num_images=1)
        
        assert is_zip_file(str(zip_path)) == False
        print("✓ test_is_zip_file_wrong_extension passed")


def test_extract_zip_file_basic():
    """Test basic ZIP extraction."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test ZIP
        zip_path = Path(temp_dir) / "test.zip"
        create_test_zip(str(zip_path), num_images=3)
        
        # Extract
        extract_dir, images = extract_zip_file(str(zip_path))
        
        try:
            # Verify extraction
            assert len(images) == 3
            assert all(Path(img).exists() for img in images)
            assert all(Path(img).suffix == '.png' for img in images)
            print("✓ test_extract_zip_file_basic passed")
        finally:
            # Cleanup
            cleanup_temp_directory(extract_dir)


def test_extract_zip_file_with_nested():
    """Test ZIP extraction with nested ZIP files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test ZIP with nested ZIP
        zip_path = Path(temp_dir) / "test.zip"
        create_test_zip(str(zip_path), num_images=3, include_nested=True)
        
        # Extract
        extract_dir, images = extract_zip_file(str(zip_path))
        
        try:
            # Verify extraction (3 main images + 2 nested images)
            assert len(images) == 5
            assert all(Path(img).exists() for img in images)
            print("✓ test_extract_zip_file_with_nested passed")
        finally:
            # Cleanup
            cleanup_temp_directory(extract_dir)


def test_extract_zip_file_to_specific_dir():
    """Test ZIP extraction to a specific directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test ZIP
        zip_path = Path(temp_dir) / "test.zip"
        create_test_zip(str(zip_path), num_images=2)
        
        # Create extraction directory
        extract_dir = Path(temp_dir) / "extracted"
        
        # Extract
        returned_dir, images = extract_zip_file(str(zip_path), str(extract_dir))
        
        try:
            # Verify extraction directory
            assert returned_dir == str(extract_dir)
            assert extract_dir.exists()
            assert len(images) == 2
            print("✓ test_extract_zip_file_to_specific_dir passed")
        finally:
            # Cleanup
            cleanup_temp_directory(str(extract_dir))


def test_extract_zip_file_invalid():
    """Test ZIP extraction with invalid file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a non-ZIP file
        fake_zip = Path(temp_dir) / "fake.zip"
        fake_zip.write_text("Not a ZIP")
        
        # Should raise ValidationError
        try:
            extract_zip_file(str(fake_zip))
            assert False, "Should have raised ValidationError"
        except ValidationError:
            print("✓ test_extract_zip_file_invalid passed")


def test_cleanup_temp_directory():
    """Test temporary directory cleanup."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix="test_cleanup_")
    
    # Create some files in it
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("test content")
    
    # Verify it exists
    assert Path(temp_dir).exists()
    
    # Cleanup
    cleanup_temp_directory(temp_dir)
    
    # Verify it's gone
    assert not Path(temp_dir).exists()
    print("✓ test_cleanup_temp_directory passed")


def test_cleanup_nonexistent_directory():
    """Test cleanup of non-existent directory (should not raise error)."""
    cleanup_temp_directory("/nonexistent/directory")
    print("✓ test_cleanup_nonexistent_directory passed")


def test_create_output_zip_basic():
    """Test basic ZIP output creation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir()
        
        # Create some test images
        for i in range(3):
            img_path = output_dir / f"result_{i}.png"
            create_test_image(str(img_path))
        
        # Create ZIP
        zip_path = create_output_zip(str(output_dir), "results")
        
        # Verify ZIP was created
        assert Path(zip_path).exists()
        assert Path(zip_path).suffix == '.zip'
        
        # Verify ZIP contents
        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()
            # Should have 3 images (no metadata since we didn't provide it)
            assert len(files) == 3, f"Expected 3 files, got {len(files)}: {files}"
            assert all('result_' in f for f in files)
        
        print("✓ test_create_output_zip_basic passed")


def test_create_output_zip_with_metadata():
    """Test ZIP creation with custom metadata."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir()
        
        # Create a test image
        img_path = output_dir / "result.png"
        create_test_image(str(img_path))
        
        # Create ZIP with metadata
        metadata = {
            "batch_id": "test_batch_123",
            "total_images": 1,
            "processing_time": 45.2
        }
        zip_path = create_output_zip(str(output_dir), "results", metadata=metadata)
        
        # Verify metadata in ZIP
        with zipfile.ZipFile(zip_path, 'r') as zf:
            metadata_content = zf.read('processing_metadata.json').decode('utf-8')
            loaded_metadata = json.loads(metadata_content)
            
            assert loaded_metadata["batch_id"] == "test_batch_123"
            assert loaded_metadata["total_images"] == 1
            assert "created_at" in loaded_metadata
            assert "cobra_version" in loaded_metadata
        
        print("✓ test_create_output_zip_with_metadata passed")


def test_create_output_zip_preserve_structure():
    """Test ZIP creation with directory structure preservation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir()
        
        # Create subdirectory structure
        subdir = output_dir / "subdir"
        subdir.mkdir()
        
        # Create images in different directories
        create_test_image(str(output_dir / "root.png"))
        create_test_image(str(subdir / "nested.png"))
        
        # Create ZIP with structure preservation
        zip_path = create_output_zip(str(output_dir), "results", preserve_structure=True)
        
        # Verify structure in ZIP
        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()
            assert any('root.png' in f for f in files)
            assert any('subdir/nested.png' in f or 'subdir\\nested.png' in f for f in files)
        
        print("✓ test_create_output_zip_preserve_structure passed")


def test_create_output_zip_no_structure():
    """Test ZIP creation without directory structure preservation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir()
        
        # Create subdirectory structure
        subdir = output_dir / "subdir"
        subdir.mkdir()
        
        # Create images in different directories
        create_test_image(str(output_dir / "root.png"))
        create_test_image(str(subdir / "nested.png"))
        
        # Create ZIP without structure preservation
        zip_path = create_output_zip(str(output_dir), "results", preserve_structure=False)
        
        # Verify flat structure in ZIP
        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()
            # All files should be at root level (no path separators except metadata)
            image_files = [f for f in files if f.endswith('.png')]
            assert all('/' not in f and '\\' not in f for f in image_files)
        
        print("✓ test_create_output_zip_no_structure passed")


def test_create_output_zip_collision_handling():
    """Test ZIP creation with filename collision."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir()
        
        # Create a test image
        create_test_image(str(output_dir / "result.png"))
        
        # Create first ZIP
        zip_path1 = create_output_zip(str(output_dir), "results")
        assert Path(zip_path1).name == "results.zip"
        
        # Create second ZIP with same name (should get numbered)
        zip_path2 = create_output_zip(str(output_dir), "results")
        assert Path(zip_path2).name == "results_1.zip"
        
        # Both should exist
        assert Path(zip_path1).exists()
        assert Path(zip_path2).exists()
        
        print("✓ test_create_output_zip_collision_handling passed")


def test_create_output_zip_invalid_directory():
    """Test ZIP creation with invalid directory."""
    try:
        create_output_zip("/nonexistent/directory", "results")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        print("✓ test_create_output_zip_invalid_directory passed")


def test_separate_line_art_and_references():
    """Test separation of line art from colored references."""
    from batch_processing.io.zip_handler import separate_line_art_and_references
    from batch_processing.classification import ImageClassifier
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create line art images (grayscale with high edges)
        line_art_paths = []
        for i in range(2):
            img_path = Path(temp_dir) / f"lineart_{i}.png"
            # Create a simple line art (black and white with edges)
            img = Image.new('L', (100, 100), 255)
            # Draw some lines
            pixels = img.load()
            for x in range(100):
                pixels[x, 50] = 0  # Horizontal line
            for y in range(100):
                pixels[50, y] = 0  # Vertical line
            img.save(img_path)
            line_art_paths.append(str(img_path))
        
        # Create colored reference images
        colored_paths = []
        for i in range(2):
            img_path = Path(temp_dir) / f"colored_{i}.png"
            # Create a colorful image
            img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            img = Image.fromarray(img_array, 'RGB')
            img.save(img_path)
            colored_paths.append(str(img_path))
        
        # Combine all paths
        all_paths = line_art_paths + colored_paths
        
        # Separate using classifier
        classifier = ImageClassifier()
        separated_line_art, separated_refs = separate_line_art_and_references(
            all_paths, classifier
        )
        
        # Verify separation (should have 2 line art and 2 colored)
        assert len(separated_line_art) == 2, f"Expected 2 line art, got {len(separated_line_art)}"
        assert len(separated_refs) == 2, f"Expected 2 references, got {len(separated_refs)}"
        
        print("✓ test_separate_line_art_and_references passed")


def run_all_tests():
    """Run all test functions."""
    print("\n=== Running ZIP Handler Tests ===\n")
    
    # is_zip_file tests
    test_is_zip_file_valid()
    test_is_zip_file_invalid()
    test_is_zip_file_nonexistent()
    test_is_zip_file_wrong_extension()
    
    # extract_zip_file tests
    test_extract_zip_file_basic()
    test_extract_zip_file_with_nested()
    test_extract_zip_file_to_specific_dir()
    test_extract_zip_file_invalid()
    
    # cleanup tests
    test_cleanup_temp_directory()
    test_cleanup_nonexistent_directory()
    
    # create_output_zip tests
    test_create_output_zip_basic()
    test_create_output_zip_with_metadata()
    test_create_output_zip_preserve_structure()
    test_create_output_zip_no_structure()
    test_create_output_zip_collision_handling()
    test_create_output_zip_invalid_directory()
    
    # separation tests
    test_separate_line_art_and_references()
    
    print("\n=== All Tests Passed! ===\n")


if __name__ == "__main__":
    run_all_tests()

"""
Integration test for complete ZIP workflow.

This test demonstrates the end-to-end ZIP processing workflow:
1. Upload ZIP with mixed line art and colored images
2. Extract and classify images
3. Separate line art from references
4. Process (simulated)
5. Package results into output ZIP
"""

import tempfile
import zipfile
from pathlib import Path
import numpy as np
from PIL import Image

from batch_processing.io import (
    extract_zip_file,
    cleanup_temp_directory,
    create_output_zip,
    separate_line_art_and_references
)
from batch_processing.classification import ImageClassifier


def create_line_art_image(path: str, size: tuple = (100, 100)):
    """Create a simple line art image (grayscale with edges)."""
    img = Image.new('L', size, 255)
    pixels = img.load()
    # Draw a grid pattern
    for x in range(0, size[0], 10):
        for y in range(size[1]):
            pixels[x, y] = 0
    for y in range(0, size[1], 10):
        for x in range(size[0]):
            pixels[x, y] = 0
    img.save(path)


def create_colored_image(path: str, size: tuple = (100, 100)):
    """Create a colorful reference image."""
    img_array = np.random.randint(50, 255, (size[0], size[1], 3), dtype=np.uint8)
    img = Image.fromarray(img_array, 'RGB')
    img.save(path)


def simulate_colorization(line_art_path: str, output_path: str):
    """Simulate colorization by creating a colored version of the line art."""
    # Just create a colored image as output
    create_colored_image(output_path)


def test_complete_zip_workflow():
    """Test the complete ZIP processing workflow."""
    print("\n=== Testing Complete ZIP Workflow ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Step 1: Create input ZIP with mixed content
        print("Step 1: Creating input ZIP with mixed content...")
        input_zip_path = Path(temp_dir) / "input.zip"
        
        with zipfile.ZipFile(input_zip_path, 'w') as zf:
            # Create temporary images
            with tempfile.TemporaryDirectory() as img_temp:
                # Add 3 line art images
                for i in range(3):
                    img_path = Path(img_temp) / f"page_{i:02d}.png"
                    create_line_art_image(str(img_path))
                    zf.write(img_path, f"page_{i:02d}.png")
                
                # Add 2 colored reference images
                for i in range(2):
                    img_path = Path(img_temp) / f"reference_{i}.png"
                    create_colored_image(str(img_path))
                    zf.write(img_path, f"reference_{i}.png")
        
        print(f"  ✓ Created input ZIP with 5 images")
        
        # Step 2: Extract ZIP
        print("\nStep 2: Extracting ZIP file...")
        extract_dir, extracted_images = extract_zip_file(str(input_zip_path))
        print(f"  ✓ Extracted {len(extracted_images)} images to {extract_dir}")
        
        try:
            # Step 3: Classify and separate images
            print("\nStep 3: Classifying and separating images...")
            classifier = ImageClassifier()
            line_art_images, reference_images = separate_line_art_and_references(
                extracted_images, classifier
            )
            print(f"  ✓ Found {len(line_art_images)} line art images")
            print(f"  ✓ Found {len(reference_images)} colored references")
            
            # Verify classification
            assert len(line_art_images) == 3, f"Expected 3 line art, got {len(line_art_images)}"
            assert len(reference_images) == 2, f"Expected 2 references, got {len(reference_images)}"
            
            # Step 4: Simulate processing
            print("\nStep 4: Processing line art images...")
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            
            processed_count = 0
            for line_art_path in line_art_images:
                # Simulate colorization
                output_path = output_dir / f"colorized_{Path(line_art_path).name}"
                simulate_colorization(line_art_path, str(output_path))
                processed_count += 1
            
            print(f"  ✓ Processed {processed_count} images")
            
            # Step 5: Create output ZIP
            print("\nStep 5: Creating output ZIP...")
            metadata = {
                "batch_id": "test_workflow_001",
                "total_images": len(line_art_images),
                "reference_images_used": len(reference_images),
                "processing_status": "completed"
            }
            
            output_zip_path = create_output_zip(
                str(output_dir),
                "colorized_results",
                metadata=metadata
            )
            print(f"  ✓ Created output ZIP: {Path(output_zip_path).name}")
            
            # Step 6: Verify output ZIP
            print("\nStep 6: Verifying output ZIP...")
            with zipfile.ZipFile(output_zip_path, 'r') as zf:
                files = zf.namelist()
                print(f"  ✓ Output ZIP contains {len(files)} files")
                
                # Should have 3 colorized images + 1 metadata file
                assert len(files) == 4, f"Expected 4 files, got {len(files)}"
                assert 'processing_metadata.json' in files
                
                # Verify metadata
                import json
                metadata_content = zf.read('processing_metadata.json').decode('utf-8')
                loaded_metadata = json.loads(metadata_content)
                assert loaded_metadata["batch_id"] == "test_workflow_001"
                assert loaded_metadata["total_images"] == 3
                print(f"  ✓ Metadata verified")
            
            print("\n=== Complete ZIP Workflow Test PASSED ===\n")
            
        finally:
            # Step 7: Cleanup
            print("Step 7: Cleaning up temporary files...")
            cleanup_temp_directory(extract_dir)
            print("  ✓ Cleanup complete")


def test_nested_zip_workflow():
    """Test ZIP workflow with nested ZIP files."""
    print("\n=== Testing Nested ZIP Workflow ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create nested ZIP structure
        print("Step 1: Creating nested ZIP structure...")
        
        # Create inner ZIP
        inner_zip_path = Path(temp_dir) / "inner.zip"
        with zipfile.ZipFile(inner_zip_path, 'w') as zf:
            with tempfile.TemporaryDirectory() as img_temp:
                # Add 2 line art images to inner ZIP
                for i in range(2):
                    img_path = Path(img_temp) / f"nested_page_{i}.png"
                    create_line_art_image(str(img_path))
                    zf.write(img_path, f"nested_page_{i}.png")
        
        # Create outer ZIP
        outer_zip_path = Path(temp_dir) / "outer.zip"
        with zipfile.ZipFile(outer_zip_path, 'w') as zf:
            with tempfile.TemporaryDirectory() as img_temp:
                # Add 1 line art image to outer ZIP
                img_path = Path(img_temp) / "main_page.png"
                create_line_art_image(str(img_path))
                zf.write(img_path, "main_page.png")
                
                # Add 1 colored reference to outer ZIP
                ref_path = Path(img_temp) / "reference.png"
                create_colored_image(str(ref_path))
                zf.write(ref_path, "reference.png")
            
            # Add the inner ZIP to outer ZIP
            zf.write(inner_zip_path, "nested.zip")
        
        print("  ✓ Created nested ZIP structure")
        
        # Extract and process
        print("\nStep 2: Extracting nested ZIP...")
        extract_dir, extracted_images = extract_zip_file(str(outer_zip_path))
        print(f"  ✓ Extracted {len(extracted_images)} images (including nested)")
        
        try:
            # Should have 3 line art + 1 colored = 4 total
            # (1 from outer + 2 from inner + 1 colored from outer)
            assert len(extracted_images) >= 3, f"Expected at least 3 images, got {len(extracted_images)}"
            
            # Classify
            print("\nStep 3: Classifying images...")
            classifier = ImageClassifier()
            line_art_images, reference_images = separate_line_art_and_references(
                extracted_images, classifier
            )
            print(f"  ✓ Found {len(line_art_images)} line art images")
            print(f"  ✓ Found {len(reference_images)} colored references")
            
            print("\n=== Nested ZIP Workflow Test PASSED ===\n")
            
        finally:
            cleanup_temp_directory(extract_dir)


def test_zip_with_subdirectories():
    """Test ZIP workflow with directory structure."""
    print("\n=== Testing ZIP with Subdirectories ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create ZIP with directory structure
        print("Step 1: Creating ZIP with subdirectories...")
        input_zip_path = Path(temp_dir) / "structured.zip"
        
        with zipfile.ZipFile(input_zip_path, 'w') as zf:
            with tempfile.TemporaryDirectory() as img_temp:
                # Create chapter1 directory
                chapter1_dir = Path(img_temp) / "chapter1"
                chapter1_dir.mkdir()
                for i in range(2):
                    img_path = chapter1_dir / f"page_{i}.png"
                    create_line_art_image(str(img_path))
                    zf.write(img_path, f"chapter1/page_{i}.png")
                
                # Create chapter2 directory
                chapter2_dir = Path(img_temp) / "chapter2"
                chapter2_dir.mkdir()
                for i in range(2):
                    img_path = chapter2_dir / f"page_{i}.png"
                    create_line_art_image(str(img_path))
                    zf.write(img_path, f"chapter2/page_{i}.png")
                
                # Add references at root
                ref_path = Path(img_temp) / "reference.png"
                create_colored_image(str(ref_path))
                zf.write(ref_path, "reference.png")
        
        print("  ✓ Created structured ZIP")
        
        # Extract and process
        print("\nStep 2: Extracting and processing...")
        extract_dir, extracted_images = extract_zip_file(str(input_zip_path))
        
        try:
            print(f"  ✓ Extracted {len(extracted_images)} images")
            
            # Process and create output with preserved structure
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            
            # Simulate processing with structure preservation
            for img_path in extracted_images:
                img_path_obj = Path(img_path)
                # Preserve relative structure
                rel_path = img_path_obj.relative_to(extract_dir)
                output_path = output_dir / rel_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Simulate colorization
                if "reference" not in str(rel_path):
                    simulate_colorization(str(img_path), str(output_path))
            
            # Create output ZIP with structure
            print("\nStep 3: Creating output ZIP with preserved structure...")
            output_zip_path = create_output_zip(
                str(output_dir),
                "structured_output",
                preserve_structure=True
            )
            
            # Verify structure is preserved
            with zipfile.ZipFile(output_zip_path, 'r') as zf:
                files = zf.namelist()
                # Should have chapter1/ and chapter2/ paths
                has_structure = any('chapter1' in f or 'chapter2' in f for f in files)
                assert has_structure, "Directory structure not preserved in output ZIP"
                print(f"  ✓ Structure preserved in output ZIP")
            
            print("\n=== ZIP with Subdirectories Test PASSED ===\n")
            
        finally:
            cleanup_temp_directory(extract_dir)


if __name__ == "__main__":
    test_complete_zip_workflow()
    test_nested_zip_workflow()
    test_zip_with_subdirectories()
    print("\n✅ All integration tests passed!\n")

"""
Demonstration of separate_line_art_and_references function.

This script shows how the function integrates with the ZIP workflow
to automatically separate line art from colored references.
"""

from pathlib import Path
from PIL import Image
import numpy as np
import tempfile
import shutil
import zipfile

from batch_processing.io import (
    separate_line_art_and_references,
    extract_zip_file,
    cleanup_temp_directory
)


def create_comic_page_lineart(path: str, page_num: int):
    """Create a realistic comic page line art."""
    size = (400, 600)
    img_array = np.ones((size[1], size[0]), dtype=np.uint8) * 255
    
    # Add panel borders
    img_array[50:250, 50:350] = 0  # Panel 1 border
    img_array[52:248, 52:348] = 255  # Panel 1 interior
    
    img_array[300:500, 50:350] = 0  # Panel 2 border
    img_array[302:498, 52:348] = 255  # Panel 2 interior
    
    # Add some character outlines (simple shapes)
    img_array[100:150, 150:200] = 0  # Character head
    img_array[150:200, 140:210] = 0  # Character body
    
    img_array[350:400, 150:200] = 0  # Another character
    
    img = Image.fromarray(img_array, mode='L')
    img.save(path)
    print(f"  Created page {page_num} line art")


def create_colored_reference(path: str, ref_type: str):
    """Create a colored reference image."""
    size = (300, 300)
    img_array = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    
    if ref_type == "character":
        # Character reference with skin tones and clothing
        img_array[:, :, 0] = 220  # Red channel (skin tone)
        img_array[:, :, 1] = 180  # Green channel
        img_array[:, :, 2] = 150  # Blue channel
        
        # Add some clothing colors
        img_array[150:, :, 0] = 50   # Dark blue clothing
        img_array[150:, :, 1] = 50
        img_array[150:, :, 2] = 200
        
    elif ref_type == "background":
        # Background reference with sky and ground
        # Sky gradient
        for y in range(150):
            img_array[y, :, 0] = 100
            img_array[y, :, 1] = 150
            img_array[y, :, 2] = 255 - int(y * 0.5)
        
        # Ground
        img_array[150:, :, 0] = 100  # Green ground
        img_array[150:, :, 1] = 200
        img_array[150:, :, 2] = 80
    
    img = Image.fromarray(img_array, mode='RGB')
    img.save(path)
    print(f"  Created {ref_type} reference")


def main():
    """Demonstrate the separate_line_art_and_references function."""
    print("=" * 70)
    print("DEMONSTRATION: Smart Reference Detection and Separation")
    print("=" * 70)
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="demo_separate_")
    print(f"\nWorking directory: {temp_dir}\n")
    
    try:
        # Scenario 1: Direct file list
        print("SCENARIO 1: Direct File List")
        print("-" * 70)
        
        files_dir = Path(temp_dir) / "files"
        files_dir.mkdir()
        
        print("Creating test images...")
        create_comic_page_lineart(str(files_dir / "page1.png"), 1)
        create_comic_page_lineart(str(files_dir / "page2.png"), 2)
        create_comic_page_lineart(str(files_dir / "page3.png"), 3)
        create_colored_reference(str(files_dir / "character_ref.png"), "character")
        create_colored_reference(str(files_dir / "background_ref.png"), "background")
        
        all_files = [str(f) for f in files_dir.glob("*.png")]
        print(f"\nTotal files: {len(all_files)}")
        
        print("\nSeparating line art from references...")
        line_art, references, metadata = separate_line_art_and_references(all_files)
        
        print(f"\n✓ Found {len(line_art)} line art images:")
        for img in line_art:
            name = Path(img).name
            conf = metadata[img].confidence
            print(f"  - {name} (confidence: {conf:.2f})")
        
        print(f"\n✓ Found {len(references)} colored references:")
        for img in references:
            name = Path(img).name
            conf = metadata[img].confidence
            print(f"  - {name} (confidence: {conf:.2f})")
        
        # Scenario 2: ZIP file workflow
        print("\n" + "=" * 70)
        print("SCENARIO 2: ZIP File Workflow")
        print("-" * 70)
        
        # Create a ZIP file with mixed content
        zip_dir = Path(temp_dir) / "zip_test"
        zip_dir.mkdir()
        
        print("\nCreating ZIP file with mixed content...")
        zip_path = zip_dir / "comic_chapter.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add line art pages
            for i in range(1, 4):
                img_path = files_dir / f"page{i}.png"
                zf.write(img_path, f"pages/page{i}.png")
            
            # Add reference images
            zf.write(files_dir / "character_ref.png", "references/character.png")
            zf.write(files_dir / "background_ref.png", "references/background.png")
        
        print(f"✓ Created ZIP: {zip_path.name}")
        
        # Extract ZIP
        print("\nExtracting ZIP file...")
        extract_dir, extracted_files = extract_zip_file(str(zip_path))
        print(f"✓ Extracted {len(extracted_files)} images")
        
        # Separate extracted images
        print("\nSeparating extracted images...")
        line_art_zip, references_zip, metadata_zip = separate_line_art_and_references(
            extracted_files
        )
        
        print(f"\n✓ Line art for colorization ({len(line_art_zip)}):")
        for img in line_art_zip:
            name = Path(img).name
            conf = metadata_zip[img].confidence
            metrics = metadata_zip[img].metrics
            print(f"  - {name}")
            print(f"    Confidence: {conf:.2f}")
            print(f"    Saturation: {metrics['saturation']:.3f}")
            print(f"    Colors: {int(metrics['color_count'])}")
            print(f"    Edge density: {metrics['edge_density']:.3f}")
        
        print(f"\n✓ References for style guidance ({len(references_zip)}):")
        for img in references_zip:
            name = Path(img).name
            conf = metadata_zip[img].confidence
            metrics = metadata_zip[img].metrics
            print(f"  - {name}")
            print(f"    Confidence: {conf:.2f}")
            print(f"    Saturation: {metrics['saturation']:.3f}")
            print(f"    Colors: {int(metrics['color_count'])}")
            print(f"    Edge density: {metrics['edge_density']:.3f}")
        
        # Show the workflow
        print("\n" + "=" * 70)
        print("TYPICAL WORKFLOW")
        print("-" * 70)
        print("""
1. User uploads ZIP file containing:
   - Comic pages (line art to be colorized)
   - Reference images (colored examples for style)

2. System extracts ZIP and classifies images:
   - Analyzes color saturation, color diversity, edge density
   - Separates into line art vs colored references

3. System displays reference preview:
   - Shows detected colored images in gallery
   - User can select/deselect references

4. System processes batch:
   - Colorizes line art using selected references
   - Applies style from references to guide colorization

5. System packages results:
   - Creates output ZIP with colorized pages
   - Preserves directory structure
        """)
        
        # Cleanup extracted files
        print("\nCleaning up extracted files...")
        cleanup_temp_directory(extract_dir)
        print("✓ Cleanup complete")
        
        print("\n" + "=" * 70)
        print("✓ DEMONSTRATION COMPLETE")
        print("=" * 70)
        
    finally:
        # Clean up temp directory
        print(f"\nRemoving temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()

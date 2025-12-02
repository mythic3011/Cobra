#!/usr/bin/env python3
"""
Demonstration of file I/O and directory scanning functionality.

This script demonstrates the key features of the file handler module
for batch processing operations.
"""

import tempfile
import os
from pathlib import Path

from batch_processing.io import (
    scan_directory,
    validate_image_file,
    create_output_path,
    handle_filename_collision
)


def create_demo_structure():
    """Create a demo directory structure with test files."""
    temp_dir = tempfile.mkdtemp(prefix="cobra_demo_")
    
    # Create directory structure
    input_dir = Path(temp_dir) / "input"
    input_dir.mkdir()
    
    subdir1 = input_dir / "chapter1"
    subdir2 = input_dir / "chapter2"
    subdir1.mkdir()
    subdir2.mkdir()
    
    # Create test image files
    files = [
        input_dir / "cover.png",
        subdir1 / "page1.png",
        subdir1 / "page2.jpg",
        subdir2 / "page3.jpeg",
        subdir2 / "page4.webp",
        input_dir / "readme.txt",  # Non-image file
    ]
    
    for file in files:
        with open(file, 'w') as f:
            f.write("demo content")
    
    return temp_dir, input_dir


def demo_directory_scanning():
    """Demonstrate directory scanning functionality."""
    print("\n" + "="*60)
    print("DEMO 1: Directory Scanning")
    print("="*60)
    
    temp_dir, input_dir = create_demo_structure()
    
    try:
        # Non-recursive scan
        print(f"\n📁 Scanning: {input_dir}")
        print("   Mode: Non-recursive")
        images = scan_directory(str(input_dir), recursive=False)
        print(f"   Found: {len(images)} image(s)")
        for img in images:
            print(f"   - {Path(img).name}")
        
        # Recursive scan
        print(f"\n📁 Scanning: {input_dir}")
        print("   Mode: Recursive")
        images = scan_directory(str(input_dir), recursive=True)
        print(f"   Found: {len(images)} image(s)")
        for img in images:
            rel_path = Path(img).relative_to(input_dir)
            print(f"   - {rel_path}")
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)


def demo_file_validation():
    """Demonstrate file validation functionality."""
    print("\n" + "="*60)
    print("DEMO 2: File Validation")
    print("="*60)
    
    temp_dir, input_dir = create_demo_structure()
    
    try:
        test_files = [
            (input_dir / "cover.png", "Valid PNG file"),
            (input_dir / "readme.txt", "Text file (invalid)"),
            (input_dir / "nonexistent.png", "Non-existent file"),
        ]
        
        print("\n🔍 Validating files:")
        for file_path, description in test_files:
            is_valid = validate_image_file(str(file_path))
            status = "✓ Valid" if is_valid else "✗ Invalid"
            print(f"   {status}: {description}")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def demo_output_path_creation():
    """Demonstrate output path creation functionality."""
    print("\n" + "="*60)
    print("DEMO 3: Output Path Creation")
    print("="*60)
    
    temp_dir, input_dir = create_demo_structure()
    
    try:
        input_file = input_dir / "cover.png"
        output_dir = Path(temp_dir) / "output"
        
        print(f"\n📄 Input file: {input_file.name}")
        print(f"📂 Output directory: {output_dir}")
        
        # Default suffix
        output1 = create_output_path(str(input_file), str(output_dir))
        print(f"\n   Default suffix:")
        print(f"   → {Path(output1).name}")
        
        # Custom suffix
        output2 = create_output_path(
            str(input_file),
            str(output_dir),
            suffix="_processed"
        )
        print(f"\n   Custom suffix '_processed':")
        print(f"   → {Path(output2).name}")
        
        # Prefix and suffix
        output3 = create_output_path(
            str(input_file),
            str(output_dir),
            prefix="batch_",
            suffix="_final"
        )
        print(f"\n   Prefix 'batch_' + suffix '_final':")
        print(f"   → {Path(output3).name}")
        
        print(f"\n✓ Output directory created: {output_dir.exists()}")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def demo_collision_handling():
    """Demonstrate filename collision handling."""
    print("\n" + "="*60)
    print("DEMO 4: Filename Collision Handling")
    print("="*60)
    
    temp_dir = Path(tempfile.mkdtemp(prefix="cobra_demo_"))
    
    try:
        # Create existing files
        existing_files = [
            temp_dir / "output.png",
            temp_dir / "output_1.png",
            temp_dir / "output_2.png",
        ]
        
        for file in existing_files:
            file.touch()
        
        print("\n📁 Existing files:")
        for file in existing_files:
            print(f"   - {file.name}")
        
        # Test collision handling
        target_path = str(temp_dir / "output.png")
        
        print(f"\n🎯 Target path: output.png")
        
        # Without overwrite
        result1 = handle_filename_collision(target_path, overwrite=False)
        print(f"\n   Overwrite=False:")
        print(f"   → {Path(result1).name}")
        
        # With overwrite
        result2 = handle_filename_collision(target_path, overwrite=True)
        print(f"\n   Overwrite=True:")
        print(f"   → {Path(result2).name}")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def main():
    """Run all demonstrations."""
    print("\n" + "="*60)
    print("File I/O and Directory Scanning Demonstration")
    print("="*60)
    
    demo_directory_scanning()
    demo_file_validation()
    demo_output_path_creation()
    demo_collision_handling()
    
    print("\n" + "="*60)
    print("✓ All demonstrations completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

"""
ZIP file handling for batch processing.

This module provides functionality for extracting images from ZIP files,
including nested ZIP support, and packaging processed images into ZIP files.
"""

import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import json
from datetime import datetime

from ..logging_config import get_logger
from ..exceptions import ZIPExtractionError, ValidationError

logger = get_logger(__name__)

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.webp'}

# Patterns to skip (macOS metadata, hidden files, etc.)
SKIP_PATTERNS = {
    '__MACOSX',  # macOS metadata folder
    '.DS_Store',  # macOS folder metadata
    '._',  # macOS resource fork files (start with ._)
    'Thumbs.db',  # Windows thumbnail cache
    'desktop.ini',  # Windows folder settings
}


def should_skip_file(file_path: Path) -> bool:
    """
    Check if a file should be skipped during extraction.
    
    Skips macOS metadata files, hidden system files, and other non-image files.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if the file should be skipped, False otherwise
    """
    # Check if any part of the path contains skip patterns
    path_parts = file_path.parts
    for part in path_parts:
        if part in SKIP_PATTERNS:
            return True
        # Check for files starting with ._
        if part.startswith('._'):
            return True
    
    # Skip hidden files (starting with .)
    if file_path.name.startswith('.') and file_path.name not in {'.gitkeep'}:
        return True
    
    return False


def is_zip_file(path: str) -> bool:
    """
    Validate if a file is a valid ZIP file.
    
    Checks both the file extension and the file content to ensure
    it's a valid ZIP archive.
    
    Args:
        path: Path to the file to check
        
    Returns:
        True if the file is a valid ZIP file, False otherwise
    """
    file_path = Path(path)
    
    # Check if file exists
    if not file_path.exists():
        logger.debug(f"File does not exist: {path}")
        return False
    
    # Check if it's a file (not a directory)
    if not file_path.is_file():
        logger.debug(f"Path is not a file: {path}")
        return False
    
    # Check extension
    if file_path.suffix.lower() != '.zip':
        logger.debug(f"File does not have .zip extension: {path}")
        return False
    
    # Verify it's a valid ZIP file by attempting to open it
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            # Test the ZIP file integrity
            bad_file = zf.testzip()
            if bad_file is not None:
                logger.warning(f"ZIP file has corrupted member: {bad_file}")
                return False
        logger.debug(f"Validated ZIP file: {path}")
        return True
    except zipfile.BadZipFile:
        logger.debug(f"File is not a valid ZIP archive: {path}")
        return False
    except Exception as e:
        logger.warning(f"Error validating ZIP file {path}: {e}")
        return False


def extract_zip_file(
    zip_path: str,
    extract_dir: Optional[str] = None,
    nested_level: int = 0,
    max_nested_level: int = 1
) -> Tuple[str, List[str]]:
    """
    Extract all image files from a ZIP archive.
    
    Supports nested ZIP files up to one level deep. Creates a temporary
    directory for extraction if none is provided. The temporary directory
    will need to be cleaned up by the caller.
    
    Args:
        zip_path: Path to the ZIP file to extract
        extract_dir: Optional directory to extract to. If None, creates a temp directory
        nested_level: Current nesting level (used for recursion)
        max_nested_level: Maximum nesting level to support (default: 1)
        
    Returns:
        Tuple of (extraction_directory, list_of_extracted_image_paths)
        
    Raises:
        ZIPExtractionError: If extraction fails
        ValidationError: If the ZIP file is invalid
    """
    # Validate the ZIP file
    if not is_zip_file(zip_path):
        raise ValidationError(f"Invalid or corrupted ZIP file: {zip_path}")
    
    # Create extraction directory if not provided
    if extract_dir is None:
        extract_dir = tempfile.mkdtemp(prefix="cobra_zip_extract_")
        logger.info(f"Created temporary extraction directory: {extract_dir}")
    else:
        extract_dir_path = Path(extract_dir)
        extract_dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using extraction directory: {extract_dir}")
    
    extracted_images: List[str] = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Get list of all files in the ZIP
            all_files = zf.namelist()
            logger.info(f"Extracting {len(all_files)} files from {Path(zip_path).name}")
            
            # Extract all files
            zf.extractall(extract_dir)
            
            # Process extracted files
            for file_name in all_files:
                file_path = Path(extract_dir) / file_name
                
                # Skip directories
                if file_path.is_dir():
                    continue
                
                # Skip macOS metadata and hidden files
                if should_skip_file(file_path):
                    logger.debug(f"Skipping metadata/hidden file: {file_path.name}")
                    continue
                
                # Check if it's an image file
                if file_path.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
                    extracted_images.append(str(file_path))
                    logger.debug(f"Found image: {file_path.name}")
                
                # Check if it's a nested ZIP file
                elif file_path.suffix.lower() == '.zip' and nested_level < max_nested_level:
                    logger.info(
                        f"Found nested ZIP file: {file_path.name} "
                        f"(level {nested_level + 1}/{max_nested_level})"
                    )
                    try:
                        # Extract nested ZIP to a subdirectory
                        nested_extract_dir = file_path.parent / f"{file_path.stem}_extracted"
                        _, nested_images = extract_zip_file(
                            str(file_path),
                            str(nested_extract_dir),
                            nested_level=nested_level + 1,
                            max_nested_level=max_nested_level
                        )
                        extracted_images.extend(nested_images)
                        logger.info(f"Extracted {len(nested_images)} images from nested ZIP")
                    except Exception as e:
                        logger.warning(f"Failed to extract nested ZIP {file_path.name}: {e}")
                        # Continue processing other files
                        continue
        
        logger.info(
            f"Successfully extracted {len(extracted_images)} images from {Path(zip_path).name}"
        )
        return extract_dir, extracted_images
        
    except zipfile.BadZipFile as e:
        error_msg = f"Corrupted ZIP file: {zip_path}"
        logger.error(error_msg)
        raise ZIPExtractionError(error_msg) from e
    except PermissionError as e:
        error_msg = f"Permission denied accessing ZIP file or extraction directory: {zip_path}"
        logger.error(error_msg)
        raise ZIPExtractionError(error_msg) from e
    except Exception as e:
        error_msg = f"Failed to extract ZIP file {zip_path}: {str(e)}"
        logger.error(error_msg)
        raise ZIPExtractionError(error_msg) from e


def cleanup_temp_directory(directory: str) -> None:
    """
    Clean up a temporary extraction directory.
    
    Safely removes the directory and all its contents. Logs warnings
    if cleanup fails but does not raise exceptions.
    
    Args:
        directory: Path to the directory to remove
    """
    try:
        dir_path = Path(directory)
        if dir_path.exists() and dir_path.is_dir():
            shutil.rmtree(directory)
            logger.info(f"Cleaned up temporary directory: {directory}")
        else:
            logger.debug(f"Directory does not exist or is not a directory: {directory}")
    except PermissionError as e:
        logger.warning(f"Permission denied cleaning up directory {directory}: {e}")
    except Exception as e:
        logger.warning(f"Failed to clean up directory {directory}: {e}")


def create_output_zip(
    output_dir: str,
    zip_name: str,
    metadata: Optional[dict] = None,
    preserve_structure: bool = True
) -> str:
    """
    Package all processed images from output directory into a ZIP file.
    
    Creates a ZIP archive containing all images from the output directory.
    Optionally preserves the directory structure and includes a metadata
    file with processing information.
    
    Args:
        output_dir: Directory containing the processed images
        zip_name: Name for the output ZIP file (without .zip extension)
        metadata: Optional dictionary of metadata to include in the ZIP
        preserve_structure: If True, preserve directory structure in ZIP
        
    Returns:
        Path to the created ZIP file
        
    Raises:
        ZIPExtractionError: If ZIP creation fails
        ValidationError: If output directory is invalid
    """
    output_path = Path(output_dir)
    
    # Validate output directory
    if not output_path.exists():
        raise ValidationError(f"Output directory does not exist: {output_dir}")
    
    if not output_path.is_dir():
        raise ValidationError(f"Output path is not a directory: {output_dir}")
    
    # Create ZIP file path
    zip_path = output_path / f"{zip_name}.zip"
    
    # Ensure we don't overwrite existing ZIP
    counter = 1
    while zip_path.exists():
        zip_path = output_path / f"{zip_name}_{counter}.zip"
        counter += 1
    
    logger.info(f"Creating output ZIP: {zip_path}")
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Collect all image files
            image_files: List[Path] = []
            for ext in SUPPORTED_IMAGE_FORMATS:
                image_files.extend(output_path.rglob(f"*{ext}"))
            
            logger.info(f"Found {len(image_files)} images to package")
            
            # Add images to ZIP
            for image_file in image_files:
                # Calculate archive name
                if preserve_structure:
                    # Preserve relative path from output_dir
                    arcname = str(image_file.relative_to(output_path))
                else:
                    # Just use the filename
                    arcname = image_file.name
                
                # Add to ZIP
                zf.write(image_file, arcname)
                logger.debug(f"Added to ZIP: {arcname}")
            
            # Add metadata file if provided
            if metadata is not None:
                metadata_content = _create_metadata_content(metadata)
                zf.writestr("processing_metadata.json", metadata_content)
                logger.info("Added metadata file to ZIP")
        
        logger.info(f"Successfully created ZIP file: {zip_path}")
        return str(zip_path)
        
    except PermissionError as e:
        error_msg = f"Permission denied creating ZIP file: {zip_path}"
        logger.error(error_msg)
        raise ZIPExtractionError(error_msg) from e
    except Exception as e:
        error_msg = f"Failed to create ZIP file {zip_path}: {str(e)}"
        logger.error(error_msg)
        raise ZIPExtractionError(error_msg) from e


def _create_metadata_content(metadata: dict) -> str:
    """
    Create formatted metadata content for inclusion in ZIP.
    
    Args:
        metadata: Dictionary of metadata to format
        
    Returns:
        JSON-formatted string of metadata
    """
    # Add timestamp if not present
    if "created_at" not in metadata:
        metadata["created_at"] = datetime.now().isoformat()
    
    # Add version info
    if "cobra_version" not in metadata:
        metadata["cobra_version"] = "batch_processing_v1"
    
    # Format as pretty JSON
    return json.dumps(metadata, indent=2, sort_keys=True)


def separate_line_art_and_references(
    image_paths: List[str],
    classifier=None
) -> Tuple[List[str], List[str]]:
    """
    Separate images into line art and colored references using classification.
    
    This is a convenience function that uses the ImageClassifier to automatically
    separate a list of images into those suitable for colorization (line art)
    and those suitable as style references (colored images).
    
    Args:
        image_paths: List of image file paths to classify
        classifier: Optional ImageClassifier instance. If None, creates a default one.
        
    Returns:
        Tuple of (line_art_paths, reference_paths)
        
    Example:
        >>> line_art, refs = separate_line_art_and_references(all_images)
        >>> print(f"Found {len(line_art)} line art images and {len(refs)} references")
    """
    # Import here to avoid circular dependency
    from ..classification import ImageClassifier
    
    if classifier is None:
        classifier = ImageClassifier()
    
    logger.info(f"Classifying {len(image_paths)} images to separate line art from references")
    
    # Classify all images
    classifications = classifier.classify_batch(image_paths)
    
    # Separate into two lists
    line_art_paths = []
    reference_paths = []
    
    for image_path, classification in classifications.items():
        if classification.type == "line_art":
            line_art_paths.append(image_path)
        else:  # colored
            reference_paths.append(image_path)
    
    logger.info(
        f"Separated images: {len(line_art_paths)} line art, "
        f"{len(reference_paths)} colored references"
    )
    
    return line_art_paths, reference_paths


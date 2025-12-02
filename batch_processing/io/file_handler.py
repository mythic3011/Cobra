"""
File I/O operations for batch processing.

This module provides functionality for directory scanning, file validation,
and output path management for batch processing operations.
"""

from pathlib import Path
from typing import List, Optional, Set, Tuple, Dict
import os

from ..logging_config import get_logger
from ..exceptions import ValidationError, ResourceError
from ..classification.classifier import ImageClassifier, ImageType

logger = get_logger(__name__)

# Supported image formats (imported from zip_handler for consistency)
from .zip_handler import SUPPORTED_IMAGE_FORMATS


def scan_directory(
    directory: str,
    recursive: bool = False,
    supported_formats: Optional[Set[str]] = None
) -> List[str]:
    """
    Scan a directory for valid image files.
    
    Identifies all supported image formats in the specified directory.
    Invalid files are skipped with logging. Optionally scans subdirectories
    recursively.
    
    Args:
        directory: Path to the directory to scan
        recursive: If True, scan subdirectories recursively
        supported_formats: Set of supported file extensions (e.g., {'.png', '.jpg'}).
                          If None, uses SUPPORTED_IMAGE_FORMATS
        
    Returns:
        List of absolute paths to valid image files
        
    Raises:
        ValidationError: If directory does not exist or is not accessible
        
    Example:
        >>> images = scan_directory('/path/to/images', recursive=True)
        >>> print(f"Found {len(images)} images")
    """
    if supported_formats is None:
        supported_formats = SUPPORTED_IMAGE_FORMATS
    
    dir_path = Path(directory)
    
    # Validate directory exists
    if not dir_path.exists():
        error_msg = f"Directory does not exist: {directory}"
        logger.error(error_msg)
        raise ValidationError(error_msg)
    
    # Validate it's a directory
    if not dir_path.is_dir():
        error_msg = f"Path is not a directory: {directory}"
        logger.error(error_msg)
        raise ValidationError(error_msg)
    
    # Check directory is accessible
    if not os.access(directory, os.R_OK):
        error_msg = f"Directory is not readable: {directory}"
        logger.error(error_msg)
        raise ValidationError(error_msg)
    
    logger.info(
        f"Scanning directory: {directory} "
        f"(recursive={'yes' if recursive else 'no'})"
    )
    
    valid_images: List[str] = []
    invalid_count = 0
    
    try:
        # Choose scanning method based on recursive flag
        if recursive:
            # Use rglob for recursive scanning
            file_iterator = dir_path.rglob('*')
        else:
            # Use glob for non-recursive scanning
            file_iterator = dir_path.glob('*')
        
        # Process each file
        for file_path in file_iterator:
            # Skip directories
            if file_path.is_dir():
                continue
            
            # Check if file has supported extension
            if file_path.suffix.lower() in supported_formats:
                # Validate the image file
                if validate_image_file(str(file_path)):
                    valid_images.append(str(file_path.absolute()))
                    logger.debug(f"Found valid image: {file_path.name}")
                else:
                    invalid_count += 1
                    logger.warning(f"Skipping invalid image file: {file_path}")
            else:
                # Log files with unsupported extensions at debug level
                if file_path.suffix:  # Only log if there is an extension
                    logger.debug(
                        f"Skipping file with unsupported extension: {file_path.name}"
                    )
        
        logger.info(
            f"Scan complete: found {len(valid_images)} valid images, "
            f"skipped {invalid_count} invalid files"
        )
        
        return valid_images
        
    except PermissionError as e:
        error_msg = f"Permission denied accessing directory or files in: {directory}"
        logger.error(error_msg)
        raise ValidationError(error_msg) from e
    except Exception as e:
        error_msg = f"Error scanning directory {directory}: {str(e)}"
        logger.error(error_msg)
        raise ValidationError(error_msg) from e


def validate_image_file(path: str) -> bool:
    """
    Validate if a file is a valid image file.
    
    Checks if the file exists, is readable, and has a supported format.
    Does not validate the actual image content (e.g., checking if it's corrupted),
    only that it's accessible and has the right extension.
    
    Args:
        path: Path to the file to validate
        
    Returns:
        True if the file is valid, False otherwise
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
    
    # Check if file is readable
    if not os.access(path, os.R_OK):
        logger.debug(f"File is not readable: {path}")
        return False
    
    # Check if file has supported extension
    if file_path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
        logger.debug(f"File has unsupported format: {path}")
        return False
    
    # Check if file is not empty
    if file_path.stat().st_size == 0:
        logger.debug(f"File is empty: {path}")
        return False
    
    return True


def create_output_path(
    input_path: str,
    output_dir: str,
    suffix: str = "_colorized",
    prefix: str = ""
) -> str:
    """
    Create an output path for a processed image.
    
    Generates an output file path based on the input filename, applying
    optional prefix and suffix. Preserves the original file extension.
    Creates the output directory if it doesn't exist.
    
    Args:
        input_path: Path to the input image file
        output_dir: Directory where output should be saved
        suffix: Suffix to add to filename (default: "_colorized")
        prefix: Prefix to add to filename (default: "")
        
    Returns:
        Absolute path to the output file
        
    Raises:
        ValidationError: If input path is invalid
        ResourceError: If output directory cannot be created
        
    Example:
        >>> output = create_output_path(
        ...     '/input/page1.png',
        ...     '/output',
        ...     suffix='_colored'
        ... )
        >>> print(output)
        /output/page1_colored.png
    """
    input_file = Path(input_path)
    
    # Validate input path
    if not input_file.exists():
        error_msg = f"Input file does not exist: {input_path}"
        logger.error(error_msg)
        raise ValidationError(error_msg)
    
    if not input_file.is_file():
        error_msg = f"Input path is not a file: {input_path}"
        logger.error(error_msg)
        raise ValidationError(error_msg)
    
    # Create output directory if it doesn't exist
    output_dir_path = Path(output_dir)
    try:
        output_dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured output directory exists: {output_dir}")
    except PermissionError as e:
        error_msg = f"Permission denied creating output directory: {output_dir}"
        logger.error(error_msg)
        raise ResourceError(error_msg) from e
    except Exception as e:
        error_msg = f"Failed to create output directory {output_dir}: {str(e)}"
        logger.error(error_msg)
        raise ResourceError(error_msg) from e
    
    # Build output filename
    stem = input_file.stem  # Filename without extension
    extension = input_file.suffix  # File extension including the dot
    
    output_filename = f"{prefix}{stem}{suffix}{extension}"
    output_path = output_dir_path / output_filename
    
    logger.debug(f"Created output path: {output_path}")
    
    return str(output_path.absolute())


def handle_filename_collision(
    path: str,
    overwrite: bool = False
) -> str:
    """
    Handle filename collisions when saving output files.
    
    If a file already exists at the specified path, either overwrites it
    (if overwrite=True) or creates a numbered variant (e.g., file_1.png,
    file_2.png, etc.).
    
    Args:
        path: Desired output file path
        overwrite: If True, allows overwriting existing files.
                  If False, creates numbered variants.
        
    Returns:
        Final path to use for saving (may be modified to avoid collision)
        
    Example:
        >>> # If output.png exists and overwrite=False
        >>> final_path = handle_filename_collision('/output/output.png', overwrite=False)
        >>> print(final_path)
        /output/output_1.png
    """
    file_path = Path(path)
    
    # If file doesn't exist, no collision
    if not file_path.exists():
        logger.debug(f"No collision: {path}")
        return path
    
    # If overwrite is enabled, return original path
    if overwrite:
        logger.info(f"Overwriting existing file: {path}")
        return path
    
    # Create numbered variant
    stem = file_path.stem
    extension = file_path.suffix
    parent = file_path.parent
    
    counter = 1
    while True:
        new_filename = f"{stem}_{counter}{extension}"
        new_path = parent / new_filename
        
        if not new_path.exists():
            logger.info(f"Collision resolved: {path} -> {new_path}")
            return str(new_path)
        
        counter += 1
        
        # Safety check to prevent infinite loop
        if counter > 10000:
            error_msg = f"Too many file collisions for: {path}"
            logger.error(error_msg)
            raise ResourceError(error_msg)



def separate_line_art_and_references(
    image_paths: List[str],
    classifier: Optional[ImageClassifier] = None
) -> Tuple[List[str], List[str], Dict[str, ImageType]]:
    """
    Separate images into line art and colored reference lists.
    
    Uses ImageClassifier to automatically classify each image as either
    line art (to be colorized) or colored reference (to be used as style guide).
    This is particularly useful when processing ZIP files that contain both
    types of images.
    
    Args:
        image_paths: List of paths to image files to classify
        classifier: Optional ImageClassifier instance. If None, creates a new
                   classifier with default thresholds.
        
    Returns:
        Tuple containing:
        - List of line art image paths
        - List of colored reference image paths
        - Dictionary mapping all image paths to their ImageType classification
        
    Raises:
        ValidationError: If image_paths is empty or contains invalid paths
        
    Example:
        >>> line_art, references, metadata = separate_line_art_and_references(
        ...     ['/path/page1.png', '/path/colored_ref.png']
        ... )
        >>> print(f"Line art: {len(line_art)}, References: {len(references)}")
        Line art: 1, References: 1
    """
    if not image_paths:
        error_msg = "Cannot separate images: image_paths list is empty"
        logger.error(error_msg)
        raise ValidationError(error_msg)
    
    logger.info(f"Separating {len(image_paths)} images into line art and references")
    
    # Create classifier if not provided
    if classifier is None:
        classifier = ImageClassifier()
        logger.debug("Created new ImageClassifier with default thresholds")
    
    # Classify all images in batch
    try:
        classifications = classifier.classify_batch(image_paths)
    except Exception as e:
        error_msg = f"Failed to classify images: {str(e)}"
        logger.error(error_msg)
        raise ValidationError(error_msg) from e
    
    # Separate into line art and references
    line_art_images: List[str] = []
    reference_images: List[str] = []
    
    for image_path, classification in classifications.items():
        if classification.type == "line_art":
            line_art_images.append(image_path)
            logger.debug(
                f"Classified as line art: {Path(image_path).name} "
                f"(confidence: {classification.confidence:.2f})"
            )
        elif classification.type == "colored":
            reference_images.append(image_path)
            logger.debug(
                f"Classified as colored reference: {Path(image_path).name} "
                f"(confidence: {classification.confidence:.2f})"
            )
        else:
            # This should not happen due to validation in ImageType
            logger.warning(
                f"Unknown classification type '{classification.type}' for {image_path}"
            )
    
    # Log summary
    logger.info(
        f"Separation complete: {len(line_art_images)} line art images, "
        f"{len(reference_images)} colored references"
    )
    
    # Log warning if no line art found
    if not line_art_images:
        logger.warning(
            "No line art images found - all images classified as colored references"
        )
    
    # Log warning if no references found
    if not reference_images:
        logger.warning(
            "No colored reference images found - all images classified as line art"
        )
    
    return line_art_images, reference_images, classifications

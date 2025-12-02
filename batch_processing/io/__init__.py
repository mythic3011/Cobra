"""
File I/O operations for batch processing.

This submodule handles file and directory operations including scanning,
validation, ZIP file handling, and output path management.
"""

from .zip_handler import (
    is_zip_file,
    extract_zip_file,
    cleanup_temp_directory,
    create_output_zip,
    SUPPORTED_IMAGE_FORMATS
)

from .file_handler import (
    scan_directory,
    validate_image_file,
    create_output_path,
    handle_filename_collision,
    separate_line_art_and_references
)

__all__ = [
    'is_zip_file',
    'extract_zip_file',
    'cleanup_temp_directory',
    'create_output_zip',
    'separate_line_art_and_references',
    'SUPPORTED_IMAGE_FORMATS',
    'scan_directory',
    'validate_image_file',
    'create_output_path',
    'handle_filename_collision'
]

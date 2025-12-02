#!/usr/bin/env python3
"""
CLI interface for batch colorization of comic line art.

This script provides a command-line interface to the Cobra batch processing
system, allowing users to colorize multiple images without requiring the GUI.

Usage:
    python batch_colorize.py --input-dir ./input --output-dir ./output \\
        --reference-dir ./references --style "line + shadow" --seed 0 \\
        --steps 10 --top-k 3

For more information, run:
    python batch_colorize.py --help
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import List, Optional
import time

from batch_processing.config import BatchConfig
from batch_processing.processor import BatchProcessor
from batch_processing.io.file_handler import scan_directory
from batch_processing.io.zip_handler import is_zip_file, extract_zip_file
from batch_processing.exceptions import BatchProcessingError, ConfigurationError, ValidationError
from batch_processing.logging_config import get_logger

logger = get_logger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments as argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Batch colorization of comic line art using Cobra",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic batch processing
  python batch_colorize.py --input-dir ./input --output-dir ./output \\
      --reference-dir ./references

  # With custom parameters
  python batch_colorize.py --input-dir ./input --output-dir ./output \\
      --reference-dir ./references --style "line + shadow" --seed 42 \\
      --steps 20 --top-k 5

  # Recursive directory scanning
  python batch_colorize.py --input-dir ./input --output-dir ./output \\
      --reference-dir ./references --recursive

  # Process ZIP file
  python batch_colorize.py --input-zip ./input.zip --output-dir ./output \\
      --reference-dir ./references

  # Output as ZIP
  python batch_colorize.py --input-dir ./input --output-zip ./output.zip \\
      --reference-dir ./references

  # Preview mode (process first image only)
  python batch_colorize.py --input-dir ./input --output-dir ./output \\
      --reference-dir ./references --preview

  # With configuration file
  python batch_colorize.py --input-dir ./input --output-dir ./output \\
      --reference-dir ./references --config config.json
        """
    )
    
    # Input/Output arguments
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input-dir",
        type=str,
        help="Directory containing input images to colorize"
    )
    input_group.add_argument(
        "--input-zip",
        type=str,
        help="ZIP file containing input images to colorize"
    )
    
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument(
        "--output-dir",
        type=str,
        help="Directory where colorized images will be saved"
    )
    output_group.add_argument(
        "--output-zip",
        type=str,
        help="ZIP file where colorized images will be packaged"
    )
    
    parser.add_argument(
        "--reference-dir",
        type=str,
        required=True,
        help="Directory containing reference images for colorization"
    )
    
    # Style and model parameters
    parser.add_argument(
        "--style",
        type=str,
        default="line + shadow",
        choices=["line", "line + shadow"],
        help="Style mode for line extraction (default: line + shadow)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducible results (default: 0)"
    )
    
    parser.add_argument(
        "--steps",
        type=int,
        default=10,
        help="Number of inference steps (default: 10)"
    )
    
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of top reference images to use (default: 3)"
    )
    
    # Processing options
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan input directory recursively for images"
    )
    
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files"
    )
    
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview mode: process only the first image"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to JSON configuration file for per-image settings"
    )
    
    # Logging options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )
    
    return parser.parse_args()


def validate_paths(args: argparse.Namespace) -> bool:
    """
    Validate that all specified paths exist and are accessible.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        True if all paths are valid
        
    Raises:
        ValidationError: If any path is invalid
    """
    # Validate input path
    if args.input_dir:
        input_path = Path(args.input_dir)
        if not input_path.exists():
            raise ValidationError(f"Input directory does not exist: {args.input_dir}")
        if not input_path.is_dir():
            raise ValidationError(f"Input path is not a directory: {args.input_dir}")
    
    if args.input_zip:
        input_path = Path(args.input_zip)
        if not input_path.exists():
            raise ValidationError(f"Input ZIP file does not exist: {args.input_zip}")
        if not input_path.is_file():
            raise ValidationError(f"Input ZIP path is not a file: {args.input_zip}")
        if not is_zip_file(str(input_path)):
            raise ValidationError(f"Input file is not a valid ZIP file: {args.input_zip}")
    
    # Validate reference directory
    ref_path = Path(args.reference_dir)
    if not ref_path.exists():
        raise ValidationError(f"Reference directory does not exist: {args.reference_dir}")
    if not ref_path.is_dir():
        raise ValidationError(f"Reference path is not a directory: {args.reference_dir}")
    
    # Check that reference directory contains images
    ref_images = scan_directory(str(ref_path), recursive=False)
    if not ref_images:
        raise ValidationError(f"No valid images found in reference directory: {args.reference_dir}")
    
    # Validate output path (create if doesn't exist for directory)
    if args.output_dir:
        output_path = Path(args.output_dir)
        if not output_path.exists():
            logger.info(f"Creating output directory: {args.output_dir}")
            output_path.mkdir(parents=True, exist_ok=True)
        elif not output_path.is_dir():
            raise ValidationError(f"Output path exists but is not a directory: {args.output_dir}")
    
    if args.output_zip:
        output_path = Path(args.output_zip)
        # Check parent directory exists
        if not output_path.parent.exists():
            logger.info(f"Creating output directory: {output_path.parent}")
            output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Validate config file if provided
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            raise ValidationError(f"Configuration file does not exist: {args.config}")
        if not config_path.is_file():
            raise ValidationError(f"Configuration path is not a file: {args.config}")
    
    return True


def validate_parameters(args: argparse.Namespace) -> bool:
    """
    Validate parameter ranges and values.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        True if all parameters are valid
        
    Raises:
        ValidationError: If any parameter is invalid
    """
    # Validate seed
    if args.seed < 0:
        raise ValidationError(f"Seed must be non-negative, got: {args.seed}")
    
    # Validate steps
    if args.steps < 1:
        raise ValidationError(f"Steps must be at least 1, got: {args.steps}")
    if args.steps > 100:
        logger.warning(f"Steps value is very high ({args.steps}), this may take a long time")
    
    # Validate top_k
    if args.top_k < 1:
        raise ValidationError(f"Top-k must be at least 1, got: {args.top_k}")
    if args.top_k > 50:
        logger.warning(f"Top-k value is very high ({args.top_k}), this may not improve results")
    
    # Validate mutually exclusive flags
    if args.verbose and args.quiet:
        raise ValidationError("Cannot specify both --verbose and --quiet")
    
    return True


def setup_batch_processor(args: argparse.Namespace) -> BatchProcessor:
    """
    Create and configure a BatchProcessor from CLI arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Configured BatchProcessor instance
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Determine input and output paths
    if args.input_dir:
        input_dir = args.input_dir
        input_is_zip = False
    else:
        # For ZIP input, we'll extract to a temp directory
        input_dir = args.input_zip
        input_is_zip = True
    
    if args.output_dir:
        output_dir = args.output_dir
        output_as_zip = False
        zip_output_name = None
    else:
        # For ZIP output, use parent directory and set ZIP name
        output_path = Path(args.output_zip)
        output_dir = str(output_path.parent)
        output_as_zip = True
        zip_output_name = output_path.name
    
    # Scan reference directory for images
    logger.info(f"Scanning reference directory: {args.reference_dir}")
    reference_images = scan_directory(args.reference_dir, recursive=False)
    logger.info(f"Found {len(reference_images)} reference images")
    
    # Create batch configuration
    config = BatchConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        reference_images=reference_images,
        style=args.style,
        seed=args.seed,
        num_inference_steps=args.steps,
        top_k=args.top_k,
        recursive=args.recursive,
        overwrite=args.overwrite,
        preview_mode=args.preview,
        max_concurrent=1,  # CLI always processes sequentially
        input_is_zip=input_is_zip,
        output_as_zip=output_as_zip,
        zip_output_name=zip_output_name
    )
    
    # Create batch processor
    processor = BatchProcessor(config)
    
    # Load configuration file if provided
    if args.config:
        logger.info(f"Loading configuration from: {args.config}")
        from batch_processing.config import ConfigurationHandler
        config_handler = ConfigurationHandler()
        config_handler.load_config_file(args.config)
        # Note: Per-image configs will be applied during processing
    
    return processor


def display_progress(processor: BatchProcessor) -> None:
    """
    Display processing progress to stdout.
    
    Args:
        processor: BatchProcessor instance
    """
    status = processor.get_status()
    summary = status["summary"]
    
    # Calculate progress percentage
    if summary.total > 0:
        progress_pct = (summary.completed + summary.failed) / summary.total * 100
    else:
        progress_pct = 0
    
    # Build progress message
    progress_msg = (
        f"Progress: {summary.completed + summary.failed}/{summary.total} "
        f"({progress_pct:.1f}%) | "
        f"Completed: {summary.completed} | "
        f"Failed: {summary.failed} | "
        f"Pending: {summary.pending}"
    )
    
    if summary.elapsed_time:
        progress_msg += f" | Elapsed: {summary.elapsed_time:.1f}s"
    
    # Print progress (overwrite previous line)
    print(f"\r{progress_msg}", end="", flush=True)


def run_batch_processing(processor: BatchProcessor, args: argparse.Namespace) -> int:
    """
    Run the batch processing operation.
    
    Args:
        processor: Configured BatchProcessor instance
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Scan for input images
        if args.input_zip:
            logger.info(f"Extracting ZIP file: {args.input_zip}")
            # Extract ZIP to temporary directory
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix="cobra_batch_")
            extracted_files = extract_zip_file(args.input_zip, temp_dir)
            input_images = extracted_files
            logger.info(f"Extracted {len(input_images)} images from ZIP")
        else:
            logger.info(f"Scanning input directory: {args.input_dir}")
            input_images = scan_directory(
                args.input_dir,
                recursive=args.recursive
            )
            logger.info(f"Found {len(input_images)} images to process")
        
        if not input_images:
            logger.error("No valid images found to process")
            return 1
        
        # Add images to processor
        logger.info("Adding images to processing queue")
        processor.add_images(input_images)
        
        # Display initial status
        if not args.quiet:
            print(f"\nStarting batch processing of {len(input_images)} images")
            print(f"Style: {args.style}")
            print(f"Seed: {args.seed}")
            print(f"Steps: {args.steps}")
            print(f"Top-K: {args.top_k}")
            print(f"Reference images: {len(processor.config.reference_images)}")
            print()
        
        # Start processing
        start_time = time.time()
        
        # Process images
        processor.start_processing()
        
        # Display progress periodically (in a real implementation, this would be in a separate thread)
        # For now, we'll just display final status
        
        # Get final status
        status = processor.get_status()
        summary = status["summary"]
        
        elapsed_time = time.time() - start_time
        
        # Display final results
        if not args.quiet:
            print()  # New line after progress
            print("\n" + "=" * 60)
            print("Batch Processing Complete")
            print("=" * 60)
            print(f"Total images: {summary.total}")
            print(f"Completed: {summary.completed}")
            print(f"Failed: {summary.failed}")
            print(f"Success rate: {summary.success_rate:.1f}%")
            print(f"Total time: {elapsed_time:.2f} seconds")
            
            if summary.completed > 0:
                avg_time = elapsed_time / summary.completed
                print(f"Average time per image: {avg_time:.2f} seconds")
            
            if args.output_dir:
                print(f"\nOutput directory: {args.output_dir}")
            elif args.output_zip:
                print(f"\nOutput ZIP: {args.output_zip}")
            
            print("=" * 60)
        
        # Return appropriate exit code
        if summary.failed > 0:
            logger.warning(f"{summary.failed} images failed to process")
            return 2  # Partial failure
        else:
            logger.info("All images processed successfully")
            return 0  # Success
    
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        print("\n\nProcessing interrupted by user")
        return 130  # Standard exit code for SIGINT
    
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}", exc_info=True)
        if not args.quiet:
            print(f"\nError: {str(e)}", file=sys.stderr)
        return 1  # General failure


def main() -> int:
    """
    Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Configure logging
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG)
        elif args.quiet:
            logging.basicConfig(level=logging.ERROR)
        else:
            logging.basicConfig(level=logging.INFO)
        
        # Validate paths
        logger.info("Validating paths")
        validate_paths(args)
        
        # Validate parameters
        logger.info("Validating parameters")
        validate_parameters(args)
        
        # Setup batch processor
        logger.info("Setting up batch processor")
        processor = setup_batch_processor(args)
        
        # Run batch processing
        logger.info("Starting batch processing")
        exit_code = run_batch_processing(processor, args)
        
        return exit_code
    
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        print(f"Error: {str(e)}", file=sys.stderr)
        print("\nRun with --help for usage information", file=sys.stderr)
        return 1
    
    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
        print(f"Error: {str(e)}", file=sys.stderr)
        print("\nRun with --help for usage information", file=sys.stderr)
        return 1
    
    except BatchProcessingError as e:
        logger.error(f"Batch processing error: {str(e)}")
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

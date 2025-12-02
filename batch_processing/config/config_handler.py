"""
Configuration management for batch processing.

This module provides the BatchConfig dataclass for storing configuration
and the ConfigurationHandler class for loading, validating, and merging
configuration from files and defaults.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..exceptions import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """
    Configuration for batch processing operations.
    
    This dataclass holds all configuration parameters needed for batch
    processing, including input/output paths, model parameters, and
    processing options.
    
    Attributes:
        input_dir: Directory containing input images
        output_dir: Directory where processed images will be saved
        reference_images: List of paths to reference images for colorization
        style: Style mode for colorization (e.g., "line", "line + shadow")
        seed: Random seed for reproducible results
        num_inference_steps: Number of diffusion steps
        top_k: Number of top reference images to use
        recursive: Whether to scan input directory recursively
        overwrite: Whether to overwrite existing output files
        preview_mode: Whether to process only first image for preview
        max_concurrent: Maximum number of images to process concurrently
        input_is_zip: Whether input is a ZIP file
        output_as_zip: Whether to package output as ZIP file
        zip_output_name: Name for output ZIP file (if output_as_zip is True)
    """
    input_dir: str
    output_dir: str
    reference_images: List[str]
    style: str = "line + shadow"
    seed: int = 0
    num_inference_steps: int = 10
    top_k: int = 3
    recursive: bool = False
    overwrite: bool = False
    preview_mode: bool = False
    max_concurrent: int = 1
    input_is_zip: bool = False
    output_as_zip: bool = False
    zip_output_name: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate paths
        if not self.input_dir:
            raise ConfigurationError("input_dir cannot be empty")
        if not self.output_dir:
            raise ConfigurationError("output_dir cannot be empty")
        
        # Validate style
        valid_styles = ["line", "line + shadow"]
        if self.style not in valid_styles:
            raise ConfigurationError(
                f"Invalid style: {self.style}. Must be one of {valid_styles}"
            )
        
        # Validate numeric parameters
        if self.seed < 0:
            raise ConfigurationError(f"seed must be non-negative, got {self.seed}")
        
        if self.num_inference_steps < 1:
            raise ConfigurationError(
                f"num_inference_steps must be at least 1, got {self.num_inference_steps}"
            )
        
        if self.top_k < 1:
            raise ConfigurationError(
                f"top_k must be at least 1, got {self.top_k}"
            )
        
        if self.max_concurrent < 1:
            raise ConfigurationError(
                f"max_concurrent must be at least 1, got {self.max_concurrent}"
            )
        
        # Validate ZIP options
        if self.output_as_zip and not self.zip_output_name:
            # Generate default ZIP name from output directory
            self.zip_output_name = Path(self.output_dir).name + "_colorized.zip"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        return {
            "input_dir": self.input_dir,
            "output_dir": self.output_dir,
            "reference_images": self.reference_images,
            "style": self.style,
            "seed": self.seed,
            "num_inference_steps": self.num_inference_steps,
            "top_k": self.top_k,
            "recursive": self.recursive,
            "overwrite": self.overwrite,
            "preview_mode": self.preview_mode,
            "max_concurrent": self.max_concurrent,
            "input_is_zip": self.input_is_zip,
            "output_as_zip": self.output_as_zip,
            "zip_output_name": self.zip_output_name,
        }


class ConfigurationHandler:
    """
    Handles configuration loading, validation, and merging.
    
    This class provides methods to:
    - Load configuration from JSON files
    - Validate configuration parameters
    - Merge default and per-image configurations
    - Handle configuration errors gracefully
    """
    
    def __init__(self):
        """Initialize the configuration handler."""
        self._config_cache: Dict[str, Dict] = {}
        self._default_config: Dict[str, Any] = {}
        self._image_configs: Dict[str, Dict[str, Any]] = {}
    
    def load_config_file(self, path: str) -> Dict[str, Any]:
        """
        Load configuration from a JSON file.
        
        The configuration file should have the following structure:
        {
            "default": {
                "style": "line + shadow",
                "seed": 0,
                ...
            },
            "images": {
                "image1.png": {
                    "seed": 42,
                    ...
                },
                ...
            }
        }
        
        This method handles errors gracefully:
        - JSON parsing errors are caught and reported
        - Invalid configuration values are logged and replaced with defaults
        - Missing sections are handled without crashing
        
        Args:
            path: Path to the JSON configuration file
            
        Returns:
            Dictionary containing the parsed configuration
            
        Raises:
            ConfigurationError: If file cannot be read or has critical errors
        """
        config_path = Path(path)
        
        # Check file existence
        if not config_path.exists():
            error_msg = f"Configuration file not found: {path}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        if not config_path.is_file():
            error_msg = f"Configuration path is not a file: {path}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        # Try to read and parse the file
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            error_msg = (
                f"Failed to parse JSON configuration file {path}: {e}\n"
                f"Line {e.lineno}, Column {e.colno}: {e.msg}"
            )
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        except UnicodeDecodeError as e:
            error_msg = f"Configuration file has invalid encoding (expected UTF-8): {path}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        except PermissionError:
            error_msg = f"Permission denied reading configuration file: {path}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        except Exception as e:
            error_msg = f"Failed to read configuration file {path}: {e}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        # Validate structure
        if not isinstance(config_data, dict):
            error_msg = (
                f"Configuration file must contain a JSON object, "
                f"got {type(config_data).__name__}"
            )
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        # Extract default and per-image configs with error handling
        try:
            self._default_config = config_data.get("default", {})
            
            # Validate default config structure
            if self._default_config and not isinstance(self._default_config, dict):
                logger.warning(
                    f"'default' section must be an object, got {type(self._default_config).__name__}. "
                    f"Using empty default config."
                )
                self._default_config = {}
            
            # Sanitize default config values
            self._default_config = self._sanitize_config(self._default_config, "default")
            
        except Exception as e:
            logger.error(f"Error processing default config: {e}. Using empty default config.")
            self._default_config = {}
        
        try:
            self._image_configs = config_data.get("images", {})
            
            # Validate images config structure
            if self._image_configs and not isinstance(self._image_configs, dict):
                logger.warning(
                    f"'images' section must be an object, got {type(self._image_configs).__name__}. "
                    f"Using empty images config."
                )
                self._image_configs = {}
            
            # Sanitize each image config
            sanitized_image_configs = {}
            for image_name, image_config in self._image_configs.items():
                if not isinstance(image_config, dict):
                    logger.warning(
                        f"Config for image '{image_name}' must be an object, "
                        f"got {type(image_config).__name__}. Skipping this image config."
                    )
                    continue
                
                sanitized_config = self._sanitize_config(image_config, f"image '{image_name}'")
                sanitized_image_configs[image_name] = sanitized_config
            
            self._image_configs = sanitized_image_configs
            
        except Exception as e:
            logger.error(f"Error processing image configs: {e}. Using empty image configs.")
            self._image_configs = {}
        
        logger.info(f"Loaded configuration from {path}")
        logger.debug(f"Default config: {self._default_config}")
        logger.debug(f"Per-image configs: {len(self._image_configs)} images")
        
        return config_data
    
    def _sanitize_config(self, config: Dict[str, Any], context: str) -> Dict[str, Any]:
        """
        Sanitize configuration values, replacing invalid values with defaults.
        
        This method validates each configuration parameter and replaces
        invalid values with sensible defaults, logging warnings for each
        replacement.
        
        Args:
            config: Configuration dictionary to sanitize
            context: Description of where this config came from (for logging)
            
        Returns:
            Sanitized configuration dictionary
        """
        sanitized = {}
        
        # Define defaults for each parameter
        defaults = {
            "style": "line + shadow",
            "seed": 0,
            "num_inference_steps": 10,
            "top_k": 3,
            "recursive": False,
            "overwrite": False,
            "preview_mode": False,
            "max_concurrent": 1,
        }
        
        # Define valid ranges
        valid_styles = ["line", "line + shadow"]
        
        for key, value in config.items():
            try:
                # Validate style
                if key == "style":
                    if not isinstance(value, str):
                        logger.warning(
                            f"Invalid type for 'style' in {context}: "
                            f"expected str, got {type(value).__name__}. "
                            f"Using default: {defaults['style']}"
                        )
                        sanitized[key] = defaults["style"]
                    elif value not in valid_styles:
                        logger.warning(
                            f"Invalid value for 'style' in {context}: '{value}'. "
                            f"Must be one of {valid_styles}. "
                            f"Using default: {defaults['style']}"
                        )
                        sanitized[key] = defaults["style"]
                    else:
                        sanitized[key] = value
                
                # Validate numeric parameters
                elif key in ["seed", "num_inference_steps", "top_k", "max_concurrent"]:
                    if not isinstance(value, int):
                        logger.warning(
                            f"Invalid type for '{key}' in {context}: "
                            f"expected int, got {type(value).__name__}. "
                            f"Using default: {defaults[key]}"
                        )
                        sanitized[key] = defaults[key]
                    else:
                        # Check ranges
                        if key == "seed" and value < 0:
                            logger.warning(
                                f"Invalid value for 'seed' in {context}: {value}. "
                                f"Must be non-negative. Using default: {defaults['seed']}"
                            )
                            sanitized[key] = defaults["seed"]
                        elif key in ["num_inference_steps", "top_k", "max_concurrent"] and value < 1:
                            logger.warning(
                                f"Invalid value for '{key}' in {context}: {value}. "
                                f"Must be at least 1. Using default: {defaults[key]}"
                            )
                            sanitized[key] = defaults[key]
                        else:
                            sanitized[key] = value
                
                # Validate boolean parameters
                elif key in ["recursive", "overwrite", "preview_mode"]:
                    if not isinstance(value, bool):
                        logger.warning(
                            f"Invalid type for '{key}' in {context}: "
                            f"expected bool, got {type(value).__name__}. "
                            f"Using default: {defaults[key]}"
                        )
                        sanitized[key] = defaults[key]
                    else:
                        sanitized[key] = value
                
                # Validate reference_images
                elif key == "reference_images":
                    if not isinstance(value, list):
                        logger.warning(
                            f"Invalid type for 'reference_images' in {context}: "
                            f"expected list, got {type(value).__name__}. Skipping."
                        )
                    else:
                        # Validate each reference path
                        valid_refs = []
                        for ref in value:
                            if not isinstance(ref, str):
                                logger.warning(
                                    f"Invalid reference image in {context}: "
                                    f"expected str, got {type(ref).__name__}. Skipping this reference."
                                )
                            else:
                                valid_refs.append(ref)
                        
                        if valid_refs:
                            sanitized[key] = valid_refs
                        else:
                            logger.warning(
                                f"No valid reference images in {context}. Skipping reference_images."
                            )
                
                # Unknown parameter - keep it but log warning
                else:
                    logger.debug(f"Unknown configuration parameter '{key}' in {context}. Keeping as-is.")
                    sanitized[key] = value
                    
            except Exception as e:
                logger.error(
                    f"Error sanitizing parameter '{key}' in {context}: {e}. "
                    f"Skipping this parameter."
                )
        
        return sanitized
    
    def get_image_config(self, image_path: str) -> Dict[str, Any]:
        """
        Get configuration for a specific image.
        
        This method returns the merged configuration for an image,
        combining default settings with any image-specific overrides.
        
        Args:
            image_path: Path to the image (can be absolute or just filename)
            
        Returns:
            Dictionary containing the merged configuration for the image
        """
        # Extract just the filename for lookup
        image_name = Path(image_path).name
        
        # Get image-specific config if it exists
        image_config = self._image_configs.get(image_name, {})
        
        # Merge with defaults
        merged_config = self.merge_configs(self._default_config, image_config)
        
        logger.debug(f"Config for {image_name}: {merged_config}")
        
        return merged_config
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate a configuration dictionary.
        
        This method checks that all configuration values are valid
        and within acceptable ranges. It collects all validation errors
        and reports them together.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid (with all errors listed)
        """
        if not isinstance(config, dict):
            raise ConfigurationError(
                f"Configuration must be a dictionary, got {type(config).__name__}"
            )
        
        # Collect all validation errors
        errors = []
        
        # Validate style if present
        if "style" in config:
            valid_styles = ["line", "line + shadow"]
            try:
                if not isinstance(config["style"], str):
                    errors.append(
                        f"'style' must be a string, got {type(config['style']).__name__}"
                    )
                elif config["style"] not in valid_styles:
                    errors.append(
                        f"Invalid style: '{config['style']}'. Must be one of {valid_styles}"
                    )
            except Exception as e:
                errors.append(f"Error validating 'style': {e}")
        
        # Validate numeric parameters
        numeric_params = {
            "seed": (0, None),  # (min, max) - None means no max
            "num_inference_steps": (1, None),
            "top_k": (1, None),
            "max_concurrent": (1, None),
        }
        
        for param, (min_val, max_val) in numeric_params.items():
            if param in config:
                try:
                    value = config[param]
                    if not isinstance(value, int):
                        errors.append(
                            f"'{param}' must be an integer, got {type(value).__name__}"
                        )
                    elif value < min_val:
                        errors.append(
                            f"'{param}' must be at least {min_val}, got {value}"
                        )
                    elif max_val is not None and value > max_val:
                        errors.append(
                            f"'{param}' must be at most {max_val}, got {value}"
                        )
                except Exception as e:
                    errors.append(f"Error validating '{param}': {e}")
        
        # Validate boolean parameters
        boolean_params = [
            "recursive", "overwrite", "preview_mode",
            "input_is_zip", "output_as_zip"
        ]
        
        for param in boolean_params:
            if param in config:
                try:
                    if not isinstance(config[param], bool):
                        errors.append(
                            f"'{param}' must be a boolean, got {type(config[param]).__name__}"
                        )
                except Exception as e:
                    errors.append(f"Error validating '{param}': {e}")
        
        # Validate reference_images if present
        if "reference_images" in config:
            try:
                if not isinstance(config["reference_images"], list):
                    errors.append(
                        f"'reference_images' must be a list, "
                        f"got {type(config['reference_images']).__name__}"
                    )
                else:
                    for i, ref in enumerate(config["reference_images"]):
                        if not isinstance(ref, str):
                            errors.append(
                                f"reference_images[{i}] must be a string path, "
                                f"got {type(ref).__name__}"
                            )
            except Exception as e:
                errors.append(f"Error validating 'reference_images': {e}")
        
        # If there are errors, raise with all of them
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        return True
    
    def merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge default and override configurations.
        
        Override values take precedence over default values.
        For list values (like reference_images), override completely replaces default.
        
        Args:
            default: Default configuration dictionary
            override: Override configuration dictionary
            
        Returns:
            Merged configuration dictionary
        """
        merged = default.copy()
        
        for key, value in override.items():
            merged[key] = value
        
        return merged
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get the default configuration.
        
        Returns:
            Dictionary containing default configuration
        """
        return self._default_config.copy()
    
    def has_image_config(self, image_path: str) -> bool:
        """
        Check if a specific image has custom configuration.
        
        Args:
            image_path: Path to the image
            
        Returns:
            True if image has custom configuration, False otherwise
        """
        image_name = Path(image_path).name
        return image_name in self._image_configs
    
    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._config_cache.clear()
        self._default_config.clear()
        self._image_configs.clear()
        logger.debug("Configuration cache cleared")

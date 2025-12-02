"""
Image classification for distinguishing line art from colored references.

This module provides automatic classification of images based on color analysis
and edge detection to separate line art (to be colorized) from colored reference
images (to be used as style guides).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import numpy as np
from PIL import Image
import cv2

from ..logging_config import get_logger
from ..exceptions import ImageProcessingError

logger = get_logger(__name__)


@dataclass
class ImageType:
    """Classification result for an image."""
    
    type: str  # "line_art" or "colored"
    confidence: float
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the classification result."""
        if self.type not in ["line_art", "colored"]:
            raise ValueError(f"Invalid image type: {self.type}")
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")


class ImageClassifier:
    """Classifies images as line art or colored references.
    
    Uses color saturation analysis, unique color counting, and edge density
    calculation to determine whether an image is line art (suitable for
    colorization) or a colored reference (suitable as a style guide).
    
    Attributes:
        saturation_threshold: Threshold for average saturation (0-1 scale)
        color_count_threshold: Threshold for number of unique colors
        edge_ratio_threshold: Threshold for edge density ratio
    """
    
    def __init__(
        self,
        saturation_threshold: float = 0.15,
        color_count_threshold: int = 1000,
        edge_ratio_threshold: float = 0.3
    ):
        """Initialize the image classifier with thresholds.
        
        Args:
            saturation_threshold: Images with saturation below this are more
                likely to be line art (default: 0.15)
            color_count_threshold: Images with fewer unique colors than this
                are more likely to be line art (default: 1000)
            edge_ratio_threshold: Images with edge density above this are more
                likely to be line art (default: 0.3)
        """
        self.saturation_threshold = saturation_threshold
        self.color_count_threshold = color_count_threshold
        self.edge_ratio_threshold = edge_ratio_threshold
        self._classification_cache: Dict[str, ImageType] = {}
        
        logger.info(
            f"ImageClassifier initialized with thresholds: "
            f"saturation={saturation_threshold}, "
            f"color_count={color_count_threshold}, "
            f"edge_ratio={edge_ratio_threshold}"
        )
    
    def analyze_color_saturation(self, image: Image.Image) -> float:
        """Analyze the average color saturation of an image.
        
        Converts the image to HSV color space and calculates the mean
        saturation value across all pixels.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            Average saturation value between 0 and 1
        """
        # Convert PIL Image to numpy array
        img_array = np.array(image)
        
        # Handle grayscale images
        if len(img_array.shape) == 2:
            return 0.0
        
        # Handle RGBA images by removing alpha channel
        if img_array.shape[2] == 4:
            img_array = img_array[:, :, :3]
        
        # Convert RGB to HSV
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        
        # Extract saturation channel (index 1) and normalize to 0-1
        saturation = hsv[:, :, 1] / 255.0
        
        # Calculate mean saturation
        mean_saturation = float(np.mean(saturation))
        
        logger.debug(f"Calculated saturation: {mean_saturation:.4f}")
        return mean_saturation
    
    def count_unique_colors(self, image: Image.Image) -> int:
        """Count the number of unique colors in an image.
        
        Reduces the image to a reasonable size for performance, then counts
        unique RGB color combinations.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            Number of unique colors found
        """
        # Resize image for performance (max 256x256)
        max_size = 256
        if image.width > max_size or image.height > max_size:
            image = image.copy()
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Reshape to list of RGB tuples
        pixels = img_array.reshape(-1, 3)
        
        # Count unique colors
        unique_colors = len(np.unique(pixels, axis=0))
        
        logger.debug(f"Counted unique colors: {unique_colors}")
        return unique_colors
    
    def calculate_edge_density(self, image: Image.Image) -> float:
        """Calculate the edge density of an image.
        
        Uses Canny edge detection to find edges, then calculates the ratio
        of edge pixels to total pixels.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            Edge density ratio between 0 and 1
        """
        # Convert to grayscale
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image
        
        # Convert to numpy array
        img_array = np.array(gray)
        
        # Apply Canny edge detection
        # Using adaptive thresholds based on image statistics
        median = np.median(img_array)
        lower = int(max(0, 0.7 * median))
        upper = int(min(255, 1.3 * median))
        
        edges = cv2.Canny(img_array, lower, upper)
        
        # Calculate edge density
        edge_pixels = np.count_nonzero(edges)
        total_pixels = edges.size
        edge_density = edge_pixels / total_pixels
        
        logger.debug(f"Calculated edge density: {edge_density:.4f}")
        return float(edge_density)
    
    def classify(self, image_path: str) -> ImageType:
        """Classify a single image as line art or colored reference.
        
        Uses a scoring system based on three metrics:
        - Color saturation (low = line art)
        - Unique color count (low = line art)
        - Edge density (high = line art)
        
        An image needs to score 2 or more "line art" indicators to be
        classified as line art.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            ImageType with classification result and confidence
            
        Raises:
            ImageProcessingError: If the image cannot be loaded or processed
        """
        # Check cache first
        cache_key = str(Path(image_path).resolve())
        if cache_key in self._classification_cache:
            logger.debug(f"Using cached classification for {image_path}")
            return self._classification_cache[cache_key]
        
        try:
            # Load image
            image = Image.open(image_path)
            
            # Calculate metrics
            saturation = self.analyze_color_saturation(image)
            color_count = self.count_unique_colors(image)
            edge_density = self.calculate_edge_density(image)
            
            # Store metrics
            metrics = {
                "saturation": saturation,
                "color_count": float(color_count),
                "edge_density": edge_density
            }
            
            # Scoring system with weighted criteria
            # Saturation is the most important indicator
            line_art_score = 0
            
            has_low_saturation = saturation < self.saturation_threshold
            has_low_colors = color_count < self.color_count_threshold
            has_high_edges = edge_density > self.edge_ratio_threshold
            
            if has_low_saturation:
                line_art_score += 1
                logger.debug(f"Low saturation indicator: {saturation:.4f} < {self.saturation_threshold}")
            
            if has_low_colors:
                line_art_score += 1
                logger.debug(f"Low color count indicator: {color_count} < {self.color_count_threshold}")
            
            if has_high_edges:
                line_art_score += 1
                logger.debug(f"High edge density indicator: {edge_density:.4f} > {self.edge_ratio_threshold}")
            
            # Classification logic:
            # - If saturation is very low (<15%), it's likely line art even if other metrics disagree
            # - Otherwise, need at least 2 out of 3 criteria for line art
            # - For colored images, saturation should be high (>15%)
            
            if has_low_saturation and line_art_score >= 1:
                # Low saturation + at least one other indicator = line art
                image_type = "line_art"
                confidence = line_art_score / 3.0
            elif line_art_score >= 2:
                # At least 2 indicators = line art
                image_type = "line_art"
                confidence = line_art_score / 3.0
            else:
                # Otherwise it's colored
                # But if saturation is low, reduce confidence
                image_type = "colored"
                confidence = 1.0 - (line_art_score / 3.0)
                if has_low_saturation:
                    # Penalize confidence if saturation is low but classified as colored
                    confidence *= 0.7
            
            result = ImageType(
                type=image_type,
                confidence=confidence,
                metrics=metrics
            )
            
            # Cache the result
            self._classification_cache[cache_key] = result
            
            logger.info(
                f"Classified {Path(image_path).name} as {image_type} "
                f"(confidence: {confidence:.2f}, score: {line_art_score}/3)"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to classify image {image_path}: {str(e)}"
            logger.error(error_msg)
            raise ImageProcessingError(image_path, error_msg) from e
    
    def classify_batch(self, image_paths: List[str]) -> Dict[str, ImageType]:
        """Classify multiple images in batch.
        
        Processes each image and returns a dictionary mapping image paths
        to their classification results. Uses caching to avoid reprocessing.
        
        Args:
            image_paths: List of paths to image files
            
        Returns:
            Dictionary mapping image paths to ImageType results
        """
        logger.info(f"Starting batch classification of {len(image_paths)} images")
        
        results = {}
        for image_path in image_paths:
            try:
                result = self.classify(image_path)
                results[image_path] = result
            except ImageProcessingError as e:
                logger.warning(f"Skipping image due to classification error: {e}")
                continue
        
        # Log summary
        line_art_count = sum(1 for r in results.values() if r.type == "line_art")
        colored_count = len(results) - line_art_count
        
        logger.info(
            f"Batch classification complete: {line_art_count} line art, "
            f"{colored_count} colored references"
        )
        
        return results
    
    def get_classification_confidence(self, image_path: str) -> float:
        """Get the classification confidence for an image.
        
        If the image has been classified before, returns the cached confidence.
        Otherwise, classifies the image first.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Confidence value between 0 and 1
        """
        result = self.classify(image_path)
        return result.confidence
    
    def clear_cache(self) -> None:
        """Clear the classification cache."""
        cache_size = len(self._classification_cache)
        self._classification_cache.clear()
        logger.debug(f"Cleared classification cache ({cache_size} entries)")

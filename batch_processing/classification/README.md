# Image Classification Module

This module provides automatic classification of images as line art or colored references for the Cobra batch processing system.

## Overview

The `ImageClassifier` analyzes images using three key metrics to determine whether they are line art (suitable for colorization) or colored references (suitable as style guides):

1. **Color Saturation**: Measures the average saturation in HSV color space
2. **Unique Color Count**: Counts distinct RGB color combinations
3. **Edge Density**: Calculates the ratio of edge pixels using Canny edge detection

## Usage

### Basic Classification

```python
from batch_processing.classification import ImageClassifier

# Initialize classifier with default thresholds
classifier = ImageClassifier()

# Classify a single image
result = classifier.classify("path/to/image.png")
print(f"Type: {result.type}")  # "line_art" or "colored"
print(f"Confidence: {result.confidence}")  # 0.0 to 1.0
print(f"Metrics: {result.metrics}")
```

### Batch Classification

```python
# Classify multiple images at once
image_paths = ["image1.png", "image2.png", "image3.png"]
results = classifier.classify_batch(image_paths)

for path, result in results.items():
    print(f"{path}: {result.type} ({result.confidence:.2f})")
```

### Custom Thresholds

```python
# Adjust thresholds for different image types
classifier = ImageClassifier(
    saturation_threshold=0.20,      # Higher = more strict for line art
    color_count_threshold=1500,     # Higher = more strict for line art
    edge_ratio_threshold=0.25       # Lower = more strict for line art
)
```

## Classification Algorithm

The classifier uses a scoring system:

- **Line Art Score = 0-3** based on:
  - Saturation < 0.15 → +1 point
  - Color count < 1000 → +1 point
  - Edge density > 0.3 → +1 point

- **Classification**:
  - Score ≥ 2 → Line Art (confidence = score/3)
  - Score < 2 → Colored (confidence = 1 - score/3)

## Features

- **Automatic caching**: Results are cached to avoid reprocessing
- **Batch processing**: Efficiently process multiple images
- **Confidence scoring**: Provides confidence level for each classification
- **Detailed metrics**: Returns all three analysis metrics for inspection
- **Error handling**: Gracefully handles invalid images with proper logging

## Example Results

### Line Art Image
```
Type: line_art
Confidence: 0.67
Metrics:
  - saturation: 0.0000
  - color_count: 151
  - edge_density: 0.0271
```

### Colored Reference Image
```
Type: colored
Confidence: 1.00
Metrics:
  - saturation: 0.4392
  - color_count: 27533
  - edge_density: 0.1091
```

## API Reference

### ImageClassifier

#### `__init__(saturation_threshold=0.15, color_count_threshold=1000, edge_ratio_threshold=0.3)`
Initialize the classifier with custom thresholds.

#### `classify(image_path: str) -> ImageType`
Classify a single image. Results are cached automatically.

#### `classify_batch(image_paths: List[str]) -> Dict[str, ImageType]`
Classify multiple images in batch. Returns a dictionary mapping paths to results.

#### `get_classification_confidence(image_path: str) -> float`
Get the confidence score for an image (classifies if not already cached).

#### `clear_cache() -> None`
Clear the classification cache.

### ImageType

A dataclass containing classification results:

- `type: str` - Either "line_art" or "colored"
- `confidence: float` - Confidence score between 0 and 1
- `metrics: Dict[str, float]` - Dictionary with saturation, color_count, and edge_density

## Implementation Details

- Uses OpenCV for edge detection (Canny algorithm)
- Uses PIL for image loading and color analysis
- Converts images to HSV for saturation analysis
- Resizes images to 256x256 for color counting (performance optimization)
- Adaptive Canny thresholds based on image median intensity

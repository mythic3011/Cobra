"""
Image classification for batch processing.

This submodule handles automatic classification of images as line art
or colored references based on color analysis and edge detection.
"""

from .classifier import ImageClassifier, ImageType

__all__ = [
    "ImageClassifier",
    "ImageType",
]

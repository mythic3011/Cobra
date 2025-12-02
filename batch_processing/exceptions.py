"""
Exception classes for batch processing operations.

This module defines the exception hierarchy for the batch processing system,
providing specific error types for different failure scenarios.
"""


class BatchProcessingError(Exception):
    """
    Base exception for all batch processing errors.
    
    This is the root exception class that all other batch processing
    exceptions inherit from. It can be used to catch any batch processing
    related error.
    """
    pass


class ImageProcessingError(BatchProcessingError):
    """
    Exception raised when an error occurs processing a specific image.
    
    This exception includes the image path to help identify which image
    failed during batch processing.
    
    Attributes:
        image_path: Path to the image that failed processing
        message: Description of the error
    """
    
    def __init__(self, image_path: str, message: str):
        """
        Initialize ImageProcessingError.
        
        Args:
            image_path: Path to the image that failed
            message: Error message describing what went wrong
        """
        self.image_path = image_path
        self.message = message
        super().__init__(f"Error processing {image_path}: {message}")


class ConfigurationError(BatchProcessingError):
    """
    Exception raised when configuration is invalid or malformed.
    
    This exception is raised when:
    - Configuration files cannot be parsed
    - Required configuration values are missing
    - Configuration values are invalid or out of range
    """
    pass


class ResourceError(BatchProcessingError):
    """
    Exception raised when system resources are insufficient or unavailable.
    
    This exception is raised when:
    - Out of memory errors occur
    - GPU resources are unavailable
    - Disk space is insufficient
    - File system permissions prevent operations
    """
    pass


class QueueError(BatchProcessingError):
    """
    Exception raised when queue operations fail.
    
    This exception is raised when:
    - Queue is empty when dequeue is attempted
    - Queue capacity is exceeded
    - Invalid queue operations are attempted
    """
    pass


class ValidationError(BatchProcessingError):
    """
    Exception raised when input validation fails.
    
    This exception is raised when:
    - Image files are invalid or corrupted
    - File paths don't exist
    - File formats are unsupported
    - Input parameters are out of valid ranges
    """
    pass


class ZIPExtractionError(BatchProcessingError):
    """
    Exception raised when ZIP file extraction fails.
    
    This exception is raised when:
    - ZIP file is corrupted or invalid
    - Extraction directory cannot be created
    - Insufficient permissions for extraction
    """
    pass


class ClassificationError(BatchProcessingError):
    """
    Exception raised when image classification fails.
    
    This exception is raised when:
    - Image cannot be analyzed for classification
    - Classification metrics cannot be computed
    """
    pass

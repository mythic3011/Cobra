"""
Memory management for batch processing operations.

This module provides the MemoryManager class for efficient GPU memory
management during batch colorization operations.
"""

import gc
import logging
from typing import Tuple, Optional

import torch


logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages memory allocation and cleanup for batch processing.
    
    This class handles GPU memory cache clearing, memory usage monitoring,
    garbage collection triggering, and memory estimation for images.
    
    Attributes:
        device: The torch device being used (cuda, mps, or cpu)
        memory_threshold: Percentage threshold (0-1) for triggering GC
    """
    
    def __init__(self, device: torch.device, memory_threshold: float = 0.8):
        """
        Initialize the MemoryManager.
        
        Args:
            device: The torch device to manage memory for
            memory_threshold: Memory usage threshold (0-1) for triggering GC.
                            Default is 0.8 (80%)
        """
        self.device = device
        self.memory_threshold = memory_threshold
        
        if not 0 < memory_threshold <= 1:
            raise ValueError(f"memory_threshold must be between 0 and 1, got {memory_threshold}")
        
        logger.info(f"MemoryManager initialized for device: {device}, threshold: {memory_threshold}")
    
    def clear_cache(self) -> None:
        """
        Clear GPU memory caches.
        
        This method clears the memory cache for the current device type.
        For CUDA devices, it calls torch.cuda.empty_cache().
        For MPS devices, it calls torch.mps.empty_cache().
        For CPU, this is a no-op.
        """
        if self.device.type == "cuda":
            torch.cuda.empty_cache()
            logger.debug("Cleared CUDA memory cache")
        elif self.device.type == "mps":
            torch.mps.empty_cache()
            logger.debug("Cleared MPS memory cache")
        else:
            logger.debug("No cache to clear for CPU device")
    
    def check_memory_usage(self) -> float:
        """
        Check current memory usage as a percentage.
        
        Returns:
            Memory usage as a float between 0 and 1, where 1 means 100% used.
            Returns 0.0 for CPU devices or if memory info is unavailable.
        """
        try:
            if self.device.type == "cuda":
                allocated = torch.cuda.memory_allocated(self.device)
                reserved = torch.cuda.memory_reserved(self.device)
                # Use reserved memory as the baseline since that's what's allocated from GPU
                if reserved > 0:
                    usage = allocated / reserved
                    logger.debug(f"CUDA memory usage: {usage:.2%} ({allocated / 1024**2:.1f}MB / {reserved / 1024**2:.1f}MB)")
                    return usage
                return 0.0
            elif self.device.type == "mps":
                # MPS doesn't provide detailed memory stats, estimate conservatively
                allocated = torch.mps.current_allocated_memory()
                # MPS typically has access to unified memory, use a conservative estimate
                # This is a rough approximation since MPS doesn't expose total memory
                logger.debug(f"MPS memory allocated: {allocated / 1024**2:.1f}MB")
                # Return a conservative estimate based on allocated memory
                # Assume if we've allocated more than 4GB, we're at high usage
                return min(allocated / (4 * 1024**3), 1.0)
            else:
                logger.debug("Memory usage check not available for CPU device")
                return 0.0
        except Exception as e:
            logger.warning(f"Failed to check memory usage: {e}")
            return 0.0
    
    def trigger_gc_if_needed(self) -> None:
        """
        Trigger garbage collection if memory usage exceeds threshold.
        
        This method checks current memory usage and triggers Python's
        garbage collector if usage exceeds the configured threshold.
        """
        usage = self.check_memory_usage()
        
        if usage >= self.memory_threshold:
            logger.info(f"Memory usage ({usage:.2%}) exceeds threshold ({self.memory_threshold:.2%}), triggering GC")
            gc.collect()
            
            # Clear cache after GC for GPU devices
            if self.device.type in ["cuda", "mps"]:
                self.clear_cache()
            
            # Check usage again after cleanup
            new_usage = self.check_memory_usage()
            logger.info(f"Memory usage after GC: {new_usage:.2%}")
        else:
            logger.debug(f"Memory usage ({usage:.2%}) below threshold ({self.memory_threshold:.2%})")
    
    def estimate_memory_required(self, image_size: Tuple[int, int]) -> int:
        """
        Estimate memory required for processing an image.
        
        This provides a rough estimate of GPU memory needed for processing
        an image of the given size through the colorization pipeline.
        
        Args:
            image_size: Tuple of (width, height) in pixels
            
        Returns:
            Estimated memory requirement in bytes
        """
        width, height = image_size
        pixels = width * height
        
        # Rough estimation based on typical pipeline requirements:
        # - Input image: 3 channels * 4 bytes (float32) = 12 bytes/pixel
        # - Latent representation: ~1/64 of input size * 4 channels * 4 bytes
        # - Model activations: ~2x latent size
        # - Reference images: assume 4 references at same resolution
        # - Overhead: 1.5x multiplier for intermediate tensors
        
        input_memory = pixels * 3 * 4  # RGB float32
        latent_memory = (pixels // 64) * 4 * 4  # Compressed latent
        activation_memory = latent_memory * 2  # Model activations
        reference_memory = input_memory * 4  # 4 reference images
        
        total_estimate = int((input_memory + latent_memory + activation_memory + reference_memory) * 1.5)
        
        logger.debug(f"Estimated memory for {width}x{height} image: {total_estimate / 1024**2:.1f}MB")
        
        return total_estimate

"""
Tests for the MemoryManager class.

This module tests memory management functionality including cache clearing,
memory usage monitoring, garbage collection triggering, and memory estimation.
"""

import gc
import pytest
import torch

from batch_processing.memory import MemoryManager


class TestMemoryManagerInitialization:
    """Tests for MemoryManager initialization."""
    
    def test_init_with_valid_threshold(self):
        """Test initialization with valid threshold values."""
        device = torch.device("cpu")
        
        # Test default threshold
        manager = MemoryManager(device)
        assert manager.device == device
        assert manager.memory_threshold == 0.8
        
        # Test custom threshold
        manager = MemoryManager(device, memory_threshold=0.5)
        assert manager.memory_threshold == 0.5
    
    def test_init_with_invalid_threshold(self):
        """Test initialization with invalid threshold values."""
        device = torch.device("cpu")
        
        # Test threshold too low
        with pytest.raises(ValueError, match="memory_threshold must be between 0 and 1"):
            MemoryManager(device, memory_threshold=0.0)
        
        # Test threshold too high
        with pytest.raises(ValueError, match="memory_threshold must be between 0 and 1"):
            MemoryManager(device, memory_threshold=1.5)
        
        # Test negative threshold
        with pytest.raises(ValueError, match="memory_threshold must be between 0 and 1"):
            MemoryManager(device, memory_threshold=-0.1)


class TestMemoryManagerCacheClear:
    """Tests for cache clearing functionality."""
    
    def test_clear_cache_cpu(self):
        """Test cache clearing on CPU device (should be no-op)."""
        device = torch.device("cpu")
        manager = MemoryManager(device)
        
        # Should not raise any errors
        manager.clear_cache()
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_clear_cache_cuda(self):
        """Test cache clearing on CUDA device."""
        device = torch.device("cuda")
        manager = MemoryManager(device)
        
        # Allocate some memory
        tensor = torch.randn(1000, 1000, device=device)
        del tensor
        
        # Clear cache should not raise errors
        manager.clear_cache()
    
    @pytest.mark.skipif(not torch.backends.mps.is_available(), reason="MPS not available")
    def test_clear_cache_mps(self):
        """Test cache clearing on MPS device."""
        device = torch.device("mps")
        manager = MemoryManager(device)
        
        # Allocate some memory
        tensor = torch.randn(1000, 1000, device=device)
        del tensor
        
        # Clear cache should not raise errors
        manager.clear_cache()


class TestMemoryManagerUsageCheck:
    """Tests for memory usage checking."""
    
    def test_check_memory_usage_cpu(self):
        """Test memory usage check on CPU (should return 0)."""
        device = torch.device("cpu")
        manager = MemoryManager(device)
        
        usage = manager.check_memory_usage()
        assert usage == 0.0
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_check_memory_usage_cuda(self):
        """Test memory usage check on CUDA device."""
        device = torch.device("cuda")
        manager = MemoryManager(device)
        
        # Initially should have low usage
        initial_usage = manager.check_memory_usage()
        assert 0.0 <= initial_usage <= 1.0
        
        # Allocate memory and check again
        tensor = torch.randn(10000, 10000, device=device)
        usage_with_tensor = manager.check_memory_usage()
        assert 0.0 <= usage_with_tensor <= 1.0
        
        # Clean up
        del tensor
        torch.cuda.empty_cache()
    
    @pytest.mark.skipif(not torch.backends.mps.is_available(), reason="MPS not available")
    def test_check_memory_usage_mps(self):
        """Test memory usage check on MPS device."""
        device = torch.device("mps")
        manager = MemoryManager(device)
        
        usage = manager.check_memory_usage()
        assert 0.0 <= usage <= 1.0


class TestMemoryManagerGarbageCollection:
    """Tests for garbage collection triggering."""
    
    def test_trigger_gc_below_threshold(self):
        """Test that GC is not triggered when below threshold."""
        device = torch.device("cpu")
        manager = MemoryManager(device, memory_threshold=0.9)
        
        # Should not raise errors even if usage is low
        manager.trigger_gc_if_needed()
    
    def test_trigger_gc_above_threshold(self):
        """Test that GC is triggered when above threshold."""
        device = torch.device("cpu")
        # Set very low threshold to ensure it triggers
        manager = MemoryManager(device, memory_threshold=0.01)
        
        # Create some garbage
        large_list = [list(range(1000)) for _ in range(1000)]
        
        # This should trigger GC (though on CPU it won't do much)
        manager.trigger_gc_if_needed()
        
        # Clean up
        del large_list
        gc.collect()
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_trigger_gc_cuda_with_high_usage(self):
        """Test GC triggering on CUDA with high memory usage."""
        device = torch.device("cuda")
        manager = MemoryManager(device, memory_threshold=0.1)
        
        # Allocate significant memory
        tensors = [torch.randn(5000, 5000, device=device) for _ in range(5)]
        
        # Trigger GC
        manager.trigger_gc_if_needed()
        
        # Clean up
        del tensors
        torch.cuda.empty_cache()


class TestMemoryManagerEstimation:
    """Tests for memory estimation."""
    
    def test_estimate_memory_small_image(self):
        """Test memory estimation for small images."""
        device = torch.device("cpu")
        manager = MemoryManager(device)
        
        # Small image: 512x512
        estimate = manager.estimate_memory_required((512, 512))
        
        # Should be positive
        assert estimate > 0
        
        # Should be reasonable (less than 100MB for small image)
        assert estimate < 100 * 1024 * 1024
    
    def test_estimate_memory_medium_image(self):
        """Test memory estimation for medium images."""
        device = torch.device("cpu")
        manager = MemoryManager(device)
        
        # Medium image: 1024x1024
        estimate = manager.estimate_memory_required((1024, 1024))
        
        # Should be positive and larger than small image
        assert estimate > 0
        small_estimate = manager.estimate_memory_required((512, 512))
        assert estimate > small_estimate
    
    def test_estimate_memory_large_image(self):
        """Test memory estimation for large images."""
        device = torch.device("cpu")
        manager = MemoryManager(device)
        
        # Large image: 2048x2048
        estimate = manager.estimate_memory_required((2048, 2048))
        
        # Should be positive and significantly larger
        assert estimate > 0
        medium_estimate = manager.estimate_memory_required((1024, 1024))
        assert estimate > medium_estimate
    
    def test_estimate_memory_scaling(self):
        """Test that memory estimation scales appropriately with image size."""
        device = torch.device("cpu")
        manager = MemoryManager(device)
        
        # Get estimates for different sizes
        estimate_512 = manager.estimate_memory_required((512, 512))
        estimate_1024 = manager.estimate_memory_required((1024, 1024))
        
        # Doubling dimensions should roughly quadruple memory (4x pixels)
        # Allow some tolerance for overhead
        ratio = estimate_1024 / estimate_512
        assert 3.0 < ratio < 5.0, f"Expected ratio ~4, got {ratio}"
    
    def test_estimate_memory_non_square(self):
        """Test memory estimation for non-square images."""
        device = torch.device("cpu")
        manager = MemoryManager(device)
        
        # Non-square image
        estimate = manager.estimate_memory_required((800, 600))
        
        # Should be positive
        assert estimate > 0
        
        # Should be between square images of similar total pixels
        estimate_700 = manager.estimate_memory_required((700, 700))
        estimate_800 = manager.estimate_memory_required((800, 800))
        
        # 800x600 = 480k pixels, 700x700 = 490k pixels, 800x800 = 640k pixels
        # So estimate should be close to 700x700
        assert estimate_700 * 0.8 < estimate < estimate_800 * 1.2


class TestMemoryManagerIntegration:
    """Integration tests for MemoryManager."""
    
    def test_full_workflow_cpu(self):
        """Test complete memory management workflow on CPU."""
        device = torch.device("cpu")
        manager = MemoryManager(device, memory_threshold=0.7)
        
        # Estimate memory for an image
        estimate = manager.estimate_memory_required((1024, 1024))
        assert estimate > 0
        
        # Check memory usage
        usage = manager.check_memory_usage()
        assert usage == 0.0  # CPU always returns 0
        
        # Clear cache
        manager.clear_cache()
        
        # Trigger GC if needed
        manager.trigger_gc_if_needed()
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_full_workflow_cuda(self):
        """Test complete memory management workflow on CUDA."""
        device = torch.device("cuda")
        manager = MemoryManager(device, memory_threshold=0.7)
        
        # Estimate memory for an image
        estimate = manager.estimate_memory_required((1024, 1024))
        assert estimate > 0
        
        # Allocate some memory
        tensor = torch.randn(5000, 5000, device=device)
        
        # Check memory usage
        usage = manager.check_memory_usage()
        assert 0.0 <= usage <= 1.0
        
        # Delete tensor
        del tensor
        
        # Clear cache
        manager.clear_cache()
        
        # Trigger GC if needed
        manager.trigger_gc_if_needed()
        
        # Usage should be lower after cleanup
        final_usage = manager.check_memory_usage()
        assert 0.0 <= final_usage <= 1.0
    
    @pytest.mark.skipif(not torch.backends.mps.is_available(), reason="MPS not available")
    def test_full_workflow_mps(self):
        """Test complete memory management workflow on MPS."""
        device = torch.device("mps")
        manager = MemoryManager(device, memory_threshold=0.7)
        
        # Estimate memory for an image
        estimate = manager.estimate_memory_required((1024, 1024))
        assert estimate > 0
        
        # Allocate some memory
        tensor = torch.randn(5000, 5000, device=device)
        
        # Check memory usage
        usage = manager.check_memory_usage()
        assert 0.0 <= usage <= 1.0
        
        # Delete tensor
        del tensor
        
        # Clear cache
        manager.clear_cache()
        
        # Trigger GC if needed
        manager.trigger_gc_if_needed()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

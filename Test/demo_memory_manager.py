"""
Demo script for MemoryManager functionality.

This script demonstrates the key features of the MemoryManager class
including cache clearing, memory monitoring, and garbage collection.
"""

import torch
from batch_processing.memory import MemoryManager


def main():
    """Demonstrate MemoryManager functionality."""
    
    # Detect available device
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("Using MPS (Apple Silicon) device")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print("Using CUDA device")
    else:
        device = torch.device("cpu")
        print("Using CPU device")
    
    print("\n" + "="*60)
    print("MemoryManager Demo")
    print("="*60)
    
    # Initialize MemoryManager
    print("\n1. Initializing MemoryManager with 80% threshold...")
    manager = MemoryManager(device, memory_threshold=0.8)
    print(f"   Device: {manager.device}")
    print(f"   Threshold: {manager.memory_threshold:.0%}")
    
    # Check initial memory usage
    print("\n2. Checking initial memory usage...")
    initial_usage = manager.check_memory_usage()
    print(f"   Memory usage: {initial_usage:.2%}")
    
    # Estimate memory for different image sizes
    print("\n3. Estimating memory requirements for different image sizes...")
    sizes = [(512, 512), (1024, 1024), (2048, 2048)]
    for width, height in sizes:
        estimate = manager.estimate_memory_required((width, height))
        print(f"   {width}x{height}: {estimate / 1024**2:.1f} MB")
    
    # Allocate some memory (if not CPU)
    if device.type != "cpu":
        print(f"\n4. Allocating memory on {device.type.upper()}...")
        tensors = []
        for i in range(3):
            tensor = torch.randn(2000, 2000, device=device)
            tensors.append(tensor)
            usage = manager.check_memory_usage()
            print(f"   After allocation {i+1}: {usage:.2%}")
        
        # Check memory usage
        print("\n5. Checking memory usage after allocations...")
        usage = manager.check_memory_usage()
        print(f"   Current usage: {usage:.2%}")
        
        # Clear cache
        print("\n6. Clearing memory cache...")
        del tensors
        manager.clear_cache()
        usage_after_clear = manager.check_memory_usage()
        print(f"   Usage after clear: {usage_after_clear:.2%}")
        
        # Trigger GC if needed
        print("\n7. Triggering garbage collection if needed...")
        manager.trigger_gc_if_needed()
        final_usage = manager.check_memory_usage()
        print(f"   Final usage: {final_usage:.2%}")
    else:
        print("\n4-7. Skipping GPU memory operations (CPU device)")
    
    # Demonstrate threshold-based GC
    print("\n8. Demonstrating threshold-based garbage collection...")
    low_threshold_manager = MemoryManager(device, memory_threshold=0.1)
    print(f"   Created manager with {low_threshold_manager.memory_threshold:.0%} threshold")
    print("   Triggering GC check...")
    low_threshold_manager.trigger_gc_if_needed()
    print("   GC check complete")
    
    print("\n" + "="*60)
    print("Demo complete!")
    print("="*60)
    
    # Summary
    print("\nKey Features Demonstrated:")
    print("  ✓ Device detection and initialization")
    print("  ✓ Memory usage monitoring")
    print("  ✓ Memory estimation for images")
    print("  ✓ Cache clearing")
    print("  ✓ Threshold-based garbage collection")
    
    print("\nUsage in Batch Processing:")
    print("  - Initialize MemoryManager at start of batch")
    print("  - Call clear_cache() after processing each image")
    print("  - Call trigger_gc_if_needed() periodically")
    print("  - Use estimate_memory_required() to plan batch sizes")


if __name__ == "__main__":
    main()

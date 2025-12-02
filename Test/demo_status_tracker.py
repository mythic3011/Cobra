"""
Demo script showing the status tracking system in action.

This script demonstrates how to use the StatusTracker to monitor
batch processing operations.
"""

import time
from batch_processing.core.status import StatusTracker, ProcessingState


def simulate_batch_processing():
    """Simulate a batch processing workflow with status tracking."""
    print("=" * 60)
    print("Status Tracking System Demo")
    print("=" * 60)
    print()
    
    # Create a status tracker
    tracker = StatusTracker()
    
    # Add images to track
    images = ["page_001.png", "page_002.png", "page_003.png", "page_004.png", "page_005.png"]
    
    print("Adding images to track...")
    for img in images:
        tracker.add_image(img)
    print(f"✓ Added {len(images)} images to tracker")
    print()
    
    # Display initial summary
    summary = tracker.get_summary()
    print("Initial Status Summary:")
    print(f"  Total: {summary.total}")
    print(f"  Pending: {summary.pending}")
    print(f"  Processing: {summary.processing}")
    print(f"  Completed: {summary.completed}")
    print(f"  Failed: {summary.failed}")
    print()
    
    # Simulate processing each image
    print("Starting batch processing...")
    print()
    
    for i, img in enumerate(images, 1):
        print(f"[{i}/{len(images)}] Processing {img}...")
        
        # Update to processing
        tracker.update_status(img, ProcessingState.PROCESSING.value)
        
        # Simulate processing time
        time.sleep(0.2)
        
        # Simulate success or failure
        if i == 3:
            # Simulate a failure
            tracker.update_status(
                img,
                ProcessingState.FAILED.value,
                error_message="Out of memory error"
            )
            print(f"  ✗ Failed: Out of memory error")
        else:
            # Success
            output_path = f"/output/{img.replace('.png', '_colorized.png')}"
            tracker.update_status(
                img,
                ProcessingState.COMPLETED.value,
                output_path=output_path
            )
            print(f"  ✓ Completed: {output_path}")
        
        # Show processing time
        status = tracker.get_status(img)
        if status.processing_time:
            print(f"  ⏱  Processing time: {status.processing_time:.2f}s")
        print()
    
    # Display final summary
    print("=" * 60)
    print("Final Status Summary:")
    print("=" * 60)
    summary = tracker.get_summary()
    print(f"  Total: {summary.total}")
    print(f"  Pending: {summary.pending}")
    print(f"  Processing: {summary.processing}")
    print(f"  Completed: {summary.completed}")
    print(f"  Failed: {summary.failed}")
    print(f"  Success Rate: {summary.success_rate:.1f}%")
    if summary.elapsed_time:
        print(f"  Total Time: {summary.elapsed_time:.2f}s")
    print()
    
    # Show detailed status for each image
    print("Detailed Status:")
    print("-" * 60)
    all_statuses = tracker.get_all_statuses()
    for img_id, status in all_statuses.items():
        print(f"  {img_id}:")
        print(f"    State: {status.state}")
        if status.processing_time:
            print(f"    Time: {status.processing_time:.2f}s")
        if status.output_path:
            print(f"    Output: {status.output_path}")
        if status.error_message:
            print(f"    Error: {status.error_message}")
        print()
    
    # Show images by state
    print("Images by State:")
    print("-" * 60)
    for state in [ProcessingState.COMPLETED, ProcessingState.FAILED, ProcessingState.PENDING]:
        images_in_state = tracker.get_images_by_state(state.value)
        if images_in_state:
            print(f"  {state.value.upper()}: {', '.join(images_in_state)}")
    print()


if __name__ == "__main__":
    simulate_batch_processing()

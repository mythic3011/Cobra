"""
Demo script for the batch processing queue system.

This script demonstrates the functionality of the ImageQueue and ImageQueueItem classes.
"""

from batch_processing.core.queue import ImageQueue, ImageQueueItem


def main():
    print("=" * 60)
    print("Batch Processing Queue System Demo")
    print("=" * 60)
    print()
    
    # Create a new queue
    queue = ImageQueue()
    print("✓ Created empty queue")
    print(f"  Queue size: {queue.size()}")
    print()
    
    # Add some items with different priorities
    print("Adding items to queue:")
    print("-" * 60)
    
    items_data = [
        ("page_001.png", 0, "line_art", 0.95),
        ("page_002.png", 5, "line_art", 0.88),
        ("page_003.png", 0, "line_art", 0.92),
        ("urgent_page.png", 10, "line_art", 0.99),
        ("reference.png", 0, "colored", 0.87),
    ]
    
    for i, (filename, priority, img_type, confidence) in enumerate(items_data):
        item = ImageQueueItem(
            id=f"img_{i:03d}",
            input_path=f"/input/{filename}",
            output_path=f"/output/{filename}",
            priority=priority,
            image_type=img_type,
            classification_confidence=confidence
        )
        queue.enqueue(item)
        print(f"  ✓ Enqueued: {filename} (priority={priority}, type={img_type}, confidence={confidence:.2f})")
    
    print()
    print(f"Queue size after enqueuing: {queue.size()}")
    print()
    
    # Peek at the next item
    print("Peeking at next item (without removing):")
    print("-" * 60)
    next_item = queue.peek()
    if next_item:
        print(f"  Next item: {next_item.input_path}")
        print(f"  Priority: {next_item.priority}")
        print(f"  Type: {next_item.image_type}")
        print(f"  Confidence: {next_item.classification_confidence:.2f}")
    print(f"  Queue size (unchanged): {queue.size()}")
    print()
    
    # Process items in priority order
    print("Processing items in priority order:")
    print("-" * 60)
    
    processed_count = 0
    while queue.size() > 0:
        item = queue.dequeue()
        processed_count += 1
        print(f"  {processed_count}. Processing: {item.input_path}")
        print(f"     Priority: {item.priority}, Type: {item.image_type}, Confidence: {item.classification_confidence:.2f}")
        print(f"     Remaining in queue: {queue.size()}")
    
    print()
    print(f"✓ All {processed_count} items processed")
    print(f"  Final queue size: {queue.size()}")
    print()
    
    # Demonstrate queue clearing
    print("Demonstrating queue clearing:")
    print("-" * 60)
    
    # Add a few more items
    for i in range(3):
        item = ImageQueueItem(
            id=f"test_{i}",
            input_path=f"/test/image_{i}.png",
            output_path=f"/test/output_{i}.png"
        )
        queue.enqueue(item)
    
    print(f"  Added 3 items, queue size: {queue.size()}")
    queue.clear()
    print(f"  After clear(), queue size: {queue.size()}")
    print()
    
    # Demonstrate iteration
    print("Demonstrating queue iteration:")
    print("-" * 60)
    
    # Add items with different priorities
    for priority in [1, 5, 3, 10, 2]:
        item = ImageQueueItem(
            id=f"priority_{priority}",
            input_path=f"/iter/image_p{priority}.png",
            output_path=f"/iter/output_p{priority}.png",
            priority=priority
        )
        queue.enqueue(item)
    
    print(f"  Added 5 items with priorities: [1, 5, 3, 10, 2]")
    print(f"  Iterating over queue (in priority order):")
    
    for i, item in enumerate(queue, 1):
        print(f"    {i}. {item.id} (priority={item.priority})")
    
    print()
    print("=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

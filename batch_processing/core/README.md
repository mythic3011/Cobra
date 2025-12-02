# Core Batch Processing Components

This module contains the core components for batch processing of images in the Cobra colorization system.

## Components

### ImageQueue

A priority queue for managing the order of image processing.

**Features**:
- Priority-based ordering (higher priority processed first)
- FIFO ordering within same priority level
- Type-safe operations
- Iterator support
- Efficient size tracking

**Usage**:
```python
from batch_processing.core import ImageQueue, ImageQueueItem

# Create a queue
queue = ImageQueue()

# Add items
item = ImageQueueItem(
    id="img_001",
    input_path="/input/image.png",
    output_path="/output/image.png",
    priority=5
)
queue.enqueue(item)

# Process items
while queue:
    item = queue.dequeue()
    # Process the item
```

### ImageQueueItem

A data class representing an item in the processing queue.

**Fields**:
- `id` (str): Unique identifier
- `input_path` (str): Path to input image
- `output_path` (str): Path for output image
- `config` (Optional[Dict]): Image-specific configuration
- `priority` (int): Processing priority (default: 0)
- `image_type` (Optional[str]): "line_art" or "colored"
- `classification_confidence` (Optional[float]): Confidence score (0.0-1.0)

**Validation**:
- `image_type` must be "line_art" or "colored" if provided
- `classification_confidence` must be between 0.0 and 1.0 if provided

**Usage**:
```python
from batch_processing.core import ImageQueueItem

# Create a queue item
item = ImageQueueItem(
    id="page_001",
    input_path="/input/page1.png",
    output_path="/output/page1_colored.png",
    priority=10,
    image_type="line_art",
    classification_confidence=0.95
)
```

## Priority System

The queue uses a priority system where:
- Higher priority values are processed first
- Priority 10 > Priority 5 > Priority 0
- Items with the same priority maintain FIFO order
- Default priority is 0

**Example**:
```python
# Add items with different priorities
queue.enqueue(ImageQueueItem(id="1", ..., priority=0))   # Third
queue.enqueue(ImageQueueItem(id="2", ..., priority=10))  # First
queue.enqueue(ImageQueueItem(id="3", ..., priority=5))   # Second

# Processing order: id="2", id="3", id="1"
```

## Queue Operations

### enqueue(item)
Add an item to the queue in priority order.

```python
queue.enqueue(item)
```

### dequeue()
Remove and return the highest priority item.

```python
item = queue.dequeue()  # Returns None if empty
```

### peek()
View the highest priority item without removing it.

```python
item = queue.peek()  # Returns None if empty
```

### size()
Get the number of items in the queue.

```python
count = queue.size()
```

### clear()
Remove all items from the queue.

```python
queue.clear()
```

## Iteration

The queue supports iteration over items in priority order:

```python
for item in queue:
    print(f"Item: {item.id}, Priority: {item.priority}")
```

Note: Iteration does not remove items from the queue.

## Boolean Evaluation

The queue can be used in boolean contexts:

```python
if queue:
    # Queue has items
    item = queue.dequeue()
else:
    # Queue is empty
    print("No items to process")
```

## Testing

Run the test suite:
```bash
uv run pytest test_queue.py -v
```

Run the demo:
```bash
uv run python demo_queue.py
```

## Integration

The queue system integrates with:
- **BatchProcessor**: Uses queue to manage processing order
- **Status Tracker**: Tracks status of queued items
- **Configuration Handler**: Applies config from queue items
- **Image Classifier**: Populates image_type and confidence fields

## Performance

- Enqueue: O(n) - finds correct position based on priority
- Dequeue: O(1) - removes from front
- Peek: O(1) - views front without removal
- Size: O(1) - tracked internally
- Clear: O(1) - clears internal list

For typical batch sizes (< 1000 images), performance is excellent.

## Future Enhancements

Potential improvements:
- Heap-based implementation for O(log n) enqueue
- Persistent queue state for crash recovery
- Queue serialization/deserialization
- Queue statistics and metrics

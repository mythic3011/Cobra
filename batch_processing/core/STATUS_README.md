# Status Tracking System

The status tracking system provides comprehensive monitoring and reporting for batch image processing operations.

## Overview

The status tracking system consists of three main components:

1. **ProcessingStatus**: A dataclass representing the status of a single image
2. **StatusTracker**: A class that manages status for all images in a batch
3. **StatusSummary**: A dataclass providing aggregate statistics for the batch

## Components

### ProcessingStatus

Represents the processing status of a single image with the following attributes:

- `id`: Unique identifier for the image
- `state`: Current processing state (pending, processing, completed, failed, cancelled)
- `start_time`: Timestamp when processing started
- `end_time`: Timestamp when processing ended
- `error_message`: Error message if processing failed
- `output_path`: Path to the output file if completed

**Properties:**
- `processing_time`: Calculated processing duration in seconds
- `is_terminal_state()`: Returns True if in a final state (completed, failed, cancelled)

### StatusTracker

Manages status tracking for all images in a batch operation.

**Key Methods:**

```python
# Add an image to track
tracker.add_image("img_001")

# Update status
tracker.update_status(
    "img_001",
    ProcessingState.PROCESSING.value
)

# Update with additional info
tracker.update_status(
    "img_001",
    ProcessingState.COMPLETED.value,
    output_path="/output/img_001.png"
)

# Get status for specific image
status = tracker.get_status("img_001")

# Get all statuses
all_statuses = tracker.get_all_statuses()

# Get summary statistics
summary = tracker.get_summary()

# Get images by state
completed = tracker.get_images_by_state(ProcessingState.COMPLETED.value)
```

### StatusSummary

Provides aggregate statistics for the entire batch:

- `total`: Total number of images
- `pending`: Number of pending images
- `processing`: Number of images being processed
- `completed`: Number of completed images
- `failed`: Number of failed images
- `cancelled`: Number of cancelled images
- `start_time`: Batch start timestamp
- `end_time`: Batch end timestamp

**Properties:**
- `is_complete`: True if all images are in terminal states
- `success_rate`: Percentage of successfully completed images
- `elapsed_time`: Total batch processing time

## Usage Example

```python
from batch_processing.core.status import StatusTracker, ProcessingState

# Create tracker
tracker = StatusTracker()

# Add images
tracker.add_image("page_001.png")
tracker.add_image("page_002.png")
tracker.add_image("page_003.png")

# Process first image
tracker.update_status("page_001.png", ProcessingState.PROCESSING.value)
# ... do processing ...
tracker.update_status(
    "page_001.png",
    ProcessingState.COMPLETED.value,
    output_path="/output/page_001_colorized.png"
)

# Handle failure
tracker.update_status("page_002.png", ProcessingState.PROCESSING.value)
tracker.update_status(
    "page_002.png",
    ProcessingState.FAILED.value,
    error_message="Out of memory"
)

# Get summary
summary = tracker.get_summary()
print(f"Completed: {summary.completed}/{summary.total}")
print(f"Success rate: {summary.success_rate:.1f}%")
print(f"Elapsed time: {summary.elapsed_time:.2f}s")

# Get detailed status
for img_id, status in tracker.get_all_statuses().items():
    print(f"{img_id}: {status.state}")
    if status.processing_time:
        print(f"  Time: {status.processing_time:.2f}s")
    if status.error_message:
        print(f"  Error: {status.error_message}")
```

## State Transitions

Valid state transitions:

```
PENDING → PROCESSING → COMPLETED
                    → FAILED
                    → CANCELLED
```

## Timestamps

The system automatically manages timestamps:

- **Batch start time**: Set when the first image is added
- **Image start time**: Set when transitioning from PENDING to PROCESSING
- **Image end time**: Set when transitioning to any terminal state
- **Batch end time**: Set when all images reach terminal states

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 4.1**: Display status table with all images and their states
- **Requirement 4.2**: Update status to processing with timestamp
- **Requirement 4.3**: Update status to completed with output path
- **Requirement 4.4**: Update status to failed with error message
- **Requirement 4.5**: Provide detailed information including processing time

## Testing

Run the test suite:

```bash
uv run pytest test_status_tracker.py -v
```

Run the demo:

```bash
uv run python demo_status_tracker.py
```

## Integration

The StatusTracker integrates with other batch processing components:

- **ImageQueue**: Tracks status for queued images
- **BatchProcessor**: Updates status during processing
- **UI Components**: Displays status information to users
- **CLI**: Reports progress and results

## Error Handling

The system handles errors gracefully:

- Invalid states raise `ValueError`
- Non-existent image IDs raise `KeyError`
- Duplicate image additions raise `ValueError`
- All errors include descriptive messages

## Performance

The status tracker is designed for efficiency:

- O(1) status lookups by image ID
- O(n) summary generation where n is number of images
- Minimal memory overhead per tracked image
- Thread-safe for single-threaded batch processing

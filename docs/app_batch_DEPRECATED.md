# DEPRECATED: app_batch.py

This file has been deprecated. The batch processing functionality has been integrated into the main `app.py` file.

## Migration

- **Old**: Run `python app_batch.py` for batch processing
- **New**: Run `python app.py` and select the "Batch Processing" tab

## Reason for Deprecation

To provide a unified user experience, both single-image and batch processing modes are now accessible from a single application entry point (`app.py`). This:

1. Simplifies the user experience - no need to know about multiple files
2. Enables easy switching between modes
3. Shares resources (models) between modes for better efficiency
4. Maintains consistent styling and UX across modes

## What Happened to the Code?

The batch processing UI code has been extracted into `batch_ui.py` as the `create_batch_processing_ui()` function, which is imported and used by `app.py`.

## If You Need the Old Standalone Version

The old `app_batch.py` file is still available in git history if needed for reference.

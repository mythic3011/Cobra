# Cobra Documentation

This directory contains all documentation for the Cobra line art colorization system.

## Directory Structure

```
docs/
├── README.md                           # This file
├── guides/                             # User guides and quick starts
│   ├── CLI_QUICK_START.md             # CLI usage guide
│   └── PREVIEW_MODE_QUICK_START.md    # Preview mode guide
├── implementation/                     # Implementation documentation
│   ├── UNIFIED_INTERFACE_IMPLEMENTATION.md      # Tab-based UI integration
│   ├── REFERENCE_UI_IMPROVEMENTS.md             # Reference preview UI v1
│   ├── REFERENCE_UI_ENHANCEMENTS_V2.md          # Reference preview UI v2
│   ├── CLASSIFIER_FIX.md                        # Saturation priority fix
│   └── APP_CLEANUP_VERIFICATION.md              # Code cleanup verification
└── app_batch_DEPRECATED.md            # Deprecation notice for old batch UI

```

## Quick Links

### For Users
- [CLI Quick Start](guides/CLI_QUICK_START.md) - Get started with command-line batch processing
- [Preview Mode Guide](guides/PREVIEW_MODE_QUICK_START.md) - Test settings before full batch

### For Developers
- [Unified Interface Implementation](implementation/UNIFIED_INTERFACE_IMPLEMENTATION.md) - Tab-based UI architecture
- [Reference UI Enhancements](implementation/REFERENCE_UI_ENHANCEMENTS_V2.md) - Latest UI improvements
- [Classifier Fix](implementation/CLASSIFIER_FIX.md) - Image classification improvements

## Additional Documentation

Module-specific documentation is located within each module:

- `batch_processing/` - Batch processing module documentation
  - `BATCH_PROCESSOR_QUICK_START.md` - Batch processor usage
  - `ERROR_HANDLING_GUIDE.md` - Error handling patterns
  - `README.md` - Module overview
  - `core/STATUS_README.md` - Status tracking system
  - `io/README.md` - File I/O documentation
  - `memory/README.md` - Memory management
  - `ui/README.md` - UI components

- `Test/` - Test documentation
  - Various `*_IMPLEMENTATION_SUMMARY.md` files
  - `TASK_*_VERIFICATION.md` files

## Main Application Files

- `app.py` - Main application entry point (unified interface)
- `batch_ui.py` - Batch processing UI components
- `batch_colorize.py` - CLI interface for batch processing
- `app_batch.py` - **DEPRECATED** (see [deprecation notice](app_batch_DEPRECATED.md))

## Getting Started

1. **Single Image Mode**: Run `python app.py` and use the "Single Image" tab
2. **Batch Processing (GUI)**: Run `python app.py` and use the "Batch Processing" tab
3. **Batch Processing (CLI)**: See [CLI Quick Start](guides/CLI_QUICK_START.md)

## Recent Updates

### Task 14: Unified Interface (Completed)
- Integrated batch processing into main app.py
- Tab-based navigation for single/batch modes
- Shared model resources
- Consistent styling

### Reference UI Enhancements
- Confidence-based sorting
- Visual selection feedback
- Detailed classification metrics
- Quality rating system

### Classifier Improvements
- Saturation priority for better accuracy
- Reduced false positives
- Better grayscale image handling

## Contributing

When adding new documentation:
- User guides → `docs/guides/`
- Implementation docs → `docs/implementation/`
- Module-specific docs → within the module directory
- Keep this README updated with new additions

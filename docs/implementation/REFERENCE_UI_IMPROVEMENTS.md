# Reference Image Preview UI Improvements

## Overview

Improved the Reference Image Preview and Selection UI to be more intuitive and user-friendly with direct image interaction and detailed classification information.

## Key Improvements

### 1. ✅ Direct Image Selection
**Before:** Separate checkbox list below gallery
**After:** Click directly on images in the gallery to select/deselect

- More intuitive interaction
- Visual feedback on selection
- No need to match images to checkboxes

### 2. ✅ Hover/Click Information Panel
**New Feature:** Right-side info panel shows detailed classification data

When you click an image, you see:
- **Filename**
- **Classification confidence** (percentage)
- **Color saturation** (why it's colored)
- **Unique colors count** (palette diversity)
- **Edge density** (vs line art)
- **Why classified as colored** (checklist with ✓/✗)
- **Current selection status** (🟢 Selected / ⚪ Not Selected)

### 3. ✅ Real-time Selection Counter
**New Feature:** Shows "X selected" or "X selected (all)"

- Updates immediately when clicking images
- Clear indication of how many references are active
- Shows "(all)" when everything is selected

### 4. ✅ Improved Layout
**Before:** Vertical stack with gallery, checkboxes, buttons
**After:** Two-column layout

```
┌─────────────────────────────┬──────────────────┐
│                             │  Selection Info  │
│   Reference Gallery         │  ─────────────   │
│   (Click to Select)         │  X selected      │
│                             │                  │
│   [Image] [Image] [Image]   │  Image Details   │
│   [Image] [Image] [Image]   │  - Filename      │
│                             │  - Saturation    │
│                             │  - Colors        │
│                             │  - Edge density  │
│                             │  - Confidence    │
│                             │                  │
│                             │  Quick Actions   │
│                             │  [Select All]    │
│                             │  [Deselect All]  │
└─────────────────────────────┴──────────────────┘
```

### 5. ✅ Better Visual Feedback

**Classification Explanation:**
```
**Why classified as colored:**
✓ High saturation (>15%)
✓ Diverse colors (>1000)
✓ Lower edge density (<30%)
```

Shows exactly why each image was classified as a colored reference with checkmarks.

## Technical Implementation

### State Management
- Uses `selected_indices_state` (gr.State) to track selected image indices
- Global `detected_references` and `reference_classifications` for data
- Real-time updates on every interaction

### Event Handlers

1. **Gallery Select Handler**
   - Toggles selection on click
   - Updates info panel with classification details
   - Shows why image was classified as colored

2. **Select All Button**
   - Selects all detected references
   - Updates counter and info

3. **Deselect All Button**
   - Clears all selections
   - Updates UI accordingly

### Data Flow

```
ZIP Upload
    ↓
Extract & Classify
    ↓
Load Images → Gallery
    ↓
Store Classifications → Info Panel
    ↓
User Clicks Image
    ↓
Toggle Selection + Show Details
    ↓
Start Processing with Selected Indices
```

## User Experience Benefits

### Before
1. Upload ZIP
2. See gallery of images
3. Scroll down to checkboxes
4. Try to match images to checkbox labels
5. Check boxes manually
6. Scroll back up to see what you selected
7. Click start

### After
1. Upload ZIP
2. See gallery with info panel
3. Click images directly to select/deselect
4. See real-time details and classification info
5. Understand why each image was classified
6. Click start

**Result:** 3 fewer steps, more intuitive, better understanding of classification

## Classification Metrics Explained

### Color Saturation
- Measures how vibrant/colorful the image is
- Line art: typically < 15%
- Colored images: typically > 15%

### Unique Colors
- Counts distinct colors in the image
- Line art: typically < 1000 colors
- Colored images: typically > 1000 colors

### Edge Density
- Measures proportion of edge pixels
- Line art: typically > 30% (lots of lines)
- Colored images: typically < 30% (filled areas)

### Confidence Score
- Overall classification confidence
- Based on how many criteria are met
- Higher = more certain it's a colored reference

## Example Info Panel Output

```
**Selected Image: character_colored.png**

**Classification: Colored Reference** ✓

**Metrics:**
- Color Saturation: 45.23%
- Unique Colors: 3,847
- Edge Density: 12.45%
- Confidence: 100.0%

**Why classified as colored:**
✓ High saturation (>15%)
✓ Diverse colors (>1000)
✓ Lower edge density (<30%)

**Status:** 🟢 Selected
```

## Future Enhancements (Optional)

- [ ] Add thumbnail preview on hover
- [ ] Show before/after comparison
- [ ] Add manual classification override
- [ ] Batch edit classification thresholds
- [ ] Export classification report

## Testing

Compile test passed:
```bash
$ uv run python -m py_compile batch_ui.py
✓ batch_ui.py compiles successfully
```

## Conclusion

The improved UI makes reference selection:
- **More intuitive** - Direct image clicking
- **More informative** - See classification details
- **More efficient** - Fewer steps, better feedback
- **More transparent** - Understand why images were classified

Users can now confidently select references with full understanding of the classification process.

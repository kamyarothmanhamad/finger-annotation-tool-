# Simple Mask Annotator

A modular Python application for creating precise mask annotations for hand and finger segmentation using smooth curves.

## Features

- Create mask annotations using smooth Bézier curves for natural contours
- Finger-level classification (thumb, index, middle, ring, pinky, palm)
- Support for multiple subjects and both hands in the same image
- Person ID and handedness tracking for multi-subject datasets
- Save and load annotations in COCO-compatible format
- Automatic binary mask storage for reliable loading
- Adjustable curve smoothness and mask opacity
- Robust annotation loading with multiple fallback strategies
- Filtering options to view annotations by person, hand, or hand instance
- Straightforward UI with keyboard shortcuts for efficient annotation

## Directory Structure

```
simple_mask_annotator/
├── __init__.py
├── __main__.py
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── enums.py
│   ├── hand_instance.py
│   └── mask_manager.py
├── ui/
│   ├── __init__.py
│   ├── app.py
│   ├── canvas_controller.py
│   └── mask_list.py
└── utils/
    ├── __init__.py
    └── file_manager.py
```

## Requirements

- Python 3.7+
- NumPy
- Pillow (PIL)
- OpenCV
- pycocotools

## Installation

1. Clone the repository
2. Install requirements:
   ```
   pip install -r simple_mask_annotator/requirements.txt
   ```

## Usage

Run the application:

```
python -m simple_mask_annotator
```

### Creating Masks

1. Load a dataset of images by clicking "Load Dataset"
2. Set the Person ID and Handedness (left/right) in the Subject Info panel
3. Select a finger type (thumb, index, etc.)
4. Click on the image to add control points for your mask
5. Double-click near the first point to close and create the mask
6. Adjust smoothness and opacity using the sliders
7. Navigate through images with the "Previous" and "Next" buttons
8. Save annotations using the "Save Annotations" button

### Managing Multiple Hands

1. Use the "Add Hand" button to create a new hand instance
2. Select the appropriate person ID and handedness
3. Switch between hand instances using the Hand Instances list
4. Filter annotations by hand instance using the "Filter by Hand Instance" option

## Annotation Storage

The application saves annotations in COCO format with additional metadata:

1. **Person ID**: Identifier for the person whose hand is annotated
2. **Handedness**: Whether the hand is left or right
3. **Binary Masks**: PNG images containing the mask data for reliable loading
4. **Hand Instance**: Combination of person ID and handedness

The JSON annotations include this data at both the file level and for each individual annotation.

## Output Format

Annotations are saved in two complementary formats:

1. **JSON File**: COCO-compatible format with RLE encoded masks and additional metadata
2. **Binary Masks**: Individual PNG files for each mask in a `masks` subdirectory

Example directory structure after annotation:
```
dataset/
├── images/
│   ├── image001.jpg
│   └── image002.jpg
└── annotations/
    ├── image001.json
    ├── image002.json
    └── masks/
        ├── image001_person_001_RIGHT_thumb_mask_1.png
        ├── image001_person_001_RIGHT_index_mask_2.png
        └── ...
```

## Usage Tips

- Enable "Save Binary Masks" option (on by default) for reliable mask storage and loading
- Use consistent Person IDs across images of the same subject
- Use the filter options to focus on specific hands when working with multi-hand datasets
- Double-click to close curve paths when creating masks
- Save annotations frequently, especially before navigating between images

## Troubleshooting

### Mask Loading Issues

If you encounter issues with loading annotations:

1. Check if binary mask files exist in the `masks` subdirectory
2. Ensure the mask filenames match the expected pattern
3. Try loading with debug logging enabled:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### RLE Decoding Issues

If you encounter "Invalid RLE mask representation" errors:

1. Make sure pycocotools is properly installed: `pip install pycocotools --upgrade`
2. Check that binary mask files exist as a fallback
3. Verify the JSON annotations follow the COCO specification

## License

[]

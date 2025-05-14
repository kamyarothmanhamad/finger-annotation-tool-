# Simple Mask Annotator

A powerful, user-friendly application for creating precise mask annotations for hand and finger segmentation using smooth curves.

## Overview

Simple Mask Annotator is designed for researchers and developers who need to create high-quality segmentation masks for hand and finger images. It supports multi-subject annotation with person ID tracking, left/right hand differentiation, and finger-level classification.

![Simple Mask Annotator Screenshot](https://via.placeholder.com/800x500?text=Simple+Mask+Annotator+Screenshot)

## Project Structure

- `simple_mask_annotator/` - The main package containing all application modules
  - `core/` - Core functionality and data structures
  - `ui/` - User interface components
  - `utils/` - Utility functions for file operations
- `setup.py` - Package installation configuration
- `run_annotator.sh` - Executable script to run the annotator
- `example_usage.py` - Example script showing programmatic usage

## Key Features

- **Smooth Curve Drawing**: Create natural contours using Bézier curves
- **Multi-Hand Support**: Annotate multiple hands in the same image
- **Person Tracking**: Assign person IDs to track subjects across datasets
- **Hand Differentiation**: Separately annotate left and right hands
- **Finger Classification**: Categorize masks by finger type (thumb, index, middle, ring, pinky, palm)
- **COCO-Compatible**: Save and load annotations in COCO format with extensions
- **Binary Mask Storage**: Reliable mask storage with PNG files
- **Customizable UI**: Adjust mask opacity and curve smoothness

## Installation

You can install the package in development mode:

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r simple_mask_annotator/requirements.txt
```

Run the application:

```bash
./run_annotator.sh
```

or

```bash
python -m simple_mask_annotator
```

## Requirements

- Python 3.7+
- NumPy
- Pillow (PIL)
- OpenCV (cv2)
- pycocotools

## Usage Examples

### Starting the application

```bash
python -m simple_mask_annotator
```

### Using as a library

```python
import tkinter as tk
from simple_mask_annotator.ui.app import SimpleMaskAnnotatorApp

# Create a tkinter window
root = tk.Tk()

# Initialize the application
app = SimpleMaskAnnotatorApp(root)

# Start the application
root.mainloop()
```

### Programmatic access to annotation data

```python
from simple_mask_annotator.utils.file_manager import FileManager
from simple_mask_annotator.core.mask_manager import MaskManager

# Initialize managers
file_manager = FileManager()
mask_manager = MaskManager()

# Load a dataset
file_manager.load_dataset("path/to/dataset")

# Load annotations for the current image
success, hand_instances = file_manager.load_annotations(
    mask_manager,
    image_width=640,
    image_height=480
)

# Access mask data
for finger in mask_manager.finger_annotations:
    for mask_data in mask_manager.finger_annotations[finger]["masks"]:
        # Process mask data
        mask = mask_data["mask"]  # NumPy array
        person_id = mask_data["person_id"]
        handedness = mask_data["handedness"]
        # ...
```

See `example_usage.py` for more detailed examples of programmatic usage.

## Annotation Format

Annotations are saved in COCO-compatible JSON format with additional metadata:

```json
{
  "annotations": [
    {
      "id": 1,
      "image_id": 1,
      "category_id": 0,
      "segmentation": {
        "size": [480, 640],
        "counts": "..."
      },
      "area": 1500,
      "bbox": [100, 150, 50, 40],
      "iscrowd": 0,
      "mask_file": "masks/image001_person_001_RIGHT_thumb_mask_1.png",
      "person_id": "person_001",
      "handedness": "RIGHT"
    },
    // ...more annotations
  ],
  "categories": [
    {"id": 0, "name": "thumb", "supercategory": "finger"},
    {"id": 1, "name": "index", "supercategory": "finger"},
    {"id": 2, "name": "middle", "supercategory": "finger"},
    {"id": 3, "name": "ring", "supercategory": "finger"},
    {"id": 4, "name": "pinky", "supercategory": "finger"},
    {"id": 5, "name": "palm", "supercategory": "finger"}
  ],
  "hand_metadata": {
    "default_person_id": "person_001",
    "default_handedness": "RIGHT"
  }
}
```

## Documentation

For detailed documentation, see the [package README](simple_mask_annotator/README.md).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[]

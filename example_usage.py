#!/usr/bin/env python3
"""
Example script demonstrating how to use the SimpleMarkAnnotator programmatically.
This script shows how to:
1. Create a basic annotator
2. Load a specific image
3. Access the mask annotations programmatically
"""

import os
import tkinter as tk
from simple_mask_annotator.ui.app import SimpleMaskAnnotatorApp
from simple_mask_annotator.core.enums import FingerType
import numpy as np
import matplotlib.pyplot as plt

def show_masks_example(annotator):
    """
    Example function to demonstrate how to access mask data programmatically
    
    Args:
        annotator: SimpleMaskAnnotatorApp instance
    """
    # Check if we have any masks
    has_masks = False
    for finger in FingerType:
        if annotator.mask_manager.finger_annotations[finger]["masks"]:
            has_masks = True
            break
    
    if not has_masks:
        print("No masks found. Please create some masks first.")
        return
    
    # Get image dimensions
    img_width = annotator.canvas_controller.current_image_data.width
    img_height = annotator.canvas_controller.current_image_data.height
    
    # Create a combined mask for visualization
    combined_mask = np.zeros((img_height, img_width, 3), dtype=np.uint8)
    
    # Fill each finger mask with a different color
    colors = {
        FingerType.THUMB: (255, 0, 0),    # Red
        FingerType.INDEX: (0, 255, 0),    # Green
        FingerType.MIDDLE: (0, 0, 255),   # Blue
        FingerType.RING: (255, 0, 255),   # Purple
        FingerType.PINKY: (255, 165, 0),  # Orange
        FingerType.PALM: (128, 128, 128)  # Gray
    }
    
    # Process each finger type
    for finger in FingerType:
        for mask_data in annotator.mask_manager.finger_annotations[finger]["masks"]:
            mask = mask_data["mask"]
            color = colors[finger]
            
            # Apply mask color
            for c in range(3):
                combined_mask[:, :, c] = np.where(mask == 1, color[c], combined_mask[:, :, c])
    
    # Display the combined mask
    plt.figure(figsize=(10, 8))
    plt.imshow(combined_mask)
    plt.title("Combined Finger Masks")
    plt.axis('off')
    plt.show()

def main():
    """Main function"""
    # Create the application window
    root = tk.Tk()
    app = SimpleMaskAnnotatorApp(root)
    
    # Add a button to demonstrate mask access
    demo_btn = tk.Button(root, text="Show Masks (Demo)", 
                        command=lambda: show_masks_example(app))
    demo_btn.pack(pady=5)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()

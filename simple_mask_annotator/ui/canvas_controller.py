import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
from ..core.enums import FingerType, Handedness
from ..core.hand_instance import HandInstance

class CanvasController:
    """Controller for canvas operations and drawing"""
    
    def __init__(self, canvas, mask_manager):
        """Initialize the canvas controller"""
    
        self.canvas = canvas
        self.mask_manager = mask_manager
        self.current_finger = FingerType.PALM
        self.current_hand_instance = HandInstance("person_001", Handedness.RIGHT)
        self.drawing = False
        self.mask_points = []
        self.current_image = None
        self.current_image_data = None
        self.original_image_data = None  # Store original image to prevent quality loss when zooming
        self.smoothness = 0.3
        self.mask_opacity = 0.5
        self._mask_photos = {}  # Store mask photo references
    
        # Get parent widget for proper geometry management
        parent = canvas.master
    
        # Create scrollbars - using pack instead of grid
        self.h_scrollbar = tk.Scrollbar(parent, orient=tk.HORIZONTAL)
        self.v_scrollbar = tk.Scrollbar(parent, orient=tk.VERTICAL)
        
        # Place scrollbars using pack
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure canvas with scrollbars
        self.canvas.config(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)
        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)
        
        # Place canvas using pack
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
        # Finger colors for visualization
        self.finger_colors = {
            FingerType.THUMB: "red",
            FingerType.INDEX: "green",
            FingerType.MIDDLE: "blue",
            FingerType.RING: "purple",
            FingerType.PINKY: "orange",
            FingerType.PALM: "gray"
        }
        self.setup_bindings()

    def set_current_finger(self, finger_type):
        """Set the current finger type for annotations"""
        self.current_finger = finger_type
    
    def set_current_hand_instance(self, hand_instance):
        """Set the current hand instance for annotations"""
        self.current_hand_instance = hand_instance
    
    # Keep these methods for backward compatibility
    def set_current_person(self, person_id):
        """Set the current person ID for annotations"""
        self.current_hand_instance.person_id = person_id
    
    def set_current_handedness(self, handedness):
        """Set the current handedness for annotations"""
        self.current_hand_instance.handedness = handedness
    
    def set_smoothness(self, value):
        """Set the smoothness value and update preview if drawing"""
        self.smoothness = value
        
        # If we're currently drawing a curve, update the preview
        if self.drawing and len(self.mask_points) > 1:
            self.canvas.delete("temp_mask")
            # Draw temporary control points
            for x, y in self.mask_points:
                self.canvas.create_oval(x-3, y-3, x+3, y+3, 
                                      fill=self.finger_colors[self.current_finger], 
                                      tags="temp_mask")
            
            # Draw temporary smooth curve
            self.draw_mask_smooth_curve_preview()
    
    def set_opacity(self, value):
        """Set the opacity value and redraw masks"""
        self.mask_opacity = value
        self.redraw_all_masks()
    
    def redraw_all_masks(self):
        """Redraw all masks with current opacity"""
        # Clear all masks from canvas
        for finger in FingerType:
            for mask_data in self.mask_manager.finger_annotations[finger]["masks"]:
                mask_id = mask_data["id"]
                self.canvas.delete(f"mask_{mask_id}_{finger.name}")
        
        # Redraw all masks
        for finger in FingerType:
            for mask_data in self.mask_manager.finger_annotations[finger]["masks"]:
                mask_data["opacity"] = self.mask_opacity
                self.draw_mask(mask_data)
    
    def handle_click(self, event):
        """Handle mouse click on the canvas"""
        if self.current_image is None:
            return
        
        x, y = event.x, event.y
        
        # Start or continue a smooth curve
        if not self.drawing:
            self.drawing = True
            self.mask_points = [(x, y)]
            self.canvas.create_oval(x-3, y-3, x+3, y+3, 
                                  fill=self.finger_colors[self.current_finger], 
                                  tags="temp_mask")
        else:
            self.mask_points.append((x, y))
            # Draw control point
            self.canvas.create_oval(x-3, y-3, x+3, y+3, 
                                  fill=self.finger_colors[self.current_finger], 
                                  tags="temp_mask")
            
            # Draw smooth curve preview if we have at least 2 points
            if len(self.mask_points) >= 2:
                self.draw_mask_smooth_curve_preview()
    
    def handle_drag(self, event):
        """Handle mouse drag on the canvas - just for visual feedback"""
        if not self.drawing or self.current_image is None:
            return
        
        x, y = event.x, event.y
        
        # Show a temporary line from the last point to current mouse position
        if len(self.mask_points) > 0:
            last_x, last_y = self.mask_points[-1]
            # Remove previous temporary line
            self.canvas.delete("temp_drag_line")
            # Draw new temporary line
            self.canvas.create_line(last_x, last_y, x, y, 
                                   fill=self.finger_colors[self.current_finger], 
                                   width=2, tags="temp_drag_line")
    
    def handle_release(self, event):
        """Handle mouse release on the canvas"""
        if not self.drawing or self.current_image is None:
            return
        
        x, y = event.x, event.y
        
        # Remove any temporary drag line
        self.canvas.delete("temp_drag_line")
        
        # Double-click to end the smooth curve (check if close to starting point)
        if len(self.mask_points) > 1 and abs(x - self.mask_points[0][0]) < 10 and abs(y - self.mask_points[0][1]) < 10:
            # Close the smooth curve and create mask
            self.finalize_mask()
    
    def draw_mask_smooth_curve_preview(self):
        """Draw a preview of the smooth curve for mask drawing"""
        if len(self.mask_points) < 2:
            return
        
        # Generate smooth curve points
        smooth_points = self.mask_manager.generate_smooth_curve(self.mask_points, self.smoothness)
        
        # Draw smooth curve segments
        for i in range(len(smooth_points) - 1):
            p1 = smooth_points[i]
            p2 = smooth_points[i+1]
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], 
                                   fill=self.finger_colors[self.current_finger], 
                                   width=2, tags="temp_mask")
    
    def finalize_mask(self):
        """Convert temporary mask to final mask"""
        if not self.mask_points or len(self.mask_points) < 3:
            self.drawing = False
            self.canvas.delete("temp_mask")
            return
        
        if self.current_image_data is None:
            self.drawing = False
            self.canvas.delete("temp_mask")
            return
            
        # Create mask
        mask_data = self.mask_manager.create_mask_from_points(
            self.mask_points, 
            self.smoothness,
            self.current_image_data.height,
            self.current_image_data.width,
            self.current_finger,
            self.mask_opacity,
            self.current_hand_instance.person_id,
            self.current_hand_instance.handedness
        )
        
        # Draw the mask on canvas
        self.draw_mask(mask_data)
        
        # Reset
        self.drawing = False
        self.canvas.delete("temp_mask")
        self.mask_points = []
        
        # Notify the main application to update the mask list view
        if hasattr(self, 'on_mask_created') and callable(self.on_mask_created):
            self.on_mask_created()
    
    def draw_mask(self, mask_data):
        """Draw a mask on the canvas"""
        mask_id = mask_data["id"]
        finger_type = mask_data["finger"]
        mask = mask_data["mask"]
        opacity = mask_data["opacity"]

        # Convert binary mask to color image with transparency
        color = self.finger_colors[finger_type]
        r, g, b = self._parse_color(color)
        
        # Create RGBA image (with transparency)
        rgba = np.zeros((mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
        rgba[mask == 1, 0] = r
        rgba[mask == 1, 1] = g
        rgba[mask == 1, 2] = b
        rgba[mask == 1, 3] = int(255 * opacity)  # Alpha channel
        
        # Convert to PIL Image
        mask_image = Image.fromarray(rgba, 'RGBA')
        
        # Convert to Tkinter PhotoImage
        mask_photo = ImageTk.PhotoImage(mask_image)
        
        # Save reference to prevent garbage collection
        self._mask_photos[f"mask_{mask_id}_{finger_type.name}"] = mask_photo
        
        # Add to canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=mask_photo, 
                               tags=f"mask_{mask_id}_{finger_type.name}")
    
    def _parse_color(self, color):
        """Convert color name or hex to RGB values"""
        if color.startswith('#'):
            # Hex color code
            color = color.lstrip('#')
            return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        else:
            # Named color - use a Canvas to resolve it
            temp = tk.Canvas(self.canvas.master)
            temp.create_rectangle(0, 0, 1, 1, fill=color, outline='')
            r, g, b = temp.winfo_rgb(color)
            temp.destroy()
            return (r // 257, g // 257, b // 257)  # Convert from 16-bit to 8-bit color
    
    def load_image(self, image_path):
        """Load and display an image"""
        if not image_path:
            return None
            
        # Load image
        self.current_image_data = Image.open(image_path)
        self.original_image_data = self.current_image_data.copy()
        
        # Resize if necessary to fit canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 10 and canvas_height > 10:
            img_ratio = self.current_image_data.width / self.current_image_data.height
            canvas_ratio = canvas_width / canvas_height
            
            if img_ratio > canvas_ratio:  # Image is wider
                new_width = canvas_width
                new_height = int(canvas_width / img_ratio)
            else:  # Image is taller
                new_height = canvas_height
                new_width = int(canvas_height * img_ratio)
                
            self.current_image_data = self.current_image_data.resize((new_width, new_height), 
                                                                  Image.LANCZOS)
        
        # Convert to Tkinter image and display
        self.current_image = ImageTk.PhotoImage(self.current_image_data)
        self.canvas.config(width=self.current_image_data.width, height=self.current_image_data.height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image)
        
        return self.current_image_data

 
    
    def clear_canvas_masks(self):
        """Clear all masks from the canvas"""
        # Clear all masks from canvas
        for finger in FingerType:
            for mask_data in self.mask_manager.finger_annotations[finger]["masks"]:
                mask_id = mask_data["id"]
                self.canvas.delete(f"mask_{mask_id}_{finger.name}")
                if f"mask_{mask_id}_{finger.name}" in self._mask_photos:
                    del self._mask_photos[f"mask_{mask_id}_{finger.name}"]
        
        # Also clear any temporary mask drawing
        self.canvas.delete("temp_mask")
        self.drawing = False
        self.mask_points = []
        
        # Clear all canvas items that might be masks
        # This ensures that even masks without proper tracking get removed
        for item in self.canvas.find_all():
            tags = self.canvas.gettags(item)
            if any(tag.startswith("mask_") for tag in tags):
                self.canvas.delete(item)
            
        # Reset the mask photo reference dictionary
        self._mask_photos = {}
    
    def redraw_filtered_masks(self, person_id=None, handedness=None):
        """Redraw masks filtered by person_id and handedness"""
        # Clear all masks from canvas
        for finger in FingerType:
            for mask_data in self.mask_manager.finger_annotations[finger]["masks"]:
                mask_id = mask_data["id"]
                self.canvas.delete(f"mask_{mask_id}_{finger.name}")
                
        # Redraw filtered masks
        for finger in FingerType:
            for mask_data in self.mask_manager.finger_annotations[finger]["masks"]:
                if person_id and mask_data.get("person_id") != person_id:
                    continue
                if handedness and mask_data.get("handedness") != handedness:
                    continue
                    
                mask_data["opacity"] = self.mask_opacity
                self.draw_mask(mask_data)

                    
    def setup_bindings(self):
        """Set up canvas bindings for mouse events"""
        # Basic mouse click/drag/release for drawing
        self.canvas.bind("<ButtonPress-1>", self.handle_click)
        self.canvas.bind("<B1-Motion>", self.handle_drag)
        self.canvas.bind("<ButtonRelease-1>", self.handle_release)
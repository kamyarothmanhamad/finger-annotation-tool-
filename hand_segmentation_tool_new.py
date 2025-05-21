import tkinter as tk
from tkinter import filedialog, ttk, colorchooser
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import json
import os
from datetime import datetime
import uuid
from curve_drawing_tool import CurveDrawingTool

FINGER_CATEGORIES = [
    {"id": 1, "name": "thumb", "color": (255, 0, 0)},
    {"id": 2, "name": "index", "color": (0, 255, 0)},
    {"id": 3, "name": "middle", "color": (0, 0, 255)},
    {"id": 4, "name": "ring", "color": (255, 255, 0)},
    {"id": 5, "name": "pinky", "color": (255, 0, 255)},
    {"id": 6, "name": "palm", "color": (0, 255, 255)},
]


HAND_CATEGORIES = [
    {"id": 7, "name": "left_hand", "color": (255, 128, 0)},
    {"id": 8, "name": "right_hand", "color": (0, 128, 255)},
]

class HandSegmentationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Hand and Finger Mask Segmentation Tool")
        
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.left_panel = tk.Frame(self.main_frame, width=200)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, width=800, height=600, bg='gray')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.config(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)

        self.file_frame = tk.LabelFrame(self.left_panel, text="File Operations")
        self.file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.load_btn = tk.Button(self.file_frame, text="Load Image", command=self.load_image)
        self.load_btn.pack(fill=tk.X, padx=5, pady=2)
        
        self.export_btn = tk.Button(self.file_frame, text="Export COCO JSON", command=self.export_coco)
        self.export_btn.pack(fill=tk.X, padx=5, pady=2)

        self.person_frame = tk.LabelFrame(self.left_panel, text="Person Instances")
        self.person_frame.pack(fill=tk.X, padx=5, pady=5)
        self.person_list = []  
        self.selected_person = tk.StringVar()
        self.selected_person.set('1')  
        self.person_listbox = tk.Listbox(self.person_frame, height=3)
        self.person_listbox.pack(fill=tk.X, padx=5, pady=2)
        self.person_listbox.insert(tk.END, 'Person 1')
        self.person_list = ['1']
        self.person_listbox.selection_set(0)
        self.person_listbox.bind('<<ListboxSelect>>', self.on_person_select)
        self.add_person_btn = tk.Button(self.person_frame, text="Add Person", command=self.add_person)
        self.add_person_btn.pack(fill=tk.X, padx=5, pady=2)

        self.hand_frame = tk.LabelFrame(self.left_panel, text="Hand Selection")
        self.hand_frame.pack(fill=tk.X, padx=5, pady=5)
        self.selected_hand = tk.StringVar()
        self.selected_hand.set('left')
        tk.Radiobutton(self.hand_frame, text="Left Hand", variable=self.selected_hand, value="left").pack(anchor=tk.W, padx=5, pady=2)
        tk.Radiobutton(self.hand_frame, text="Right Hand", variable=self.selected_hand, value="right").pack(anchor=tk.W, padx=5, pady=2)

        self.finger_frame = tk.LabelFrame(self.left_panel, text="Finger Selection")
        self.finger_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.selected_finger = tk.StringVar()
        self.selected_finger.set(FINGER_CATEGORIES[0]["name"])  
        
        for category in FINGER_CATEGORIES:
            color_hex = "#{:02x}{:02x}{:02x}".format(*category["color"])
            rb = tk.Radiobutton(self.finger_frame, text=category["name"].capitalize(), 
                               variable=self.selected_finger, value=category["name"],
                               bg=color_hex, selectcolor=color_hex,
                               indicatoron=0, width=15)
            rb.pack(anchor=tk.W, padx=5, pady=2)

        self.tools_frame = tk.LabelFrame(self.left_panel, text="Drawing Tools")
        self.tools_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.drawing_mode = tk.StringVar()
        
        tk.Radiobutton(self.tools_frame, text="Polygon", variable=self.drawing_mode, 
                      value="polygon").pack(anchor=tk.W, padx=5, pady=2)
        tk.Radiobutton(self.tools_frame, text="Curve", variable=self.drawing_mode, 
                      value="curve").pack(anchor=tk.W, padx=5, pady=2)
        tk.Radiobutton(self.tools_frame, text="Bounding Box", variable=self.drawing_mode, 
                      value="bbox").pack(anchor=tk.W, padx=5, pady=2)
    
        self.curve_frame = tk.LabelFrame(self.left_panel, text="Curve Settings")
        self.curve_frame.pack(fill=tk.X, padx=5, pady=5)
   
        tk.Label(self.curve_frame, text="Curve Tension:").pack(anchor=tk.W, padx=5, pady=2)
        self.curve_tension = tk.DoubleVar()
        self.curve_tension.set(0.5)  
        self.tension_slider = tk.Scale(self.curve_frame, from_=0.0, to=1.0, resolution=0.1, orient=tk.HORIZONTAL, 
                                     variable=self.curve_tension, command=self.update_curve_tension)
        self.tension_slider.pack(fill=tk.X, padx=5, pady=2)

        self.closed_curve = tk.BooleanVar()
        self.closed_curve.set(True)  

        self.complete_curve_btn = tk.Button(self.curve_frame, text="Complete Curve", 
                                         command=self.complete_curve)
        self.complete_curve_btn.pack(fill=tk.X, padx=5, pady=2)

        self.action_frame = tk.LabelFrame(self.left_panel, text="Actions")
        self.action_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.clear_btn = tk.Button(self.action_frame, text="Clear Current Finger", command=self.clear_current_mask)
        self.clear_btn.pack(fill=tk.X, padx=5, pady=2)
        
        self.clear_all_btn = tk.Button(self.action_frame, text="Clear All Masks", command=self.clear_all_masks)
        self.clear_all_btn.pack(fill=tk.X, padx=5, pady=2)
        
        self.undo_btn = tk.Button(self.action_frame, text="Undo Last Action", command=self.undo_last_action)
        self.undo_btn.pack(fill=tk.X, padx=5, pady=2)

        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.image = None
        self.photo = None
        self.image_path = None
   
        self.masks = {}  
        self.init_masks()
        self.current_polygon_points = []
        self.polygon_line_ids = []
        self.action_history = []
   
        self.curve_tool = CurveDrawingTool()
        self.current_control_point_id = None
        self.control_point_ids = []
        self.curve_line_ids = []

        self.current_bbox_start = None
        self.current_bbox_rect_id = None
        self.hand_bboxes = {}  # {person_id: {hand: [x1, y1, x2, y2]}}
        self.init_hand_bboxes()
        
     
        self.canvas.bind("<ButtonPress-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)
       
        self.root.bind("<Control-z>", lambda event: self.undo_last_action())
        self.root.bind("<Escape>", lambda event: self.cancel_current_drawing())        
        self.root.bind("<Return>", lambda event: self.complete_current_drawing())
        
        self.canvas_frame.bind("<Configure>", self.on_canvas_resize)
    
    def canvas_to_original_coords(self, canvas_x, canvas_y):
        """Convert canvas coordinates to original image coordinates"""
        if hasattr(self, 'original_image') and self.image.size != self.original_image.size:
            scale_x = self.original_image.width / self.image.width
            scale_y = self.original_image.height / self.image.height
            original_x = int(canvas_x * scale_x)
            original_y = int(canvas_y * scale_y)
            return original_x, original_y
        else:
            return canvas_x, canvas_y
    
    def original_to_canvas_coords(self, original_x, original_y):
        """Convert original image coordinates to canvas coordinates"""
        if hasattr(self, 'original_image') and self.image.size != self.original_image.size:
            scale_x = self.image.width / self.original_image.width
            scale_y = self.image.height / self.original_image.height
            canvas_x = int(original_x * scale_x)
            canvas_y = int(original_y * scale_y)
            return canvas_x, canvas_y
        else:
            return original_x, original_y
        
    def init_masks(self):
        """Initialize the masks data structure for all persons, hands, and fingers"""
        self.masks = {}
        for person_id in self.person_list:
            self.masks[person_id] = {}
            for hand in ['left', 'right']:
                self.masks[person_id][hand] = {}
                for category in FINGER_CATEGORIES:
           
                    mask = None
                    draw = None
                    if hasattr(self, 'original_image') and self.original_image:
                        mask = Image.new('L', self.original_image.size, 0)
                        draw = ImageDraw.Draw(mask)
                    
                    self.masks[person_id][hand][category["name"]] = {
                        "mask": mask,
                        "draw": draw,
                        "polygons": [],
                        "color": category["color"]
                    }
    
    def init_hand_bboxes(self):
        """Initialize the hand bounding boxes data structure for all persons"""
        self.hand_bboxes = {}
        for person_id in self.person_list:
            self.hand_bboxes[person_id] = {
                'left': None,  # Will be [x1, y1, x2, y2] when defined
                'right': None  # Will be [x1, y1, x2, y2] when defined
            }
    
    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[('Image files', '*.jpg *.jpeg *.png')])
        if file_path:
            self.image_path = file_path
            original_image = Image.open(file_path).convert('RGB')
            
   
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
     
            if canvas_width < 50 or canvas_height < 50:
                canvas_width = 800
                canvas_height = 600
            
            img_width, img_height = original_image.size
            width_ratio = canvas_width / img_width
            height_ratio = canvas_height / img_height
            scale_factor = min(width_ratio, height_ratio)
  
            if scale_factor < 1: 
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                self.image = original_image.resize((new_width, new_height), Image.LANCZOS)
                self.original_image = original_image  
       
                self.canvas.config(scrollregion=(0, 0, new_width, new_height))
            else:  
                self.image = original_image
                self.original_image = original_image

                self.canvas.config(scrollregion=(0, 0, img_width, img_height))
            
            self.photo = ImageTk.PhotoImage(self.image)
            self.canvas.delete('all')
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo, tags='image')
            
            for person_id in self.person_list:
                for hand in ['left', 'right']:
                    for finger_name in self.masks[person_id][hand]:
                        self.masks[person_id][hand][finger_name]['mask'] = Image.new('L', self.original_image.size, 0)
                        self.masks[person_id][hand][finger_name]['draw'] = ImageDraw.Draw(self.masks[person_id][hand][finger_name]['mask'])
                        self.masks[person_id][hand][finger_name]['polygons'] = []
            
            self.current_polygon_points = []
            self.polygon_line_ids = []
            self.action_history = []

            self.curve_tool.clear_control_points()
            self.clear_curve_display()
            
            self.status_var.set(f'Loaded image: {os.path.basename(file_path)}')
    
    def get_current_finger(self):
        return self.selected_finger.get()
    
    def get_current_person(self):
        return self.selected_person.get()
    
    def get_current_hand(self):
        return self.selected_hand.get()
    
    def get_finger_color(self, finger_name):
        for category in FINGER_CATEGORIES:
            if category["name"] == finger_name:
                return category["color"]
        return (255, 255, 255) 
    
    def get_hand_color(self, hand):
        """Get the color for a hand (left or right)"""
        for category in HAND_CATEGORIES:
            if category["name"] == f"{hand}_hand":
                color_rgb = category["color"]
                return "#{:02x}{:02x}{:02x}".format(*color_rgb)
        return "#ffffff"  
    
    def start_drawing(self, event):
        if not self.image:
            return
        
        # Get canvas coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Convert canvas coordinates to original image coordinates
        original_x, original_y = self.canvas_to_original_coords(canvas_x, canvas_y)
        
        current_finger = self.get_current_finger()
        current_person = self.get_current_person()
        current_hand = self.get_current_hand()
        
        if self.drawing_mode.get() == "polygon":
            self.current_polygon_points.append((original_x, original_y))
            
            # Draw point on canvas
            point_radius = 3
            point_id = self.canvas.create_oval(
                canvas_x - point_radius, canvas_y - point_radius,
                canvas_x + point_radius, canvas_y + point_radius,
                fill="red", outline="white", tags="polygon_point"
            )
            
            # Draw line if we have at least 2 points
            if len(self.current_polygon_points) > 1:
                # Get the previous point in original coordinates
                prev_original_x, prev_original_y = self.current_polygon_points[-2]
                
                # Convert back to canvas coordinates for display
                prev_canvas_x, prev_canvas_y = self.original_to_canvas_coords(prev_original_x, prev_original_y)
                
                line_id = self.canvas.create_line(prev_canvas_x, prev_canvas_y, canvas_x, canvas_y, 
                                                fill="yellow", width=2, tags="polygon_line")
                self.polygon_line_ids.append(line_id)
            
            # If we have at least 3 points, check if clicked near the first point to close polygon
            if len(self.current_polygon_points) > 2:
                first_original_x, first_original_y = self.current_polygon_points[0]
                
                # Convert to canvas coordinates for comparison
                first_canvas_x, first_canvas_y = self.original_to_canvas_coords(first_original_x, first_original_y)
                
                if abs(canvas_x - first_canvas_x) < 10 and abs(canvas_y - first_canvas_y) < 10:
                    self.complete_polygon()
        
        elif self.drawing_mode.get() == "curve":
            # Add control point to curve (in original image coordinates)
            point_index = self.curve_tool.add_control_point((original_x, original_y))
            
            # Draw control point on canvas
            point_radius = 4
            point_id = self.canvas.create_oval(
                canvas_x - point_radius, canvas_y - point_radius,
                canvas_x + point_radius, canvas_y + point_radius,
                fill="blue", outline="white", tags="curve_point"
            )
            self.control_point_ids.append(point_id)
            
            # Update curve display
            self.update_curve_display()
            
        elif self.drawing_mode.get() == "bbox":
            # Start drawing a bounding box
            self.start_bounding_box(canvas_x, canvas_y, original_x, original_y)
    
    def draw(self, event):
        if not self.image:
            return
        
      
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Convert canvas coordinates to original image coordinates
        original_x, original_y = self.canvas_to_original_coords(canvas_x, canvas_y)
        
        if self.drawing_mode.get() == "bbox" and self.current_bbox_start:
            # Update the bounding box as the mouse is dragged
            self.update_bounding_box(canvas_x, canvas_y, original_x, original_y)
    
    def stop_drawing(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Convert canvas coordinates to original image coordinates
        original_x, original_y = self.canvas_to_original_coords(canvas_x, canvas_y)
            
        if self.drawing_mode.get() == "bbox" and self.current_bbox_start:
            # Complete the bounding box when mouse is released
            self.complete_bounding_box(canvas_x, canvas_y, original_x, original_y)
    
    def complete_polygon(self, event=None):
        if len(self.current_polygon_points) < 3:
            self.status_var.set("Need at least 3 points to create a polygon")
            return
        
        current_finger = self.get_current_finger()
        current_person = self.get_current_person()
        current_hand = self.get_current_hand()
        
        # Close the polygon by connecting last point to first point
        if self.current_polygon_points[0] != self.current_polygon_points[-1]:
            self.current_polygon_points.append(self.current_polygon_points[0])
        
        self.masks[current_person][current_hand][current_finger]["draw"].polygon(
            self.current_polygon_points,
            fill=255,
            outline=255
        )
  
        self.masks[current_person][current_hand][current_finger]["polygons"].append(
            [coord for point in self.current_polygon_points for coord in point]
        )
        
        self.action_history.append({
            "type": "polygon",
            "person": current_person,
            "hand": current_hand,
            "finger": current_finger,
            "points": self.current_polygon_points.copy()
        })
        
        self.canvas.delete("polygon_point")
        self.canvas.delete("polygon_line")
        self.current_polygon_points = []
        self.polygon_line_ids = []
        
        self.update_canvas()
        self.status_var.set(f"Added polygon to {current_finger} ({current_hand} hand, person {current_person})")
    
    def cancel_polygon(self, event=None):
        self.canvas.delete("polygon_point")
        self.canvas.delete("polygon_line")
        self.current_polygon_points = []
        self.polygon_line_ids = []
        self.status_var.set("Polygon drawing canceled")
    
    def update_curve_tension(self, value=None):
        """Update the tension parameter of the curve tool"""
        if hasattr(self, 'curve_tool'):
            self.curve_tool.set_tension(self.curve_tension.get())
            self.update_curve_display()
    
    def update_curve_display(self):
        """Update the display of the curve on the canvas"""
        for line_id in self.curve_line_ids:
            self.canvas.delete(line_id)
        self.curve_line_ids = []
        
        curve_points = self.curve_tool.get_curve_points()
        if len(curve_points) < 2:
            return

        canvas_curve_points = []
        for x, y in curve_points:
            canvas_x, canvas_y = self.original_to_canvas_coords(x, y)
            canvas_curve_points.append((canvas_x, canvas_y))

        for i in range(len(canvas_curve_points) - 1):
            line_id = self.canvas.create_line(
                canvas_curve_points[i][0], canvas_curve_points[i][1],
                canvas_curve_points[i+1][0], canvas_curve_points[i+1][1],
                fill="cyan", width=2, tags="curve_line"
            )
            self.curve_line_ids.append(line_id)
    
    def clear_curve_display(self):
        """Clear the curve display from the canvas"""
        self.canvas.delete("curve_point")
        self.canvas.delete("curve_line")
        self.control_point_ids = []
        self.curve_line_ids = []

    def complete_curve(self, event=None):
        """Complete the curve and add it to the current finger mask"""
        if not hasattr(self, 'original_image') or not self.original_image:
            self.status_var.set("Please load an image first")
            return
            
        if len(self.curve_tool.control_points) < 2:
            self.status_var.set("Need at least 2 control points to create a curve")
            return
        
        current_finger = self.get_current_finger()
        current_person = self.get_current_person()
        current_hand = self.get_current_hand()
  
        if self.masks[current_person][current_hand][current_finger]["mask"] is None:
            self.masks[current_person][current_hand][current_finger]["mask"] = Image.new('L', self.original_image.size, 0)
            self.masks[current_person][current_hand][current_finger]["draw"] = ImageDraw.Draw(self.masks[current_person][current_hand][current_finger]["mask"])
        
        if self.closed_curve.get():
            curve_mask = self.curve_tool.create_closed_mask(self.original_image.size)
        else:
            curve_mask = self.curve_tool.create_mask(self.original_image.size, 5)
        
        self.masks[current_person][current_hand][current_finger]["mask"] = Image.composite(
            Image.new('L', self.original_image.size, 255),
            self.masks[current_person][current_hand][current_finger]["mask"],
            curve_mask
        )
        self.masks[current_person][current_hand][current_finger]["draw"] = ImageDraw.Draw(self.masks[current_person][current_hand][current_finger]["mask"])
        self.action_history.append({
            "type": "curve",
            "person": current_person,
            "hand": current_hand,
            "finger": current_finger,
            "control_points": self.curve_tool.control_points.copy(),
            "closed": self.closed_curve.get(),
            "width": 5 
        })
        self.clear_curve_display()
        self.curve_tool.clear_control_points()
        self.update_canvas()
        self.status_var.set(f"Added curve to {current_finger} ({current_hand} hand, person {current_person})")
    
    def cancel_curve(self, event=None):
        """Cancel the current curve drawing"""
        self.clear_curve_display()
        self.curve_tool.clear_control_points()
        self.status_var.set("Curve drawing canceled")
    
    def cancel_current_drawing(self, event=None):
        """Cancel the current drawing operation based on the drawing mode"""
        if self.drawing_mode.get() == "polygon":
            self.cancel_polygon()
        elif self.drawing_mode.get() == "curve":
            self.cancel_curve()
        elif self.drawing_mode.get() == "bbox":
            self.cancel_bounding_box()
    
    def complete_current_drawing(self, event=None):
        """Complete the current drawing operation based on the drawing mode"""
        if self.drawing_mode.get() == "polygon":
            self.complete_polygon()
        elif self.drawing_mode.get() == "curve":
            self.complete_curve()
    
    def clear_current_mask(self):
        current_finger = self.get_current_finger()
        current_person = self.get_current_person()
        current_hand = self.get_current_hand()
        
        if self.image and self.masks[current_person][current_hand][current_finger]["mask"]:
            self.action_history.append({
                "type": "clear",
                "person": current_person,
                "hand": current_hand,
                "finger": current_finger,
                "mask": self.masks[current_person][current_hand][current_finger]["mask"].copy(),
                "polygons": self.masks[current_person][current_hand][current_finger]["polygons"].copy()
            })
            
            self.masks[current_person][current_hand][current_finger]["mask"] = Image.new("L", self.original_image.size, 0)
            self.masks[current_person][current_hand][current_finger]["draw"] = ImageDraw.Draw(self.masks[current_person][current_hand][current_finger]["mask"])
            self.masks[current_person][current_hand][current_finger]["polygons"] = []
            
            self.update_canvas()
            self.status_var.set(f"Cleared {current_finger} mask ({current_hand} hand, person {current_person})")
    
    def clear_all_masks(self):
        if self.image:
            saved_masks = {}
            for person_id in self.person_list:
                saved_masks[person_id] = {}
                for hand in ['left', 'right']:
                    saved_masks[person_id][hand] = {}
                    for finger_name in self.masks[person_id][hand]:
                        saved_masks[person_id][hand][finger_name] = {
                            "mask": self.masks[person_id][hand][finger_name]["mask"].copy() if self.masks[person_id][hand][finger_name]["mask"] else None,
                            "polygons": self.masks[person_id][hand][finger_name]["polygons"].copy()
                        }
            
            self.action_history.append({
                "type": "clear_all",
                "masks": saved_masks
            })

            for person_id in self.person_list:
                for hand in ['left', 'right']:
                    for finger_name in self.masks[person_id][hand]:
                        self.masks[person_id][hand][finger_name]["mask"] = Image.new("L", self.original_image.size, 0)
                        self.masks[person_id][hand][finger_name]["draw"] = ImageDraw.Draw(self.masks[person_id][hand][finger_name]["mask"])
                        self.masks[person_id][hand][finger_name]["polygons"] = []
            
            self.update_canvas()
            self.status_var.set("Cleared all masks")
    
    def undo_last_action(self):
        if not self.action_history:
            self.status_var.set("Nothing to undo")
            return
        
        action = self.action_history.pop()
        
        if action["type"] == "polygon":
            person = action["person"]
            hand = action["hand"]
            finger = action["finger"]

            if self.masks[person][hand][finger]["polygons"]:
                self.masks[person][hand][finger]["polygons"].pop()
    
            self.masks[person][hand][finger]["mask"] = Image.new("L", self.original_image.size, 0)
            self.masks[person][hand][finger]["draw"] = ImageDraw.Draw(self.masks[person][hand][finger]["mask"])
   
            for hist_action in self.action_history:
                if (hist_action["type"] == "polygon" and hist_action["finger"] == finger 
                        and hist_action["person"] == person and hist_action["hand"] == hand):
                    self.masks[person][hand][finger]["draw"].polygon(
                        hist_action["points"],
                        fill=255,
                        outline=255
                    )
                elif (hist_action["type"] == "curve" and hist_action["finger"] == finger 
                        and hist_action["person"] == person and hist_action["hand"] == hand):
                    temp_curve_tool = CurveDrawingTool()
                    for point in hist_action["control_points"]:
                        temp_curve_tool.add_control_point(point)
  
                    if hist_action["closed"]:
                        curve_mask = temp_curve_tool.create_closed_mask(self.original_image.size)
                    else:
                        curve_mask = temp_curve_tool.create_mask(self.original_image.size, hist_action["width"])
   
                    self.masks[person][hand][finger]["mask"] = Image.composite(
                        Image.new('L', self.original_image.size, 255),
                        self.masks[person][hand][finger]["mask"],
                        curve_mask
                    )
                    self.masks[person][hand][finger]["draw"] = ImageDraw.Draw(self.masks[person][hand][finger]["mask"])
        
        elif action["type"] == "curve":
            person = action["person"]
            hand = action["hand"]
            finger = action["finger"]
            # Redraw mask without this curve
            self.masks[person][hand][finger]["mask"] = Image.new("L", self.original_image.size, 0)
            self.masks[person][hand][finger]["draw"] = ImageDraw.Draw(self.masks[person][hand][finger]["mask"])
            
            # Redraw all remaining actions for this finger
            for hist_action in self.action_history:
                if (hist_action["type"] == "polygon" and hist_action["finger"] == finger 
                        and hist_action["person"] == person and hist_action["hand"] == hand):
                    self.masks[person][hand][finger]["draw"].polygon(
                        hist_action["points"],
                        fill=255,
                        outline=255
                    )
                elif (hist_action["type"] == "curve" and hist_action["finger"] == finger 
                        and hist_action["person"] == person and hist_action["hand"] == hand):
                    # Recreate the curve tool temporarily
                    temp_curve_tool = CurveDrawingTool()
                    for point in hist_action["control_points"]:
                        temp_curve_tool.add_control_point(point)
                    
                    # Create mask from curve
                    if hist_action["closed"]:
                        curve_mask = temp_curve_tool.create_closed_mask(self.original_image.size)
                    else:
                        curve_mask = temp_curve_tool.create_mask(self.original_image.size, hist_action["width"])
                    
                    # Composite the curve mask onto the finger mask
                    self.masks[person][hand][finger]["mask"] = Image.composite(
                        Image.new('L', self.original_image.size, 255),
                        self.masks[person][hand][finger]["mask"],
                        curve_mask
                    )
                    self.masks[person][hand][finger]["draw"] = ImageDraw.Draw(self.masks[person][hand][finger]["mask"])
        
        elif action["type"] == "clear":
            person = action["person"]
            hand = action["hand"]
            finger = action["finger"]
            self.masks[person][hand][finger]["mask"] = action["mask"]
            self.masks[person][hand][finger]["draw"] = ImageDraw.Draw(self.masks[person][hand][finger]["mask"])
            self.masks[person][hand][finger]["polygons"] = action["polygons"]
        
        elif action["type"] == "clear_all":
            for person_id, hands in action["masks"].items():
                for hand, fingers in hands.items():
                    for finger_name, mask_data in fingers.items():
                        self.masks[person_id][hand][finger_name]["mask"] = mask_data["mask"]
                        self.masks[person_id][hand][finger_name]["draw"] = ImageDraw.Draw(self.masks[person_id][hand][finger_name]["mask"])
                        self.masks[person_id][hand][finger_name]["polygons"] = mask_data["polygons"]
        
        elif action["type"] == "bbox":
            person = action["person"]
            hand = action["hand"]
            # Remove bounding box
            self.hand_bboxes[person][hand] = None
        
        self.update_canvas()
        self.status_var.set("Undid last action")
    
    def update_canvas(self):
        if not self.image:
            return
        
        composite = self.image.copy().convert("RGBA")
        
        overlay = Image.new("RGBA", self.image.size, (0, 0, 0, 0))
        
        # Add each finger mask with its color for all persons and hands
        for person_id in self.person_list:
            for hand in ['left', 'right']:
                for finger_name, finger_data in self.masks[person_id][hand].items():
                    # Use get() with None default to avoid KeyError
                    if finger_data.get("mask") is not None:
                        # Get color for this finger
                        r, g, b = finger_data["color"]
                        
                        # Create colored mask
                        colored_mask = Image.new("RGBA", self.original_image.size, (r, g, b, 128))
                        
                        # Apply mask
                        masked_overlay = Image.composite(
                            colored_mask, 
                            Image.new("RGBA", self.original_image.size, (0, 0, 0, 0)),
                            finger_data["mask"]
                        )
                        
                        # Resize the masked overlay if the displayed image is scaled
                        if hasattr(self, 'original_image') and self.image.size != self.original_image.size:
                            masked_overlay = masked_overlay.resize(self.image.size, Image.LANCZOS)
                        
                        # Composite onto overlay
                        overlay = Image.alpha_composite(overlay, masked_overlay)
        
        # Composite overlay onto image
        composite = Image.alpha_composite(composite, overlay)
        
        # Update display
        self.photo = ImageTk.PhotoImage(composite)
        self.canvas.delete("image")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo, tags="image")
        
        # Draw bounding boxes for all hands
        self.canvas.delete("hand_bbox")
        for person_id in self.person_list:
            for hand in ['left', 'right']:
                bbox = self.hand_bboxes.get(person_id, {}).get(hand)
                if bbox:
                    # Get color for this hand
                    color = self.get_hand_color(hand)
                    
                    # Convert original coordinates to canvas coordinates if needed
                    canvas_bbox = []
                    for i in range(len(bbox)):
                        coord_x = bbox[i] if i % 2 == 0 else bbox[i-1]
                        coord_y = bbox[i] if i % 2 == 1 else bbox[i+1]
                        canvas_x, canvas_y = self.original_to_canvas_coords(coord_x, coord_y)
                        if i % 2 == 0:
                            canvas_bbox.append(canvas_x)
                        else:
                            canvas_bbox.append(canvas_y)
                    
                    # Make sure we have 4 coordinates
                    if len(canvas_bbox) == 4:
                        # Draw bounding box on canvas
                        self.canvas.create_rectangle(
                            canvas_bbox[0], canvas_bbox[1], canvas_bbox[2], canvas_bbox[3],
                            outline=color, width=2, tags="hand_bbox",
                            dash=(4, 4)  # Create dashed line for bbox
                        )
                        
                        # Add hand label
                        label_text = f"Person {person_id} - {hand.capitalize()} Hand"
                        self.canvas.create_text(
                            canvas_bbox[0] + 5, canvas_bbox[1] - 5,
                            text=label_text, fill=color, anchor=tk.SW,
                            tags="hand_bbox"
                        )
    
    def export_coco(self):
        if not self.image or not self.image_path:
            self.status_var.set("No image loaded")
            return
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"{os.path.splitext(os.path.basename(self.image_path))[0]}_annotations.json"
        )
        
        if not file_path:
            return
        
        # Create COCO format data structure
        coco_data = {
            "info": {
                "description": "Hand segmentation dataset",
                "url": "",
                "version": "1.0",
                "year": datetime.now().year,
                "contributor": "",
                "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "licenses": [
                {
                    "id": 1,
                    "name": "Attribution-NonCommercial",
                    "url": "http://creativecommons.org/licenses/by-nc/2.0/"
                }
            ],
            "categories": [
                {"id": cat["id"], "name": cat["name"], "supercategory": "hand"}
                for cat in FINGER_CATEGORIES + HAND_CATEGORIES
            ],
            "images": [
                {
                    "id": 1,
                    "license": 1,
                    "file_name": os.path.basename(self.image_path),
                    "height": self.image.height,
                    "width": self.image.width,
                    "date_captured": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            ],
            "annotations": []
        }
        
        # Add annotations for each person, hand, and finger
        annotation_id = 1
        for person_id in self.person_list:
            for hand in ['left', 'right']:
                for category in FINGER_CATEGORIES:
                    finger_name = category["name"]
                    category_id = category["id"]
                    polygons = self.masks[person_id][hand][finger_name]["polygons"]
                    # If no polygons but we have a mask, convert mask to polygons
                    if not polygons and self.masks[person_id][hand][finger_name]["mask"]:
                        mask_array = np.array(self.masks[person_id][hand][finger_name]["mask"])
                        from skimage import measure
                        contours = measure.find_contours(mask_array, 0.5)
                        for contour in contours:
                            if len(contour) > 100:
                                step = len(contour) // 100 + 1
                                contour = contour[::step]
                            polygon = []
                            for point in contour:
                                y, x = point
                                polygon.extend([float(x), float(y)])
                            polygons.append(polygon)
                    for polygon in polygons:
                        xs = polygon[0::2]
                        ys = polygon[1::2]
                        x_min = min(xs)
                        y_min = min(ys)
                        width = max(xs) - x_min
                        height = max(ys) - y_min
                        area = width * height
                        annotation = {
                            "id": annotation_id,
                            "image_id": 1,
                            "category_id": category_id,
                            "segmentation": [polygon],
                            "area": float(area),
                            "bbox": [float(x_min), float(y_min), float(width), float(height)],
                            "iscrowd": 0,
                            "person_id": int(person_id),
                            "hand": hand
                        }
                        coco_data["annotations"].append(annotation)
                        annotation_id += 1
            
            # Add hand bounding boxes to annotations
            for hand_type in ['left', 'right']:
                bbox = self.hand_bboxes.get(person_id, {}).get(hand_type)
                if bbox:
                    # Get the category ID for this hand type
                    hand_category_id = None
                    for cat in HAND_CATEGORIES:
                        if cat["name"] == f"{hand_type}_hand":
                            hand_category_id = cat["id"]
                            break
                    
                    if hand_category_id:
                        x1, y1, x2, y2 = bbox
                        width = x2 - x1
                        height = y2 - y1
                        area = width * height
                        
                        # Add bounding box annotation
                        annotation = {
                            "id": annotation_id,
                            "image_id": 1,
                            "category_id": hand_category_id,
                            "segmentation": [],  # No segmentation for bbox
                            "area": float(area),
                            "bbox": [float(x1), float(y1), float(width), float(height)],
                            "iscrowd": 0,
                            "person_id": int(person_id),
                            "hand": hand_type
                        }
                        coco_data["annotations"].append(annotation)
                        annotation_id += 1
        
        # Save to file
        with open(file_path, 'w') as f:
            json.dump(coco_data, f, indent=2)
        
        self.status_var.set(f"Exported COCO annotations to {os.path.basename(file_path)}")

    def on_canvas_resize(self, event):
        # Only resize if we have an image loaded
        if hasattr(self, 'original_image') and self.original_image:
            # Get new canvas dimensions
            canvas_width = event.width
            canvas_height = event.height
            
            # Only proceed if dimensions are reasonable
            if canvas_width > 50 and canvas_height > 50:
                # Calculate scaling factor to fit image within canvas while maintaining aspect ratio
                img_width, img_height = self.original_image.size
                width_ratio = canvas_width / img_width
                height_ratio = canvas_height / img_height
                scale_factor = min(width_ratio, height_ratio)
                
                # Decide whether to scale or use scrollbars
                if scale_factor < 1:  # Image is larger than canvas
                    # Scale down the image to fit the canvas
                    new_width = int(img_width * scale_factor)
                    new_height = int(img_height * scale_factor)
                    self.image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Configure canvas for the scaled image
                    self.canvas.config(scrollregion=(0, 0, new_width, new_height))
                else:  # Image is smaller than or equal to canvas
                    self.image = self.original_image
                    
                    # Configure canvas for the original image
                    self.canvas.config(scrollregion=(0, 0, img_width, img_height))
                
                # Update the display
                self.update_canvas()
    
    def add_person(self):
        """Add a new person instance"""
        new_id = str(int(self.person_list[-1]) + 1) if self.person_list else '1'
        self.person_list.append(new_id)
        self.person_listbox.insert(tk.END, f'Person {new_id}')
        
        # Initialize masks for the new person
        self.masks[new_id] = {}
        for hand in ['left', 'right']:
            self.masks[new_id][hand] = {}
            for category in FINGER_CATEGORIES:
                # Initialize with empty image if original_image exists, otherwise None
                mask = None
                draw = None
                if hasattr(self, 'original_image') and self.original_image:
                    mask = Image.new('L', self.original_image.size, 0)
                    draw = ImageDraw.Draw(mask)
                
                self.masks[new_id][hand][category["name"]] = {
                    "mask": mask,
                    "draw": draw,
                    "polygons": [],
                    "color": category["color"]
                }
        
        # Initialize bounding boxes for the new person
        self.hand_bboxes[new_id] = {
            'left': None,
            'right': None
        }
        
        self.person_listbox.selection_clear(0, tk.END)
        self.person_listbox.selection_set(tk.END)
        self.selected_person.set(new_id)
    
    def on_person_select(self, event):
        selection = self.person_listbox.curselection()
        if selection:
            idx = selection[0]
            self.selected_person.set(self.person_list[idx])
    
    def start_bounding_box(self, canvas_x, canvas_y, original_x, original_y):
        """Start drawing a bounding box from the given point"""
        current_person = self.get_current_person()
        current_hand = self.get_current_hand()
        
        # Record starting point
        self.current_bbox_start = (original_x, original_y)
        
        # Create a rectangle on canvas
        self.current_bbox_rect_id = self.canvas.create_rectangle(
            canvas_x, canvas_y, canvas_x, canvas_y,
            outline=self.get_hand_color(current_hand),
            width=2,
            tags="bbox"
        )
    
    def update_bounding_box(self, canvas_x, canvas_y, original_x, original_y):
        """Update the bounding box as the user drags the mouse"""
        if self.current_bbox_start and self.current_bbox_rect_id:
            # Update rectangle on canvas
            start_x, start_y = self.current_bbox_start
            
            # Convert original coordinates to canvas coordinates
            canvas_start_x, canvas_start_y = self.original_to_canvas_coords(start_x, start_y)
                
            self.canvas.coords(self.current_bbox_rect_id, canvas_start_x, canvas_start_y, canvas_x, canvas_y)
    
    def complete_bounding_box(self, canvas_x, canvas_y, original_x, original_y):
        """Complete the bounding box and store it"""
        if not self.current_bbox_start:
            return
            
        current_person = self.get_current_person()
        current_hand = self.get_current_hand()
        
        # Calculate the final bbox coordinates
        x1, y1 = self.current_bbox_start
        x2, y2 = original_x, original_y
        
        # Ensure x1 < x2 and y1 < y2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
            
        # Store the bounding box
        self.hand_bboxes[current_person][current_hand] = [x1, y1, x2, y2]
        
        # Save action for undo
        self.action_history.append({
            "type": "bbox",
            "person": current_person,
            "hand": current_hand,
            "bbox": [x1, y1, x2, y2]
        })
        
        # Clear temporary drawing
        self.canvas.delete("bbox")
        self.current_bbox_start = None
        self.current_bbox_rect_id = None
        
        # Update canvas to show the bounding box
        self.update_canvas()
        self.status_var.set(f"Added bounding box for {current_hand} hand (person {current_person})")
    
    def cancel_bounding_box(self):
        """Cancel the current bounding box drawing"""
        if self.current_bbox_rect_id:
            self.canvas.delete(self.current_bbox_rect_id)
            self.current_bbox_rect_id = None
            self.current_bbox_start = None
            self.status_var.set("Bounding box drawing canceled")

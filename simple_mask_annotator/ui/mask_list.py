import tkinter as tk
from tkinter import ttk
from ..core.enums import FingerType

class MaskListView:
    """UI component for displaying the list of masks"""
    
    def __init__(self, parent, mask_manager, canvas_controller):
        """Initialize the mask list view"""
        self.parent = parent
        self.mask_manager = mask_manager
        self.canvas_controller = canvas_controller
        
        # Create the frame
        self.frame = ttk.LabelFrame(parent, text="Mask Annotations")
        
        # Mask list
        self.masks_tree = ttk.Treeview(self.frame, 
                                      columns=("id", "finger", "person", "hand", "size"), 
                                      show="headings", selectmode="browse")
        self.masks_tree.heading("id", text="ID")
        self.masks_tree.heading("finger", text="Finger")
        self.masks_tree.heading("person", text="Person ID")
        self.masks_tree.heading("hand", text="Hand")
        self.masks_tree.heading("size", text="Size")
        self.masks_tree.column("id", width=40)
        self.masks_tree.column("finger", width=80)
        self.masks_tree.column("person", width=80)
        self.masks_tree.column("hand", width=60)
        self.masks_tree.column("size", width=80)
        self.masks_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbar for the tree
        masks_scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.masks_tree.yview)
        masks_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.masks_tree.configure(yscrollcommand=masks_scrollbar.set)
        
        # Button frame
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        # Delete button
        self.delete_btn = ttk.Button(button_frame, text="Delete Selected", 
                                    command=self.delete_selected_mask)
        self.delete_btn.pack(fill=tk.X, pady=5)
    
    def update_mask_list(self, filter_person_id=None, filter_handedness=None):
        """Update the masks list in the UI with optional filtering"""
        # Clear previous entries
        self.clear_mask_list()
        
        # Add all finger masks to the tree
        for finger in FingerType:
            for mask_data in self.mask_manager.finger_annotations[finger]["masks"]:
                # Apply filters if provided
                if filter_person_id and mask_data.get("person_id") != filter_person_id:
                    continue
                if filter_handedness and mask_data.get("handedness") != filter_handedness:
                    continue
                    
                mask_id = mask_data["id"]
                finger_name = finger.name
                person_id = mask_data.get("person_id", "unknown")
                hand = mask_data.get("handedness", "unknown")
                if hasattr(hand, "name"):  # Handle enum values
                    hand = hand.name
                mask_size = f"{mask_data['mask'].sum()} px"
                
                self.masks_tree.insert("", "end", values=(mask_id, finger_name, person_id, hand, mask_size))
    
    def clear_mask_list(self):
        """Clear the mask list in the UI"""
        for item in self.masks_tree.get_children():
            self.masks_tree.delete(item)
    
    def delete_selected_mask(self):
        """Delete the selected mask"""
        selected = self.masks_tree.selection()
        if not selected:
            return
            
        values = self.masks_tree.item(selected[0], "values")
        if not values:
            return
            
        mask_id = int(values[0])
        finger_name = values[1]
        finger_type = FingerType[finger_name]
        
        # Remove from canvas
        self.canvas_controller.canvas.delete(f"mask_{mask_id}_{finger_name}")
        
        # Remove from finger annotations
        self.mask_manager.delete_mask(finger_type, mask_id)
        
        # Clean up mask photo reference to prevent memory leak
        if f"mask_{mask_id}_{finger_name}" in self.canvas_controller._mask_photos:
            del self.canvas_controller._mask_photos[f"mask_{mask_id}_{finger_name}"]
        
        # Update UI
        self.update_mask_list()
    
    def get_frame(self):
        """Get the frame of this component"""
        return self.frame

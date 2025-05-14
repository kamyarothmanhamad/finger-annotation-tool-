import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import logging

from ..core.enums import FingerType, Handedness
from ..core.mask_manager import MaskManager
from ..core.hand_instance import HandInstance
from ..utils.file_manager import FileManager
from ..ui.canvas_controller import CanvasController
from ..ui.mask_list import MaskListView

# Configure logging
logger = logging.getLogger("SimpleMaskAnnotator")

class SimpleMaskAnnotatorApp:
    """Main application class for SimpleMaskAnnotator"""
    
    def __init__(self, root):
        """Initialize the application"""
        self.root = root
        self.root.title("Simple Mask Annotator")
        self.root.geometry("1200x800")
        
        # Create core components
        self.mask_manager = MaskManager()
        self.file_manager = FileManager()
        
        # Hand instance management
        self.hand_instances = []  # List of HandInstance objects
        self.current_hand_instance = HandInstance("person_001", Handedness.RIGHT)
        self.hand_instances.append(self.current_hand_instance)
        
        # Initialize person_id and handedness (kept for backward compatibility)
        self.person_id = "person_001"
        self.handedness = Handedness.RIGHT
        
        # Initialize properties to fix the AttributeError
        self.current_person_id = "person_001"
        self.current_handedness = Handedness.RIGHT
        self.people = {"person_001": {"LEFT": False, "RIGHT": False}}
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top control panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, side=tk.TOP, pady=5)
        
        # Load dataset button
        load_btn = ttk.Button(control_frame, text="Load Dataset", command=self.load_dataset)
        load_btn.pack(side=tk.LEFT, padx=5)
        
        # Navigation controls
        nav_frame = ttk.Frame(control_frame)
        nav_frame.pack(side=tk.LEFT, padx=20)
        
        prev_btn = ttk.Button(nav_frame, text="← Previous", command=self.prev_image)
        prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.image_counter = ttk.Label(nav_frame, text="0/0")
        self.image_counter.pack(side=tk.LEFT, padx=10)
        
        next_btn = ttk.Button(nav_frame, text="Next →", command=self.next_image)
        next_btn.pack(side=tk.LEFT, padx=5)
        
        # Hand Instance panel - NEW
        hand_instance_frame = ttk.LabelFrame(control_frame, text="Hand Instances")
        hand_instance_frame.pack(side=tk.LEFT, padx=20, fill=tk.Y)
        
        # Hand instance listbox
        self.hand_instance_var = tk.StringVar()
        self.hand_instance_listbox = tk.Listbox(hand_instance_frame, 
                                              width=20, height=3,
                                              listvariable=self.hand_instance_var)
        self.hand_instance_listbox.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH)
        self.hand_instance_listbox.bind('<<ListboxSelect>>', self.on_hand_instance_selected)
        
        # Hand instance buttons frame
        hand_instance_btn_frame = ttk.Frame(hand_instance_frame)
        hand_instance_btn_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        # Add hand instance button
        add_hand_btn = ttk.Button(hand_instance_btn_frame, text="Add Hand",
                                command=self.add_hand_instance)
        add_hand_btn.pack(side=tk.TOP, padx=5, pady=2, fill=tk.X)
        
        # Remove hand instance button
        remove_hand_btn = ttk.Button(hand_instance_btn_frame, text="Remove Hand",
                                   command=self.remove_hand_instance)
        remove_hand_btn.pack(side=tk.TOP, padx=5, pady=2, fill=tk.X)
        
        # Person ID and Handedness frame
        person_hand_frame = ttk.LabelFrame(control_frame, text="Subject Info")
        person_hand_frame.pack(side=tk.LEFT, padx=20)
        
        # Person ID controls
        person_frame = ttk.Frame(person_hand_frame)
        person_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        ttk.Label(person_frame, text="Person ID:").pack(side=tk.LEFT, padx=5)
        self.person_id_var = tk.StringVar(value=self.current_person_id)
        self.person_id_combobox = ttk.Combobox(person_frame, textvariable=self.person_id_var, width=15)
        self.person_id_combobox['values'] = list(self.people.keys())
        self.person_id_combobox.pack(side=tk.LEFT, padx=5)
        self.person_id_combobox.bind("<<ComboboxSelected>>", self.update_person_id)
        
        # Add person button
        add_person_btn = ttk.Button(person_frame, text="+", width=2, 
                                    command=self.add_new_person)
        add_person_btn.pack(side=tk.LEFT, padx=2)
        
        # Handedness controls
        hand_frame = ttk.Frame(person_hand_frame)
        hand_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        ttk.Label(hand_frame, text="Hand:").pack(side=tk.LEFT, padx=5)
        self.handedness_var = tk.StringVar(value=self.current_handedness.name)
        
        ttk.Radiobutton(hand_frame, text="Left", variable=self.handedness_var, 
                       value="LEFT", command=self.update_handedness).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(hand_frame, text="Right", variable=self.handedness_var, 
                       value="RIGHT", command=self.update_handedness).pack(side=tk.LEFT, padx=5)
        
        # Finger selection panel
        finger_frame = ttk.LabelFrame(control_frame, text="Finger Selection")
        finger_frame.pack(side=tk.LEFT, padx=20, fill=tk.Y)
        
        self.finger_var = tk.StringVar(value="palm")
        
        # Radio buttons for each finger
        finger_types = [
            ("Thumb", "thumb", FingerType.THUMB),
            ("Index", "index", FingerType.INDEX),
            ("Middle", "middle", FingerType.MIDDLE),
            ("Ring", "ring", FingerType.RING),
            ("Pinky", "pinky", FingerType.PINKY),
            ("Palm", "palm", FingerType.PALM)
        ]
        
        # for label, value, _ in finger_types:
        #     ttk.Radiobutton(finger_frame, text=label, variable=self.finger_var, 
        #                   value=value, command=self.set_current_finger).pack(side=tk.LEFT, padx=5)

        for label, value, _ in finger_types:
            ttk.Radiobutton(finger_frame, text=label, variable=self.finger_var, 
                          value=value, command=self.set_current_finger).pack(side=tk.TOP, pady=2, anchor=tk.W, padx=5)
            
        # Smoothness control
        smoothness_frame = ttk.Frame(control_frame)
        smoothness_frame.pack(side=tk.LEFT, padx=20)
        
        smoothness_label = ttk.Label(smoothness_frame, text="Curve Smoothness:")
        smoothness_label.pack(side=tk.LEFT, padx=5)
        
        self.smoothness_var = tk.DoubleVar(value=0.3)
        smoothness_scale = ttk.Scale(smoothness_frame, from_=0.0, to=1.0, 
                                    variable=self.smoothness_var, length=100)
        smoothness_scale.pack(side=tk.LEFT, padx=5)
        smoothness_scale.bind("<ButtonRelease-1>", self.update_smoothness)
        
        # Opacity control
        opacity_frame = ttk.Frame(control_frame)
        opacity_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(opacity_frame, text="Mask Opacity:").pack(side=tk.LEFT, padx=5)
        self.opacity_var = tk.DoubleVar(value=0.5)
        opacity_scale = ttk.Scale(opacity_frame, from_=0.0, to=1.0, 
                                 variable=self.opacity_var, length=100)
        opacity_scale.pack(side=tk.LEFT, padx=5)
        opacity_scale.bind("<ButtonRelease-1>", self.update_opacity)

        # Add a binary mask option in the control panel
        binary_mask_frame = ttk.Frame(control_frame)
        binary_mask_frame.pack(side=tk.RIGHT, padx=5)
        
        self.binary_mask_var = tk.BooleanVar(value=True)
        binary_mask_check = ttk.Checkbutton(binary_mask_frame, 
                                          text="Save Binary Masks", 
                                          variable=self.binary_mask_var,
                                          command=self.toggle_binary_masks)
        binary_mask_check.pack(side=tk.RIGHT)
        
        # Save button
        save_btn = ttk.Button(control_frame, text="Save Annotations", command=self.save_annotations)
        save_btn.pack(side=tk.RIGHT, padx=5)
        
        # Filter controls
        filter_frame = ttk.LabelFrame(control_frame, text="Filter Display")
        filter_frame.pack(side=tk.LEFT, padx=20)
        
        # Filter by person
        self.filter_person_var = tk.BooleanVar(value=False)
        filter_person_check = ttk.Checkbutton(filter_frame, text="Filter by Person", 
                                             variable=self.filter_person_var, 
                                             command=self.apply_filters)
        filter_person_check.pack(side=tk.TOP, anchor=tk.W, padx=5, pady=2)
        
        # Filter by hand
        self.filter_hand_var = tk.BooleanVar(value=False)
        filter_hand_check = ttk.Checkbutton(filter_frame, text="Filter by Hand", 
                                           variable=self.filter_hand_var, 
                                           command=self.apply_filters)
        filter_hand_check.pack(side=tk.TOP, anchor=tk.W, padx=5, pady=2)
        
        # Filter by hand instance
        self.filter_instance_var = tk.BooleanVar(value=False)
        filter_instance_check = ttk.Checkbutton(filter_frame, text="Filter by Hand Instance", 
                                             variable=self.filter_instance_var, 
                                             command=self.apply_filters)
        filter_instance_check.pack(side=tk.TOP, anchor=tk.W, padx=5, pady=2)
        
        # Canvas for image display and annotation
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.canvas = tk.Canvas(canvas_frame, bg="gray", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initialize canvas controller
        self.canvas_controller = CanvasController(self.canvas, self.mask_manager)

        self.canvas_controller.on_mask_created = self.update_mask_list
        
        # Bind canvas events
        self.canvas.bind("<ButtonPress-1>", self.canvas_controller.handle_click)
        self.canvas.bind("<B1-Motion>", self.canvas_controller.handle_drag)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_controller.handle_release)
        
        # Initialize mask list view
        self.mask_list_view = MaskListView(main_frame, self.mask_manager, self.canvas_controller)
        self.mask_list_view.get_frame().pack(fill=tk.BOTH, side=tk.BOTTOM, expand=False, pady=5)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initialize hand instance list
        self.update_hand_instance_list()
    
    def load_dataset(self):
        """Load a dataset of images"""
        dataset_path = filedialog.askdirectory(title="Select dataset directory")
        if not dataset_path:
            return
            
        success = self.file_manager.load_dataset(dataset_path)
        if not success:
            messagebox.showerror("Error", "No images found in the selected directory")
            return
            
        # Start fresh by clearing everything before loading the first image
        self.mask_manager.clear_masks()
        self.canvas_controller.clear_canvas_masks()
        self.mask_list_view.clear_mask_list()
            
        # Load the first image
        self.load_current_image()
        
        # Update status
        self.update_status(f"Loaded {len(self.file_manager.images)} images")
    def load_current_image(self):
        """Load the current image and its annotations"""
        img_path = self.file_manager.get_current_image_path()
        if not img_path:
            return

        # Remember currently selected hand instance before clearing
        previous_person_id = self.current_person_id if hasattr(self, "current_person_id") else None
        previous_handedness = self.current_handedness if hasattr(self, "current_handedness") else None

        # Clear existing masks and UI elements before loading new image
        self.mask_manager.clear_masks()
        self.canvas_controller.clear_canvas_masks()
        self.mask_list_view.clear_mask_list()
        
        # Store current hand instances temporarily instead of setting to empty list
        # But make sure we don't use these unless explicitly needed for a new image without annotations
        previous_hand_instances = []
        if hasattr(self, "hand_instances"):
            for instance in self.hand_instances:
                previous_hand_instances.append(HandInstance(instance.person_id, instance.handedness))

        # Load the image
        image_data = self.canvas_controller.load_image(img_path)
        if image_data is None:
            messagebox.showerror("Error", f"Failed to load image: {img_path}")
            return
            
        # Update image counter
        total_images = len(self.file_manager.images)
        current_index = self.file_manager.current_image_index + 1
        self.image_counter.config(text=f"{current_index}/{total_images}")
        
        # Load annotations
        self.update_status(f"Loading annotations for {os.path.basename(img_path)}...")
        success, hand_instances = self.file_manager.load_annotations(
            self.mask_manager,
            image_data.width,
            image_data.height
        )
        
        if success:
            # Update hand instances from loaded annotations
            self.hand_instances = hand_instances if hand_instances else [HandInstance()]
            
            # Try to find a matching hand instance from previous selection
            selected_instance = None
            if previous_person_id and previous_handedness:
                for instance in self.hand_instances:
                    if instance.person_id == previous_person_id and instance.handedness == previous_handedness:
                        selected_instance = instance
                        break
            
            # If not found, use the first instance
            if not selected_instance and self.hand_instances:
                selected_instance = self.hand_instances[0]
            
            # Set current hand instance
            if selected_instance:
                self.current_hand_instance = selected_instance
                self.canvas_controller.set_current_hand_instance(self.current_hand_instance)
                
                # Update person_id and handedness for backward compatibility
                self.person_id = self.current_hand_instance.person_id
                self.handedness = self.current_hand_instance.handedness
                self.current_person_id = self.person_id
                self.current_handedness = self.handedness
                
                # Update UI controls to match loaded data
                self.person_id_var.set(self.person_id)
                self.handedness_var.set(self.handedness.name)
                
            # Update people tracking based on loaded masks
            self.update_people_tracking()
                
            # Update UI
            self.update_hand_instance_list()
            self.update_status(f"Loaded annotations for {os.path.basename(img_path)}")
        else:
            # Check if file exists but couldn't be loaded (indicating error)
            ann_dir = self.file_manager.annotations_dir
            base_filename = os.path.splitext(os.path.basename(img_path))[0]
            json_path = os.path.join(ann_dir, f"{base_filename}.json")
            
            if os.path.exists(json_path):
                messagebox.showwarning("Warning", 
                                      f"Found annotations but failed to load them. The file may be corrupted or in an incompatible format.\n\nFile: {json_path}")
                self.update_status(f"Failed to load annotations for {os.path.basename(img_path)}")
            else:
                self.update_status(f"No annotations found for {os.path.basename(img_path)}")
            
            # Restore previous hand instances if no annotations loaded
            if not hand_instances and previous_hand_instances:
                self.hand_instances = previous_hand_instances
                
                # Try to find the previous instance
                if previous_person_id and previous_handedness:
                    for instance in self.hand_instances:
                        if instance.person_id == previous_person_id and instance.handedness == previous_handedness:
                            self.current_hand_instance = instance
                            self.canvas_controller.set_current_hand_instance(self.current_hand_instance)
                            break
            else:
                # Create default hand instance if none found
                default_instance = HandInstance("person_001", Handedness.RIGHT)
                self.hand_instances = [default_instance]
                self.current_hand_instance = default_instance
                self.canvas_controller.set_current_hand_instance(default_instance)
            
            # Make sure people tracking is updated
            self.update_people_tracking()
        
        # Update person combobox values
        self.person_id_combobox['values'] = list(self.people.keys())
        
        # Draw masks
        self.apply_filters()
        
        # Update UI
        self.mask_list_view.update_mask_list(
            self.current_hand_instance.person_id if self.filter_instance_var.get() else None,
            self.current_hand_instance.handedness if self.filter_instance_var.get() else None
        )
    
    def prev_image(self):
        """Go to the previous image"""
        if self.file_manager.current_image_index <= 0:
            return
            
        # Ask to save annotations if there are any
        # If the user cancels, don't navigate
        if not self.prompt_save_annotations():
            return
            
        # Move to previous image
        if self.file_manager.prev_image():
            # Clear any remaining annotations to ensure a clean state
            self.mask_manager.clear_masks()
            self.canvas_controller.clear_canvas_masks()
            self.mask_list_view.clear_mask_list()
            
            # Load the previous image's annotations
            self.load_current_image()
    
    def next_image(self):
        """Go to the next image"""
        if self.file_manager.current_image_index >= len(self.file_manager.images) - 1:
            return
            
        # Ask to save annotations if there are any
        # If the user cancels, don't navigate
        if not self.prompt_save_annotations():
            return
        
        # Move to next image
        if self.file_manager.next_image():
            # Clear any remaining annotations to ensure a clean state
            self.mask_manager.clear_masks()
            self.canvas_controller.clear_canvas_masks()
            self.mask_list_view.clear_mask_list()
            
            # Load the next image's annotations
            self.load_current_image()
    
    def set_current_finger(self):
        """Set the current finger based on radio button selection"""
        finger_map = {
            "thumb": FingerType.THUMB,
            "index": FingerType.INDEX,
            "middle": FingerType.MIDDLE,
            "ring": FingerType.RING,
            "pinky": FingerType.PINKY,
            "palm": FingerType.PALM
        }
        
        finger_type = finger_map[self.finger_var.get()]
        self.canvas_controller.set_current_finger(finger_type)
        self.update_status(f"Selected finger: {finger_type.name}")
    
    def update_smoothness(self, event=None):
        """Update the smoothness parameter"""
        self.canvas_controller.set_smoothness(self.smoothness_var.get())
    
    def update_opacity(self, event=None):
        """Update the opacity parameter"""
        self.canvas_controller.set_opacity(self.opacity_var.get())
    
    def redraw_all_masks(self):
        """Redraw all masks on the canvas"""
        self.canvas_controller.redraw_all_masks()
    
    # def save_annotations(self):
    #     """Save annotations for the current image"""
    #     # Get filtered masks if filters are applied
    #     person_id = self.current_person_id if self.filter_person_var.get() else None
    #     handedness = self.current_handedness if self.filter_hand_var.get() else None
        
    #     success = self.file_manager.save_annotations(
    #         self.mask_manager.finger_annotations,
    #         person_id=self.current_person_id,
    #         handedness=self.current_handedness
    #     )
    #     if success:
    #         self.update_status("Saved annotations")
    #     else:
    #         self.update_status("Failed to save annotations")
    #         messagebox.showerror("Error", "Failed to save annotations")

    def save_annotations(self):
        """Save annotations for the current image"""
        # Get filtered masks if filters are applied
        person_id = self.current_person_id if self.filter_person_var.get() else None
        handedness = self.current_handedness if self.filter_hand_var.get() else None
        
        # Create a HandInstance object from person_id and handedness
        from ..core.hand_instance import HandInstance
        hand_instance = HandInstance(self.current_person_id, self.current_handedness)
        
        success = self.file_manager.save_annotations(
            self.mask_manager.finger_annotations,
            default_hand_instance=hand_instance
        )
        if success:
            self.update_status("Saved annotations")
        else:
            self.update_status("Failed to save annotations")
            messagebox.showerror("Error", "Failed to save annotations")
            
    def prompt_save_annotations(self):
        """Prompt the user to save annotations before moving to another image"""
        has_annotations = False
        
        # Check if any finger has annotations
        for finger in FingerType:
            if self.mask_manager.finger_annotations[finger]["masks"]:
                has_annotations = True
                break
        
        if has_annotations:
            response = messagebox.askyesnocancel(
                "Save Annotations",
                "Do you want to save the annotations for this image?")
            
            if response is None:  # Cancel navigation
                return False
            elif response:  # Yes, save
                # Make sure we're using the correct hand instance when saving
                self.save_annotations()
            else:  # No, discard changes
                # Make sure we fully clear all annotations to avoid propagation
                self.mask_manager.clear_masks()
                self.canvas_controller.clear_canvas_masks()
                
            # Indicate navigation should proceed
            return True
            
        # If no annotations, just proceed
        return True
    
    def toggle_binary_masks(self):
        """Toggle binary mask saving on/off"""
        enabled = self.binary_mask_var.get()
        self.file_manager.set_save_binary_masks(enabled)
        status = "enabled" if enabled else "disabled"
        self.update_status(f"Binary mask saving {status}")
        
    def update_status(self, message):
        """Update the status bar with a message"""
        self.status_bar.config(text=message)
    
    def update_person_id(self, event=None):
        """Update the person ID when the combobox selection changes"""
        self.current_person_id = self.person_id_var.get()
        self.canvas_controller.set_current_person(self.current_person_id)
        
        # If filtering is enabled, apply it
        self.apply_filters()
        
        self.update_status(f"Person ID set to: {self.current_person_id}")
    
    def update_handedness(self):
        """Update handedness when radio buttons change"""
        handedness_str = self.handedness_var.get()
        self.current_handedness = Handedness[handedness_str]
        self.canvas_controller.set_current_handedness(self.current_handedness)
        
        # If filtering is enabled, apply it
        self.apply_filters()
        
        self.update_status(f"Handedness set to: {handedness_str.lower()}")
    
    # def add_new_person(self):
    #     """Add a new person ID"""
    #     from tkinter import simpledialog
        
    #     new_id = simpledialog.askstring("New Person", "Enter new person ID:", 
    #                                    initialvalue=f"person_{len(self.people)+1:03d}")
        
    #     if new_id and new_id not in self.people:
    #         self.people[new_id] = {"LEFT": False, "RIGHT": False}
    #         self.person_id_combobox['values'] = list(self.people.keys())
    #         self.person_id_var.set(new_id)
    #         self.update_person_id()
    #         self.update_status(f"Added new person: {new_id}")


    def add_new_person(self):
        """Add a new person ID"""
        from tkinter import simpledialog
        
        new_id = simpledialog.askstring("New Person", "Enter new person ID:", 
                                       initialvalue=f"person_{len(self.people)+1:03d}")
        
        if new_id and new_id not in self.people:
            self.people[new_id] = {"LEFT": False, "RIGHT": False}
            self.person_id_combobox['values'] = list(self.people.keys())
            self.person_id_var.set(new_id)
            
            # Reset handedness to RIGHT when adding a new person
            self.handedness_var.set("RIGHT")
            self.current_handedness = Handedness.RIGHT
            self.canvas_controller.set_current_handedness(Handedness.RIGHT)
            
            self.update_person_id()
            self.update_status(f"Added new person: {new_id}")
    
    def apply_filters(self):
        """Apply hand instance filter to the displayed masks"""
        # First ensure the canvas is cleared to prevent any mask propagation between images
        self.canvas_controller.clear_canvas_masks()
        
        filter_instance = self.filter_instance_var.get()
        filter_person = self.filter_person_var.get()
        filter_hand = self.filter_hand_var.get()
        
        # Determine which filters to apply
        if filter_instance and self.current_hand_instance:
            # When filtering by instance, use both person ID and handedness
            person_id = self.current_hand_instance.person_id
            handedness = self.current_hand_instance.handedness
        elif filter_person and filter_hand:
            # If filtering by both person and hand separately
            person_id = self.current_person_id
            handedness = self.current_handedness
        elif filter_person:
            # If filtering only by person
            person_id = self.current_person_id
            handedness = None
        elif filter_hand:
            # If filtering only by hand
            person_id = None
            handedness = self.current_handedness
        else:
            # No filtering
            person_id = None
            handedness = None
        
        # Update canvas display with only the masks appropriate to the current image
        self.canvas_controller.redraw_filtered_masks(person_id, handedness)
        
        # Update mask list to show only masks from the current image
        self.mask_list_view.update_mask_list(person_id, handedness)
        
        # Update status message
        if filter_instance and self.current_hand_instance:
            self.update_status(f"Filtering by hand instance: {str(self.current_hand_instance)}")
        elif filter_person and filter_hand:
            self.update_status(f"Filtering by person: {person_id} and hand: {handedness.name}")
        elif filter_person:
            self.update_status(f"Filtering by person: {person_id}")
        elif filter_hand:
            self.update_status(f"Filtering by hand: {handedness.name}")
        else:
            self.update_status("Showing all annotations")
    
    def update_people_tracking(self):
        """Update the people dictionary based on loaded masks"""
        # Clear existing tracking
        self.people = {}
        
        # Get all unique person IDs from masks
        for finger in FingerType:
            for mask_data in self.mask_manager.finger_annotations[finger]["masks"]:
                person_id = mask_data.get("person_id", "person_001")
                handedness = mask_data.get("handedness", Handedness.RIGHT)
                
                # Convert to string for dict key
                hand_str = handedness.name if hasattr(handedness, "name") else str(handedness)
                
                # Add to people tracking
                if person_id not in self.people:
                    self.people[person_id] = {"LEFT": False, "RIGHT": False}
                
                # Mark this hand as present
                if hand_str in ["LEFT", "RIGHT"]:
                    self.people[person_id][hand_str] = True
        
        # If no people were found, add a default person
        if not self.people:
            self.people["person_001"] = {"LEFT": False, "RIGHT": False}
    
    # New methods for hand instance management
    def update_hand_instance_list(self):
        """Update the hand instance listbox with current instances"""
        instances = [str(instance) for instance in self.hand_instances]
        self.hand_instance_var.set(instances)
        
        # Select the current hand instance
        if self.current_hand_instance:
            try:
                # Find by exact object
                idx = self.hand_instances.index(self.current_hand_instance)
                self.hand_instance_listbox.selection_clear(0, tk.END)
                self.hand_instance_listbox.selection_set(idx)
                self.hand_instance_listbox.see(idx)  # Ensure the selected item is visible
            except ValueError:
                # If not found by object identity, try to find by matching person_id and handedness
                for i, instance in enumerate(self.hand_instances):
                    if (instance.person_id == self.current_hand_instance.person_id and 
                        instance.handedness == self.current_hand_instance.handedness):
                        self.hand_instance_listbox.selection_clear(0, tk.END)
                        self.hand_instance_listbox.selection_set(i)
                        self.hand_instance_listbox.see(i)
                        # Update current_hand_instance to point to this instance
                        self.current_hand_instance = instance
                        break
    
    def on_hand_instance_selected(self, event):
        """Handle selection of a hand instance from the listbox"""
        selection = self.hand_instance_listbox.curselection()
        if not selection:
            return
            
        idx = selection[0]
        if idx < 0 or idx >= len(self.hand_instances):
            return
            
        self.current_hand_instance = self.hand_instances[idx]
        
        # Update canvas controller
        self.canvas_controller.set_current_hand_instance(self.current_hand_instance)
        
        # Update person_id and handedness for backward compatibility
        self.person_id = self.current_hand_instance.person_id
        self.handedness = self.current_hand_instance.handedness
        self.current_person_id = self.person_id
        self.current_handedness = self.handedness
        
        # Update UI controls to match selected hand instance
        self.person_id_var.set(self.person_id)
        self.handedness_var.set(self.handedness.name)
        
        # Apply filters if needed
        if self.filter_instance_var.get():
            self.apply_filters()
            
        self.update_status(f"Selected hand: {str(self.current_hand_instance)}")
    
    def add_hand_instance(self):
        """Add a new hand instance"""
        person_id = simpledialog.askstring("New Hand Instance", 
                                         "Enter person ID:",
                                         initialvalue=f"person_{len(self.hand_instances)//2+1:03d}")
        
        if not person_id:
            return
            
        # Show hand selection dialog
        hand_dialog = tk.Toplevel(self.root)
        hand_dialog.title("Select Hand")
        hand_dialog.geometry("250x120")
        hand_dialog.transient(self.root)
        hand_dialog.grab_set()
        hand_dialog.resizable(False, False)
        
        hand_var = tk.StringVar(value="RIGHT")
        
        ttk.Label(hand_dialog, text="Select handedness:").pack(pady=(10, 5))
        
        ttk.Radiobutton(hand_dialog, text="Left Hand", variable=hand_var, 
                      value="LEFT").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(hand_dialog, text="Right Hand", variable=hand_var, 
                      value="RIGHT").pack(anchor=tk.W, padx=20)
        
        def on_confirm():
            nonlocal hand_var
            handedness = Handedness[hand_var.get()]
            new_instance = HandInstance(person_id, handedness)
            
            # Check if this hand instance already exists
            if any(instance.person_id == person_id and instance.handedness == handedness 
                 for instance in self.hand_instances):
                messagebox.showwarning("Duplicate", 
                                     f"Hand instance for {person_id} {handedness.name} already exists.")
                hand_dialog.destroy()
                return
                
            # Add the new hand instance
            self.hand_instances.append(new_instance)
            self.current_hand_instance = new_instance
            self.canvas_controller.set_current_hand_instance(new_instance)
            
            # Update UI
            self.update_hand_instance_list()
            self.update_status(f"Added new hand instance: {str(new_instance)}")
            hand_dialog.destroy()
            
            # Update person_id and handedness for backward compatibility
            self.person_id = person_id
            self.handedness = handedness
        
        ttk.Button(hand_dialog, text="Add", command=on_confirm).pack(pady=10)
        
        # Center the dialog relative to the parent window
        hand_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (hand_dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (hand_dialog.winfo_height() // 2)
        hand_dialog.geometry(f"+{x}+{y}")
        
        self.root.wait_window(hand_dialog)
    
    def remove_hand_instance(self):
        """Remove the selected hand instance"""
        selection = self.hand_instance_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a hand instance to remove")
            return
            
        idx = selection[0]
        if idx < 0 or idx >= len(self.hand_instances):
            return
            
        instance_to_remove = self.hand_instances[idx]
        
        # Confirm deletion
        if messagebox.askyesno("Confirm", 
                             f"Remove hand instance {str(instance_to_remove)}? " 
                             "This will also remove all associated masks."):
            # Remove masks for this hand instance
            self.mask_manager.remove_masks_by_instance(instance_to_remove.person_id, 
                                                    instance_to_remove.handedness)
            
            # Remove the instance
            self.hand_instances.pop(idx)
            
            # If we removed the current instance, select a new one
            if instance_to_remove == self.current_hand_instance:
                if self.hand_instances:
                    self.current_hand_instance = self.hand_instances[0]
                    # Update canvas controller
                    self.canvas_controller.set_current_hand_instance(self.current_hand_instance)
                else:
                    # Create a default instance if none left
                    default_instance = HandInstance("person_001", Handedness.RIGHT)
                    self.hand_instances.append(default_instance)
                    self.current_hand_instance = default_instance
                    self.canvas_controller.set_current_hand_instance(default_instance)
            
            # Update UI
            self.update_hand_instance_list()
            self.redraw_all_masks()
            self.mask_list_view.update_mask_list()
            self.update_status(f"Removed hand instance: {str(instance_to_remove)}")


    def update_mask_list(self):
        """Update the mask list after creating a new mask"""
        # First, ensure the mask list is cleared to prevent any stale data
        self.mask_list_view.clear_mask_list()
        
        # Use current filtering settings
        person_id = None
        handedness = None
        
        if self.filter_instance_var.get() and self.current_hand_instance:
            person_id = self.current_hand_instance.person_id
            handedness = self.current_hand_instance.handedness
        elif self.filter_person_var.get():
            person_id = self.current_person_id
            if self.filter_hand_var.get():
                handedness = self.current_handedness
        elif self.filter_hand_var.get():
            handedness = self.current_handedness
        
        # Update the mask list with only the relevant masks
        self.mask_list_view.update_mask_list(person_id, handedness)
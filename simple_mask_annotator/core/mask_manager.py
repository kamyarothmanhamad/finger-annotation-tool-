import numpy as np
import cv2
from ..core.enums import FingerType, Handedness
from ..core.hand_instance import HandInstance

class MaskManager:
    """Class to manage mask creation and manipulation"""
    
    def __init__(self):
        """Initialize the mask manager"""
        self.finger_annotations = {
            FingerType.THUMB: {"masks": []},
            FingerType.INDEX: {"masks": []},
            FingerType.MIDDLE: {"masks": []},
            FingerType.RING: {"masks": []},
            FingerType.PINKY: {"masks": []},
            FingerType.PALM: {"masks": []}
        }
    
    def create_mask_from_points(self, points, smoothness, image_height, image_width, 
                              finger_type, opacity=0.5, person_id="person_001", 
                              handedness=Handedness.RIGHT):
        """Create a mask from points using smooth curve algorithm"""
        # Create empty mask
        mask = np.zeros((image_height, image_width), dtype=np.uint8)
        
        # Generate smooth curve points
        smooth_points = self.generate_smooth_curve(points, smoothness)
        smooth_points = np.array(smooth_points, dtype=np.int32)
        
        # Fill the polygon
        cv2.fillPoly(mask, [smooth_points], 1)
        
        # Apply additional smoothing to curve mask borders
        mask = self.smooth_mask_borders(mask, kernel_size=3, blur_size=3)
        
        # Add as new mask
        mask_id = len(self.finger_annotations[finger_type]["masks"]) + 1
        mask_data = {
            "id": mask_id,
            "mask": mask,
            "opacity": opacity,
            "finger": finger_type,
            "person_id": person_id,
            "handedness": handedness
        }
        self.finger_annotations[finger_type]["masks"].append(mask_data)
        
        return mask_data
    
    def generate_smooth_curve(self, points, smoothness):
        """Generate points for a smooth curve using Catmull-Rom spline"""
        if len(points) < 2:
            return points
        
        # If we only have 2 points, return them
        if len(points) == 2:
            return points
        
        # For closed curves, add the first point at the end and the last point at the beginning
        if abs(points[0][0] - points[-1][0]) < 10 and abs(points[0][1] - points[-1][1]) < 10:
            # Close the curve by making the first and last points the same
            control_points = points[:-1]  # Remove the last point since it's a duplicate
            control_points.append(control_points[0])  # Add the first point to close the loop
            
            # Add extra control points for a closed curve
            extended_points = [control_points[-2]] + control_points + [control_points[1]]
        else:
            # For an open curve, duplicate the first and last points
            extended_points = [points[0]] + points + [points[-1]]
        
        # Number of segments to generate between each pair of control points
        num_segments = 10
        
        # Generate smooth curve points
        curve_points = []
        for i in range(1, len(extended_points) - 2):
            p0 = np.array(extended_points[i - 1])
            p1 = np.array(extended_points[i])
            p2 = np.array(extended_points[i + 1])
            p3 = np.array(extended_points[i + 2])
            
            # Generate points for this segment
            for t in range(num_segments + 1):
                t_normalized = t / num_segments
                
                # Catmull-Rom spline formula
                t2 = t_normalized * t_normalized
                t3 = t2 * t_normalized
                
                # Adjust tensioning (smoothness)
                s = 1.0 - smoothness
                
                # Calculate position using Catmull-Rom spline
                pos = 0.5 * (
                    (2 * p1) +
                    (-p0 + p2) * s * t_normalized +
                    (2*p0 - 5*p1 + 4*p2 - p3) * s * t2 +
                    (-p0 + 3*p1 - 3*p2 + p3) * s * t3
                )
                
                # Add point to curve
                curve_points.append((int(pos[0]), int(pos[1])))
        
        return curve_points
    
    def smooth_mask_borders(self, mask, kernel_size=5, blur_size=3):
        """
        Apply smoothing operations to mask borders to reduce jagged edges
        
        Args:
            mask (numpy.ndarray): Binary mask (0 and 1 values)
            kernel_size (int): Size of morphological kernel (odd number)
            blur_size (int): Size of Gaussian blur kernel (odd number)
        
        Returns:
            numpy.ndarray: Smoothed binary mask
        """
        # Ensure odd kernel sizes
        kernel_size = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
        blur_size = blur_size if blur_size % 2 == 1 else blur_size + 1
        
        # Create a copy of the mask for processing
        smoothed_mask = mask.copy()
        
        # Convert to proper format for morphological operations (0-255)
        if smoothed_mask.max() == 1:
            smoothed_mask = smoothed_mask.astype(np.uint8) * 255
        
        # Create kernel for morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        
        # Apply opening to remove small artifacts and smooth outer edges
        smoothed_mask = cv2.morphologyEx(smoothed_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Apply closing to fill small holes and smooth inner edges
        smoothed_mask = cv2.morphologyEx(smoothed_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        # Apply Gaussian blur to further smooth edges
        smoothed_mask = cv2.GaussianBlur(smoothed_mask, (blur_size, blur_size), 0)
        
        # Threshold back to binary mask (0 and 1 values)
        _, smoothed_mask = cv2.threshold(smoothed_mask, 127, 1, cv2.THRESH_BINARY)
        
        return smoothed_mask
    
    def delete_mask(self, finger_type, mask_id):
        """Delete a mask by ID and finger type"""
        for i, mask_data in enumerate(self.finger_annotations[finger_type]["masks"]):
            if mask_data["id"] == mask_id:
                self.finger_annotations[finger_type]["masks"].pop(i)
                return True
        return False
    
    def get_all_masks(self):
        """Get all masks across all finger types"""
        all_masks = []
        for finger_type in FingerType:
            for mask_data in self.finger_annotations[finger_type]["masks"]:
                all_masks.append(mask_data)
        return all_masks
    
    def clear_masks(self):
        """Clear all masks"""
        for finger in FingerType:
            # Explicitly delete each mask to ensure there are no references
            if "masks" in self.finger_annotations[finger]:
                for mask in self.finger_annotations[finger]["masks"]:
                    if "mask" in mask:
                        mask["mask"] = None
                        
            # Create a fresh empty list for each finger type
            self.finger_annotations[finger]["masks"] = []
            
        # Force garbage collection to ensure memory is freed
        import gc
        gc.collect()
    
    def get_masks_by_person_and_hand(self, person_id=None, handedness=None):
        """Get masks filtered by person_id and handedness"""
        filtered_masks = []
        for finger_type in FingerType:
            for mask_data in self.finger_annotations[finger_type]["masks"]:
                if person_id and mask_data.get("person_id") != person_id:
                    continue
                if handedness and mask_data.get("handedness") != handedness:
                    continue
                filtered_masks.append(mask_data)
        return filtered_masks
    
    def get_unique_people(self):
        """Get a list of unique person_ids from all masks"""
        person_ids = set()
        for finger_type in FingerType:
            for mask_data in self.finger_annotations[finger_type]["masks"]:
                if "person_id" in mask_data:
                    person_ids.add(mask_data["person_id"])
        return list(person_ids)
    
    def get_masks_by_instance(self, hand_instance):
        """Get masks for a specific hand instance"""
        return self.get_masks_by_person_and_hand(
            hand_instance.person_id, hand_instance.handedness)
    
    def remove_masks_by_instance(self, person_id, handedness):
        """Remove all masks for a specific person_id and handedness"""
        for finger_type in FingerType:
            # Create a new list without the masks to be removed
            self.finger_annotations[finger_type]["masks"] = [
                mask for mask in self.finger_annotations[finger_type]["masks"]
                if not (mask.get("person_id") == person_id and mask.get("handedness") == handedness)
            ]
    
    def get_unique_hand_instances(self):
        """Get list of unique HandInstance objects from all masks"""
        instances = set()
        
        for finger_type in FingerType:
            for mask_data in self.finger_annotations[finger_type]["masks"]:
                person_id = mask_data.get("person_id", "person_001")
                handedness = mask_data.get("handedness", Handedness.RIGHT)
                instances.add(HandInstance(person_id, handedness))
        
        return list(instances)

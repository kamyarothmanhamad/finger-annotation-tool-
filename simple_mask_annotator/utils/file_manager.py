import os
import json
import numpy as np
import cv2
import logging
import base64
import zlib
from ..core.enums import FingerType, Handedness
from ..core.hand_instance import HandInstance

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FileManager")

class FileManager:
    """Class to manage file operations like loading and saving annotations"""
    
    def __init__(self):
        """Initialize the file manager"""
        self.dataset_path = None
        self.annotations_dir = None
        self.images = []
        self.current_image_index = -1
        self.save_binary_masks = True  # Enable binary mask saving by default
    
    def load_dataset(self, dataset_path):
        """
        Load dataset from a directory
        
        Args:
            dataset_path (str): Path to the dataset directory
            
        Returns:
            bool: True if dataset was loaded successfully, False otherwise
        """
        self.dataset_path = dataset_path
        
        # Look for images directory and annotations
        images_dir = os.path.join(self.dataset_path, "images")
        if not os.path.exists(images_dir):
            images_dir = self.dataset_path
            
        # Get all image files
        self.images = []
        for ext in ['.jpg', '.jpeg', '.png']:
            self.images.extend([os.path.join(images_dir, f) for f in os.listdir(images_dir)
                             if f.lower().endswith(ext)])
        
        if not self.images:
            return False
        
        # Create annotation directory if it doesn't exist
        self.annotations_dir = os.path.join(self.dataset_path, "annotations")
        os.makedirs(self.annotations_dir, exist_ok=True)
        
        self.images.sort()
        self.current_image_index = 0
        return True
    
    def get_current_image_path(self):
        """Get the path of the current image"""
        if self.current_image_index >= 0 and self.current_image_index < len(self.images):
            return self.images[self.current_image_index]
        return None
    
    def next_image(self):
        """Go to the next image"""
        if self.current_image_index < len(self.images) - 1:
            # Advance to the next image
            self.current_image_index += 1
            return True
        return False
    
    def prev_image(self):
        """Go to the previous image"""
        if self.current_image_index > 0:
            # Go back to the previous image
            self.current_image_index -= 1
            return True
        return False
    
    def save_annotations(self, finger_annotations, default_hand_instance=None):
        """
        Save annotations for the current image
        
        Args:
            finger_annotations (dict): Dictionary of finger annotations
            default_hand_instance (HandInstance, optional): Default hand instance
            
        Returns:
            bool: True if annotations were saved successfully, False otherwise
        """
        if self.current_image_index < 0 or not self.images:
            return False
        
        # Use default values if no hand instance provided
        if default_hand_instance is None:
            default_hand_instance = HandInstance("person_001", Handedness.UNKNOWN)
            
        img_path = self.images[self.current_image_index]
        img_filename = os.path.basename(img_path)
        base_filename = os.path.splitext(img_filename)[0]
        
        # Get image dimensions
        from PIL import Image
        with Image.open(img_path) as img:
            img_width, img_height = img.size
        
        # Save in COCO format
        json_filename = f"{base_filename}.json"
        json_path = os.path.join(self.annotations_dir, json_filename)
        
        # Create masks directory if we're saving binary masks
        masks_dir = os.path.join(self.annotations_dir, "masks")
        if self.save_binary_masks:
            os.makedirs(masks_dir, exist_ok=True)
        
        # Prepare COCO data structure
        coco_data = {
            "info": {
                "description": "Finger Segmentation Dataset",
                "url": "",
                "version": "1.0",
                "year": 2025,
                "contributor": "",
                "date_created": self._get_current_date()
            },
            "licenses": [
                {
                    "id": 1,
                    "name": "Unknown",
                    "url": ""
                }
            ],
            "images": [
                {
                    "id": 1,
                    "width": img_width,
                    "height": img_height,
                    "file_name": img_filename,
                    "license": 1,
                    "flickr_url": "",
                    "coco_url": "",
                    "date_captured": self._get_current_date()
                }
            ],
            "annotations": [],
            "categories": [
                {"id": 0, "name": "thumb", "supercategory": "finger"},
                {"id": 1, "name": "index", "supercategory": "finger"},
                {"id": 2, "name": "middle", "supercategory": "finger"},
                {"id": 3, "name": "ring", "supercategory": "finger"},
                {"id": 4, "name": "pinky", "supercategory": "finger"},
                {"id": 5, "name": "palm", "supercategory": "finger"}
            ],
            "hand_metadata": {
                "default_person_id": default_hand_instance.person_id,
                "default_handedness": default_hand_instance.handedness.name
            }
        }
        
        # Map finger types to category IDs
        finger_to_category = {
            FingerType.THUMB: 0,
            FingerType.INDEX: 1,
            FingerType.MIDDLE: 2,
            FingerType.RING: 3,
            FingerType.PINKY: 4,
            FingerType.PALM: 5
        }

        # Map category IDs to finger types (for loading)
        category_to_finger = {
            0: FingerType.THUMB,
            1: FingerType.INDEX,
            2: FingerType.MIDDLE,
            3: FingerType.RING,
            4: FingerType.PINKY,
            5: FingerType.PALM
        }
        
        # Convert masks to COCO format
        annotation_id = 1
        
        # Get base filename without extension to use in mask filenames
        img_basename = os.path.splitext(os.path.basename(img_filename))[0]
        
        for finger in FingerType:
            finger_data = finger_annotations[finger]
            
            # Skip fingers with no annotations
            if not finger_data['masks']:
                continue
            
            for mask_data in finger_data['masks']:
                mask = mask_data['mask']
                
                # Get person_id and handedness from mask_data
                mask_person_id = mask_data.get("person_id", default_hand_instance.person_id)
                mask_handedness = mask_data.get("handedness", default_hand_instance.handedness)
                
                # Ensure mask_handedness is a Handedness enum
                if isinstance(mask_handedness, str):
                    try:
                        mask_handedness = Handedness[mask_handedness]
                    except KeyError:
                        mask_handedness = default_hand_instance.handedness
                
                # Convert handedness enum to string for JSON
                mask_handedness_str = mask_handedness.name if hasattr(mask_handedness, "name") else str(mask_handedness)
                
                # Save binary mask as PNG if enabled
                if self.save_binary_masks:
                    try:
                        # Create a filename for this mask that includes the image name
                        mask_filename = f"{img_basename}_{mask_person_id}_{mask_handedness_str}_{finger.name.lower()}_mask_{annotation_id}.png"
                        mask_path = os.path.join(masks_dir, mask_filename)
                        
                        # Convert binary mask to 8-bit for saving (0 or 255)
                        mask_8bit = (mask * 255).astype(np.uint8)
                        cv2.imwrite(mask_path, mask_8bit)
                        
                        # Add mask filename to the annotation for easier loading
                        coco_data.setdefault("mask_files", {}).setdefault(str(annotation_id), mask_filename)
                        logger.debug(f"Saved binary mask to {mask_path}")
                    except Exception as e:
                        logger.warning(f"Failed to save binary mask: {str(e)}")
                
                # Still include RLE format for COCO compatibility
                try:
                    rle = self._mask_to_rle(mask)
                except Exception as e:
                    logger.warning(f"Failed to encode mask to RLE: {str(e)}")
                    rle = ""  # Empty string as fallback
                
                # Calculate bounding box
                bbox = self._mask_to_bbox(mask)
                
                # Calculate area
                area = int(np.sum(mask))
                
                # Add annotation to COCO format
                annotation = {
                    "id": annotation_id,
                    "image_id": 1,
                    "category_id": finger_to_category[finger],
                    "segmentation": {
                        "size": [img_height, img_width],
                        "counts": rle
                    },
                    "area": area,
                    "bbox": bbox,
                    "iscrowd": 0,
                    "mask_file": f"masks/{mask_filename}" if self.save_binary_masks else None,
                    "person_id": mask_person_id,
                    "handedness": mask_handedness_str
                }
                
                coco_data["annotations"].append(annotation)
                annotation_id += 1
        
        try:
            # Save COCO format JSON
            with open(json_path, 'w') as f:
                json.dump(coco_data, f, indent=4)
            
            logger.info(f"Saved annotations to {json_path}" + 
                       (f" with binary masks in {masks_dir}" if self.save_binary_masks else ""))
            return True
        
        except Exception as e:
            logger.error(f"Error saving annotations: {str(e)}")
            return False
    
    def _mask_to_rle(self, mask):
        """
        Convert binary mask to run-length encoding string
        
        Args:
            mask (numpy.ndarray): Binary mask of 0s and 1s
            
        Returns:
            str: RLE encoded string
        """
        import pycocotools.mask as mask_utils
        rle = mask_utils.encode(np.asfortranarray(mask.astype(np.uint8)))
        return rle['counts'].decode('utf-8')
    
    def _mask_to_bbox(self, mask):
        """
        Calculate bounding box from mask
        
        Args:
            mask (numpy.ndarray): Binary mask
            
        Returns:
            list: [x, y, width, height] bounding box
        """
        pos = np.where(mask)
        if len(pos[0]) == 0 or len(pos[1]) == 0:
            return [0, 0, 0, 0]
        
        xmin = np.min(pos[1])
        ymin = np.min(pos[0])
        xmax = np.max(pos[1])
        ymax = np.max(pos[0])
        
        width = xmax - xmin + 1
        height = ymax - ymin + 1
        
        return [int(xmin), int(ymin), int(width), int(height)]
    
    def _get_current_date(self):
        """Get current date in YYYY-MM-DD HH:MM:SS format"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _robust_rle_decode(self, rle_data, expected_height, expected_width):
        """
        Robustly decode RLE data with multiple fallback approaches
        
        Args:
            rle_data (dict): RLE data containing counts and size
            expected_height (int): Expected height of the mask
            expected_width (int): Expected width of the mask
            
        Returns:
            numpy.ndarray: Decoded binary mask or None if decoding fails
        """
        try:
            import pycocotools.mask as mask_utils
            
            # Extract the RLE data
            rle_counts = rle_data.get("counts")
            rle_size = rle_data.get("size", [expected_height, expected_width])
            
            # Debug info about the RLE string
            if isinstance(rle_counts, str):
                logger.debug(f"RLE string length: {len(rle_counts)}, First 20 chars: {rle_counts[:20]}")
            
            # Try standard approach first (handle string vs bytes)
            try:
                if isinstance(rle_counts, str):
                    rle = {'counts': rle_counts.encode('utf-8'), 'size': rle_size}
                else:
                    rle = {'counts': rle_counts, 'size': rle_size}
                
                return mask_utils.decode(rle).astype(np.uint8)
            except Exception as e:
                logger.warning(f"Standard RLE decode failed: {str(e)}")
                
            # Approach 2: Try different encodings for the RLE string
            encodings = ['utf-8', 'latin1', 'ascii']
            for encoding in encodings:
                try:
                    if isinstance(rle_counts, str):
                        rle = {'counts': rle_counts.encode(encoding), 'size': rle_size}
                        mask = mask_utils.decode(rle).astype(np.uint8)
                        logger.debug(f"RLE decoded successfully with {encoding} encoding")
                        return mask
                except Exception:
                    pass
            
            # Approach 3: Try to fix potentially corrupted RLE strings
            if isinstance(rle_counts, str):
                # Some common corruption patterns and fixes
                fixed_rle = rle_counts.replace('\\', '')  # Remove escape characters
                try:
                    rle = {'counts': fixed_rle.encode('utf-8'), 'size': rle_size}
                    return mask_utils.decode(rle).astype(np.uint8)
                except Exception:
                    logger.warning("Failed to fix corrupted RLE string")
                
            # Approach 4: Create empty mask as a last resort
            logger.warning(f"All RLE decode attempts failed, creating empty mask of size {expected_height}x{expected_width}")
            return np.zeros((expected_height, expected_width), dtype=np.uint8)
            
        except Exception as e:
            logger.error(f"Critical error in RLE decoding: {str(e)}")
            return None
    
    def _mask_from_polygon(self, polygons, height, width):
        """
        Create a binary mask from polygon segmentation
        
        Args:
            polygons (list): List of polygon points
            height (int): Height of the mask
            width (int): Width of the mask
            
        Returns:
            numpy.ndarray: Binary mask
        """
        mask = np.zeros((height, width), dtype=np.uint8)
        
        for polygon in polygons:
            # Skip invalid polygons
            if len(polygon) < 6:  # Minimum 3 points (x,y) pairs
                continue
                
            # Reshape polygon to [[x1,y1], [x2,y2], ...] format
            try:
                poly = np.array(polygon).reshape(-1, 2).astype(np.int32)
                cv2.fillPoly(mask, [poly], 1)
            except Exception as e:
                logger.warning(f"Failed to create polygon: {str(e)}")
                
        return mask
    
    def load_annotations(self, mask_manager, image_width, image_height):
        """
        Load annotations for the current image
        
        Args:
            mask_manager (MaskManager): The mask manager to update with loaded masks
            image_width (int): Width of the current image
            image_height (int): Height of the current image
            
        Returns:
            bool: True if annotations were loaded successfully, False otherwise
            list: List of HandInstance objects found in the annotations
        """
        # Map category IDs to finger types
        category_to_finger = {
            0: FingerType.THUMB,
            1: FingerType.INDEX,
            2: FingerType.MIDDLE,
            3: FingerType.RING,
            4: FingerType.PINKY,
            5: FingerType.PALM
        }
        if self.current_image_index < 0 or not self.images:
            logger.warning("No current image selected")
            return False, []
            
        img_path = self.images[self.current_image_index]
        img_filename = os.path.basename(img_path)
        base_filename = os.path.splitext(img_filename)[0]
        
        # Check for COCO format annotations in the annotations directory
        json_filename = f"{base_filename}.json"
        json_path = os.path.join(self.annotations_dir, json_filename)
        
        # If not found in annotations directory, check original location
        if not os.path.exists(json_path):
            possible_json_path = os.path.join(os.path.dirname(img_path), json_filename)
            if os.path.exists(possible_json_path):
                json_path = possible_json_path
                logger.info(f"Found annotations in original location: {json_path}")
            else:
                # Also try with _annotations suffix (used in older versions)
                old_json_filename = f"{base_filename}_annotations.json"
                old_json_path = os.path.join(self.annotations_dir, old_json_filename)
                if os.path.exists(old_json_path):
                    json_path = old_json_path
                    logger.info(f"Found annotations with old filename format: {json_path}")
                else:
                    old_possible_json_path = os.path.join(os.path.dirname(img_path), old_json_filename)
                    if os.path.exists(old_possible_json_path):
                        json_path = old_possible_json_path
                        logger.info(f"Found annotations with old filename format in original location: {json_path}")
                    else:
                        logger.info(f"No annotations found for {img_filename}")
                        return False, []
        else:
            logger.info(f"Found annotations in annotations directory: {json_path}")
        
        # Locate masks directory - check multiple possible locations
        possible_masks_dirs = [
            os.path.join(self.annotations_dir, "masks"),  # Standard location
            os.path.join(os.path.dirname(img_path), "masks"),  # Next to images
            os.path.join(os.path.dirname(json_path), "masks"),  # Next to JSON
            os.path.join(self.dataset_path, "masks"),  # At dataset root
        ]
        
        masks_dir = None
        for dir_path in possible_masks_dirs:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                masks_dir = dir_path
                logger.debug(f"Found masks directory: {masks_dir}")
                break
        
        if not masks_dir:
            logger.debug("No dedicated masks directory found")
        
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                logger.debug(f"Successfully loaded JSON from {json_path}")
            
            # Reset finger annotations
            mask_manager.clear_masks()
            
            # Extract hand instances from the loaded masks
            hand_instances = []
            
            # Process each annotation - ensure it's a list
            annotations = data.get("annotations", [])
            if not isinstance(annotations, list):
                annotations = [annotations]
                logger.debug("Converted annotations to list")
                
            # Get mask file mapping if available
            mask_files = data.get("mask_files", {})
            
            # Track successfully loaded masks
            successful_masks = 0
            
            for annotation in annotations:
                try:
                    # Validate required fields
                    if "category_id" not in annotation:
                        logger.warning("Annotation missing category_id, skipping")
                        continue
                        
                    cat_id = annotation["category_id"]
                    if cat_id not in category_to_finger:
                        logger.warning(f"Unknown category ID: {cat_id}, skipping")
                        continue
                        
                    finger_type = category_to_finger[cat_id]
                    logger.debug(f"Processing annotation for finger type: {finger_type.name}")
                    
                    # Get the annotation ID and image ID for debugging
                    ann_id = annotation.get("id", "unknown")
                    
                    # Create a mask - first try loading from binary file
                    mask = None
                    
                    # Try to load from annotation's mask_file field
                    if mask is None and "mask_file" in annotation and annotation["mask_file"]:
                        # Try both absolute and relative paths
                        mask_path = annotation["mask_file"]
                        if not os.path.isabs(mask_path):
                            # Try relative to annotations_dir
                            mask_path = os.path.join(self.annotations_dir, mask_path)
                        
                        if not os.path.exists(mask_path) and masks_dir:
                            # Try with just the filename in masks_dir
                            mask_filename = os.path.basename(annotation["mask_file"])
                            mask_path = os.path.join(masks_dir, mask_filename)
                        
                        if os.path.exists(mask_path):
                            try:
                                logger.debug(f"Loading mask from path specified in annotation: {mask_path}")
                                mask_img = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
                                if mask_img is not None:
                                    # Convert from 255 back to 1 for binary mask
                                    _, mask = cv2.threshold(mask_img, 127, 1, cv2.THRESH_BINARY)
                            except Exception as e:
                                logger.warning(f"Failed to load mask from {mask_path}: {str(e)}")
                                mask = None
                    
                    # Try to load from mask_files dictionary
                    if mask is None and str(ann_id) in mask_files:
                        mask_filename = mask_files[str(ann_id)]
                        if masks_dir:
                            mask_path = os.path.join(masks_dir, mask_filename)
                            if os.path.exists(mask_path):
                                try:
                                    logger.debug(f"Loading mask from mask_files mapping: {mask_path}")
                                    mask_img = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
                                    if mask_img is not None:
                                        _, mask = cv2.threshold(mask_img, 127, 1, cv2.THRESH_BINARY)
                                except Exception as e:
                                    logger.warning(f"Failed to load mask from {mask_path}: {str(e)}")
                                    mask = None
                    
                    # Try multiple mask filename patterns
                    if mask is None:
                        # Get person_id and handedness for more specific filename patterns
                        person_id = annotation.get("person_id", "person_001")
                        handedness_str = annotation.get("handedness", "UNKNOWN")
                        
                        possible_filenames = [
                            # Try patterns with person ID and handedness
                            f"{person_id}_{handedness_str}_{finger_type.name.lower()}_mask_{ann_id}.png",
                            f"{person_id}_{handedness_str}_{finger_type.name.lower()}.png",
                            # Try patterns with base filename
                            f"{base_filename}_{finger_type.name.lower()}_mask_{ann_id}.png",
                            f"{base_filename}_{finger_type.name.lower()}_mask.png",
                            f"{base_filename}_mask_{ann_id}.png",
                            # Generic patterns
                            f"{finger_type.name.lower()}_mask_{ann_id}.png",
                            f"{finger_type.name.lower()}_{ann_id}.png",

                            f"{base_filename}_{person_id}_{handedness_str}_{finger_type.name.lower()}_mask_{ann_id}.png",
                            f"{base_filename}_{person_id}_{handedness_str}_{finger_type.name.lower()}.png"
                        ]
                        
                        if masks_dir:
                            for filename in possible_filenames:
                                mask_path = os.path.join(masks_dir, filename)
                                if os.path.exists(mask_path):
                                    try:
                                        logger.debug(f"Loading mask from pattern match: {mask_path}")
                                        mask_img = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
                                        if mask_img is not None:
                                            _, mask = cv2.threshold(mask_img, 127, 1, cv2.THRESH_BINARY)
                                            break  # Found a valid mask
                                    except Exception:
                                        continue  # Try next pattern
                    
                    # If we still don't have a mask, try RLE decoding as last resort
                    if mask is None and "segmentation" in annotation:
                        segmentation = annotation["segmentation"]
                        try:
                            import pycocotools.mask as mask_utils
                            if isinstance(segmentation, dict) and "counts" in segmentation and "size" in segmentation:
                                # Try robust RLE decode with fallbacks
                                mask = self._robust_rle_decode(segmentation, image_height, image_width)
                                if mask is not None:
                                    logger.debug("Succeeded loading mask from RLE data")
                        except Exception as e:
                            logger.warning(f"Failed to decode RLE: {str(e)}")
                            # Create fallback empty mask
                            mask = np.zeros((image_height, image_width), dtype=np.uint8)
                            logger.warning("Created empty mask as fallback")
                    
                    # If we still don't have a mask, create an empty one
                    if mask is None:
                        logger.warning(f"No valid mask found for {finger_type.name}, creating empty mask")
                        mask = np.zeros((image_height, image_width), dtype=np.uint8)
                    
                    # Validate mask dimensions and resize if necessary
                    if mask.shape[0] != image_height or mask.shape[1] != image_width:
                        logger.debug(f"Resizing mask from {mask.shape} to {image_height}x{image_width}")
                        try:
                            mask = cv2.resize(mask, (image_width, image_height), 
                                              interpolation=cv2.INTER_NEAREST)
                        except Exception as resize_error:
                            logger.error(f"Failed to resize mask: {str(resize_error)}")
                            continue
                    
                    # Check if mask is empty
                    if np.sum(mask) == 0:
                        logger.warning(f"Mask for {finger_type.name} is empty (no pixels set)")
                    
                    # Add mask to the manager
                    mask_id = len(mask_manager.finger_annotations[finger_type]["masks"]) + 1
                    opacity = annotation.get("opacity", 0.5)  # Use provided opacity or default
                    
                    # Get hand instance info
                    person_id = annotation.get("person_id", "person_001")
                    handedness_str = annotation.get("handedness", "UNKNOWN")
                    try:
                        handedness = Handedness[handedness_str]
                    except (KeyError, ValueError):
                        handedness = Handedness.UNKNOWN
                    
                    # Create mask object
                    mask_obj = {
                        "id": mask_id,
                        "mask": mask,
                        "opacity": opacity,
                        "finger": finger_type,
                        "person_id": person_id,
                        "handedness": handedness
                    }
                    
                    # Add to mask manager
                    mask_manager.finger_annotations[finger_type]["masks"].append(mask_obj)
                    successful_masks += 1
                    
                    # Add hand instance if not already in the list
                    hand_instance = HandInstance(person_id, handedness)
                    if hand_instance not in hand_instances:
                        hand_instances.append(hand_instance)
                    
                except Exception as e:
                    logger.error(f"Error processing annotation {ann_id}: {str(e)}")
                    continue
            
            # Look for hand_metadata in the JSON (backup approach)
            if "hand_metadata" in data and not hand_instances:
                try:
                    metadata = data["hand_metadata"]
                    person_id = metadata.get("default_person_id", "person_001")
                    handedness_str = metadata.get("default_handedness", "RIGHT")
                    handedness = Handedness[handedness_str]
                    hand_instance = HandInstance(person_id, handedness)
                    hand_instances.append(hand_instance)
                    logger.info(f"Added hand instance from metadata: {person_id} {handedness_str}")
                except Exception as e:
                    logger.error(f"Failed to process hand_metadata: {str(e)}")
            
            logger.info(f"Successfully loaded {successful_masks} masks out of {len(annotations)} annotations")
            logger.info(f"Found {len(hand_instances)} hand instances in the annotations")
            return successful_masks > 0, hand_instances
                
        except json.JSONDecodeError as json_err:
            logger.error(f"Invalid JSON in annotation file: {str(json_err)}")
            return False, []
        except Exception as e:
            logger.error(f"Error loading annotations: {str(e)}")
            return False, []
    
    def set_save_binary_masks(self, enabled=True):
        """
        Enable or disable saving binary mask files alongside COCO annotations
        
        Args:
            enabled (bool): Whether to save binary masks
        """
        self.save_binary_masks = enabled
        logger.info(f"Binary mask saving {'enabled' if enabled else 'disabled'}")

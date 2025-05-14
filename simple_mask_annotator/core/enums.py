from enum import Enum, auto

class FingerType(Enum):
    """Enum representing different finger types for annotations"""
    THUMB = auto()
    INDEX = auto()
    MIDDLE = auto()
    RING = auto()
    PINKY = auto()
    PALM = auto()  # For annotations that don't belong to specific fingers

class Handedness(Enum):
    """Enum representing hand laterality (left/right)"""
    LEFT = auto()
    RIGHT = auto()
    UNKNOWN = auto()  # Default for unspecified handedness

from .enums import Handedness

class HandInstance:
    """Class representing a hand instance (combination of person_id and handedness)"""
    
    def __init__(self, person_id="person_001", handedness=Handedness.RIGHT):
        """Initialize a hand instance"""
        self.person_id = person_id
        self.handedness = handedness
    
    def __str__(self):
        """String representation of hand instance"""
        return f"{self.person_id} {self.handedness.name}"
    
    def __eq__(self, other):
        """Check if two hand instances are equal"""
        if not isinstance(other, HandInstance):
            return False
        return self.person_id == other.person_id and self.handedness == other.handedness
    
    def __hash__(self):
        """Hash function for hand instance to use in sets/dicts"""
        return hash((self.person_id, self.handedness))
    
    @staticmethod
    def from_string(instance_str):
        """Create a hand instance from string representation"""
        try:
            parts = instance_str.split()
            if len(parts) >= 2:
                # Last part is handedness, everything before is person_id
                handedness_str = parts[-1]
                person_id = " ".join(parts[:-1])
                return HandInstance(person_id, Handedness[handedness_str])
            return None
        except (ValueError, KeyError):
            return None

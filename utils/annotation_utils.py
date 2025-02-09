from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import json

@dataclass
class BoundingBox:
    x: int
    y: int
    width: int
    height: int
    category: str
    location: str
    body_map_id: str
    created_by: str
    created_at: str
    last_modified_by: Optional[str] = None
    last_modified_at: Optional[str] = None

class AnnotationManager:
    def __init__(self):
        self.annotations: Dict[str, List[BoundingBox]] = {}  # image_id -> list of annotations
        self.current_image_id: Optional[str] = None

    def add_annotation(self, image_id: str, box: BoundingBox) -> bool:
        """
        Add an annotation for an image
        Args:
            image_id: ID of the image
            box: BoundingBox object with annotation data
        Returns:
            bool: Success status
        """
        try:
            if image_id not in self.annotations:
                self.annotations[image_id] = []
            self.annotations[image_id].append(box)
            return True
        except Exception as e:
            print(f"Error adding annotation: {str(e)}")
            return False

    def remove_annotation(self, image_id: str, index: int) -> bool:
        """
        Remove an annotation by index
        Args:
            image_id: ID of the image
            index: Index of annotation to remove
        Returns:
            bool: Success status
        """
        try:
            if image_id in self.annotations and 0 <= index < len(self.annotations[image_id]):
                self.annotations[image_id].pop(index)
                return True
            return False
        except Exception as e:
            print(f"Error removing annotation: {str(e)}")
            return False

    def get_annotations(self, image_id: str) -> List[BoundingBox]:
        """Get all annotations for an image"""
        return self.annotations.get(image_id, [])

    def clear_annotations(self, image_id: str):
        """Clear all annotations for an image"""
        if image_id in self.annotations:
            self.annotations[image_id] = []

    def save_annotations(self, file_path: str):
        """
        Save annotations to JSON file
        Args:
            file_path: Path to save the JSON file
        """
        try:
            annotations_dict = {}
            for image_id, boxes in self.annotations.items():
                annotations_dict[image_id] = [
                    {
                        'x': box.x,
                        'y': box.y,
                        'width': box.width,
                        'height': box.height,
                        'category': box.category,
                        'location': box.location,
                        'body_map_id': box.body_map_id,
                        'created_by': box.created_by,
                        'created_at': box.created_at,
                        'last_modified_by': box.last_modified_by,
                        'last_modified_at': box.last_modified_at
                    }
                    for box in boxes
                ]
            
            with open(file_path, 'w') as f:
                json.dump(annotations_dict, f, indent=4)
                
        except Exception as e:
            print(f"Error saving annotations: {str(e)}")
            raise

    def load_annotations(self, file_path: str):
        """
        Load annotations from JSON file
        Args:
            file_path: Path to the JSON file
        """
        try:
            with open(file_path, 'r') as f:
                annotations_dict = json.load(f)
            
            self.annotations = {}
            for image_id, boxes in annotations_dict.items():
                self.annotations[image_id] = [
                    BoundingBox(
                        x=box['x'],
                        y=box['y'],
                        width=box['width'],
                        height=box['height'],
                        category=box['category'],
                        location=box['location'],
                        body_map_id=box['body_map_id'],
                        created_by=box['created_by'],
                        created_at=box['created_at'],
                        last_modified_by=box.get('last_modified_by'),
                        last_modified_at=box.get('last_modified_at')
                    )
                    for box in boxes
                ]
                
        except Exception as e:
            print(f"Error loading annotations: {str(e)}")
            raise

    def export_to_csv(self, file_path: str):
        """
        Export annotations to CSV format
        Args:
            file_path: Path to save the CSV file
        """
        try:
            import csv
            
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'image_id', 'x', 'y', 'width', 'height',
                    'category', 'location', 'body_map_id',
                    'created_by', 'created_at',
                    'last_modified_by', 'last_modified_at'
                ])
                
                for image_id, boxes in self.annotations.items():
                    for box in boxes:
                        writer.writerow([
                            image_id,
                            box.x,
                            box.y,
                            box.width,
                            box.height,
                            box.category,
                            box.location,
                            box.body_map_id,
                            box.created_by,
                            box.created_at,
                            box.last_modified_by or '',
                            box.last_modified_at or ''
                        ])
                        
        except Exception as e:
            print(f"Error exporting to CSV: {str(e)}")
            raise

    def validate_box(self, box: BoundingBox) -> tuple[bool, str]:
        """
        Validate annotation data
        Returns:
            tuple: (is_valid, error_message)
        """
        if not box.category:
            return False, "Category is required"
        if not box.location:
            return False, "Location is required"
        if box.width <= 0 or box.height <= 0:
            return False, "Invalid box dimensions"
        return True, ""
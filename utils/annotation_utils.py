# utils/annotation_utils.py
from dataclasses import dataclass
from typing import List, Dict, Optional
from PyQt5.QtCore import QRect
import json

@dataclass
class BoundingBox:
    x: int
    y: int
    width: int
    height: int
    category: str
    body_location: str
    assessment_id: str

class AnnotationManager:
    def __init__(self):
        self.annotations: Dict[str, List[BoundingBox]] = {}  # image_id -> list of annotations

    def add_annotation(self, image_id: str, box: BoundingBox):
        """Add an annotation for an image"""
        if image_id not in self.annotations:
            self.annotations[image_id] = []
        self.annotations[image_id].append(box)

    def remove_annotation(self, image_id: str, index: int):
        """Remove an annotation by index"""
        if image_id in self.annotations and 0 <= index < len(self.annotations[image_id]):
            self.annotations[image_id].pop(index)

    def get_annotations(self, image_id: str) -> List[BoundingBox]:
        """Get all annotations for an image"""
        return self.annotations.get(image_id, [])

    def clear_annotations(self, image_id: str):
        """Clear all annotations for an image"""
        if image_id in self.annotations:
            self.annotations[image_id] = []

    def save_annotations(self, file_path: str):
        """Save annotations to JSON file"""
        annotations_dict = {}
        for image_id, boxes in self.annotations.items():
            annotations_dict[image_id] = [
                {
                    'x': box.x,
                    'y': box.y,
                    'width': box.width,
                    'height': box.height,
                    'category': box.category,
                    'body_location': box.body_location,
                    'assessment_id': box.assessment_id
                }
                for box in boxes
            ]
        
        with open(file_path, 'w') as f:
            json.dump(annotations_dict, f, indent=4)

    def load_annotations(self, file_path: str):
        """Load annotations from JSON file"""
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
                    body_location=box['body_location'],
                    assessment_id=box['assessment_id']
                )
                for box in boxes
            ]

    def export_to_csv(self, file_path: str):
        """Export annotations to CSV format"""
        import csv
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'assessment_id', 'x', 'y', 'width', 'height', 
                           'category', 'body_location'])
            
            for image_id, boxes in self.annotations.items():
                for box in boxes:
                    writer.writerow([
                        image_id,
                        box.assessment_id,
                        box.x,
                        box.y,
                        box.width,
                        box.height,
                        box.category,
                        box.body_location
                    ])

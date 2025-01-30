# gui/annotation_widget.py
from PyQt5.QtWidgets import (QDialog,QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QComboBox, QGroupBox, QScrollArea,
                           QMessageBox, QRubberBand, QLineEdit, QFileDialog,
                           QFrame)
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPixmap
from database.databricks_connecter import DatabricksConnector
from gui.body_map_dialog import BodyMapDialog
from config import Config
from utils.image_utils import ImageHandler
from utils.annotation_utils import AnnotationManager, BoundingBox
import json
import os

class AnnotationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabricksConnector()
        self.image_handler = ImageHandler()
        self.annotation_manager = AnnotationManager()
        self.current_image_id = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Top info panel
        info_panel = QGroupBox("Wound Information")
        info_layout = QHBoxLayout()
        
        # Wound Type from Databricks
        wound_type_layout = QVBoxLayout()
        wound_type_label = QLabel("Databricks Wound Type:")
        self.wound_type_display = QLabel("Not loaded")
        self.wound_type_display.setStyleSheet("font-weight: bold;")
        wound_type_layout.addWidget(wound_type_label)
        wound_type_layout.addWidget(self.wound_type_display)
        info_layout.addLayout(wound_type_layout)

        # Body Location from Databricks
        body_location_layout = QVBoxLayout()
        body_location_label = QLabel("Databricks Body Location:")
        self.body_location_display = QLabel("Not loaded")
        self.body_location_display.setStyleSheet("color: #0000FF; font-weight: bold;")  # Blue color
        body_location_layout.addWidget(body_location_label)
        body_location_layout.addWidget(self.body_location_display)
        info_layout.addLayout(body_location_layout)
        
        # Body Map ID input
        body_map_layout = QVBoxLayout()
        body_map_label = QLabel("Body Map ID:")
        self.body_map_input = QLineEdit()
        self.body_map_input.setPlaceholderText("Enter Body Map ID")
        view_map_btn = QPushButton("View Map")
        view_map_btn.clicked.connect(self.show_body_map)
        body_map_layout.addWidget(body_map_label)
        body_map_layout.addWidget(self.body_map_input)
        body_map_layout.addWidget(view_map_btn)
        info_layout.addLayout(body_map_layout)
        
      
        
        info_panel.setLayout(info_layout)
        layout.addWidget(info_panel)
        
        # Scroll area for image display
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Image display area
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        scroll_area.setWidget(self.image_label)
        layout.addWidget(scroll_area)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Wound category selection
        category_group = QGroupBox("Wound Category")
        category_layout = QVBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.addItems(Config.ETIOLOGY_OPTIONS)
        category_layout.addWidget(self.category_combo)
        category_group.setLayout(category_layout)
        controls_layout.addWidget(category_group)
        
        # Body location selection
        location_group = QGroupBox("Body Location")
        location_layout = QVBoxLayout()
        self.location_combo = QComboBox()
        self.location_combo.addItems(Config.BODY_LOCATIONS)
        location_layout.addWidget(self.location_combo)
        location_group.setLayout(location_layout)
        controls_layout.addWidget(location_group)
        
        layout.addLayout(controls_layout)
        
        # Annotation controls
        annotation_controls = QHBoxLayout()
        
        # Undo button
        self.undo_btn = QPushButton("Undo Last Box")
        self.undo_btn.clicked.connect(self.undo_last_box)
        self.undo_btn.setEnabled(False)
        annotation_controls.addWidget(self.undo_btn)
        
        # Save buttons
        save_json_btn = QPushButton("Save as JSON")
        save_json_btn.clicked.connect(self.save_annotations_json)
        annotation_controls.addWidget(save_json_btn)
        
        save_csv_btn = QPushButton("Save as CSV")
        save_csv_btn.clicked.connect(self.save_annotations_csv)
        annotation_controls.addWidget(save_csv_btn)
        
        layout.addLayout(annotation_controls)
        
        # Status bar
        self.status_label = QLabel()
        self.status_label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        layout.addWidget(self.status_label)
        
        # Annotation controls
        self.drawing = False
        self.start_point = None
        self.current_box = None
        self.boxes = []
        
    def load_image(self, image_id, binary_data):
            """
            Load and display image data
            """
            try:
                # Clear existing annotations when loading new image
                self.clearAnnotations()
                
                self.current_image_id = image_id
                # Extract assessment ID from image ID and clean it
                # Remove any non-numeric characters to get clean integer ID
                assessment_id = ''.join(filter(str.isdigit, image_id.split('_')[0]))
                print(f"Extracted assessment ID: {assessment_id}")  # Debug print
                
                # Get wound info from Databricks
                wound_info = self.db.get_wound_assessment(assessment_id)
                print(f"Received wound info from Databricks: {wound_info}")  # Detailed debug print
                
                # Decode and display image using new method
                pixmap = self.image_handler.decode_image_content(binary_data)
                if pixmap:
                    # Resize if necessary while maintaining aspect ratio
                    pixmap = self.image_handler.resize_pixmap(pixmap)
                    self.image_label.setPixmap(pixmap)
                    
                    # Update UI with wound info
                    if wound_info:
                        print(f"Updating UI with wound type: {wound_info.wound_type}")  # Debug print
                        print(f"Updating UI with body location: {wound_info.body_location}")  # Debug print
                        
                        # Update wound type
                        self.wound_type_display.setText(str(wound_info.wound_type) if wound_info.wound_type else "Not loaded")
                        if wound_info.wound_type:
                            self.category_combo.setCurrentText(wound_info.wound_type)
                        
                        # Update body location
                        body_location = str(wound_info.body_location) if wound_info.body_location else "Not loaded"
                        print(f"Setting body location display to: {body_location}")  # Debug print
                        self.body_location_display.setText(body_location)
                        if wound_info.body_location:
                            try:
                                self.location_combo.setCurrentText(wound_info.body_location)
                            except Exception as e:
                                print(f"Error setting location combo: {str(e)}")
                    else:
                        print(f"No wound info found for ID: {assessment_id}")  # Debug print
                        self.wound_type_display.setText("Not loaded")
                        self.body_location_display.setText("Not loaded")
                        QMessageBox.warning(self, "Warning", f"No wound information found for assessment ID: {assessment_id}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to decode image")
            except ValueError as ve:
                print(f"Error converting assessment ID: {str(ve)}")  # Debug print
                QMessageBox.warning(self, "Error", f"Invalid assessment ID format: {image_id}")
            except Exception as e:
                print(f"Error in load_image: {str(e)}")  # Debug print
                QMessageBox.warning(self, "Error", f"Failed to load image: {str(e)}")

    def clearAnnotations(self):
        """Clear all annotations and reset displays"""
        for box in self.boxes:
            if 'rubber_band' in box:
                box['rubber_band'].hide()
                box['rubber_band'].deleteLater()
        self.boxes = []
        self.undo_btn.setEnabled(False)
        self.status_label.setText("Cleared all annotations")
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = event.pos()
            
    def mouseMoveEvent(self, event):
        if self.drawing:
            if self.current_box:
                self.current_box.hide()
            self.current_box = QRubberBand(QRubberBand.Rectangle, self)
            self.current_box.setGeometry(QRect(self.start_point, event.pos()).normalized())
            self.current_box.show()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            if self.current_box:
                box_geometry = self.current_box.geometry()
                # Create a permanent QRubberBand for this box
                permanent_box = QRubberBand(QRubberBand.Rectangle, self)
                permanent_box.setGeometry(box_geometry)
                permanent_box.show()
                
                self.boxes.append({
                    'box': box_geometry,
                    'rubber_band': permanent_box,  # Store the QRubberBand widget
                    'category': self.category_combo.currentText(),
                    'location': self.location_combo.currentText(),
                    'body_map_id': self.body_map_input.text()
                })
                
                self.current_box.hide()
                self.current_box = None
                self.undo_btn.setEnabled(True)
                self.status_label.setText(f"Added box: {box_geometry.x()}, {box_geometry.y()}, {box_geometry.width()}, {box_geometry.height()}")
    
    def undo_last_box(self):
        """Remove the last drawn box"""
        if self.boxes:
            last_box = self.boxes.pop()
            # Hide and delete the QRubberBand widget
            if 'rubber_band' in last_box:
                last_box['rubber_band'].hide()
                last_box['rubber_band'].deleteLater()
            
            if not self.boxes:
                self.undo_btn.setEnabled(False)
            self.status_label.setText("Undid last box")
            
    def clearAnnotations(self):
        """Clear all annotations"""
        for box in self.boxes:
            if 'rubber_band' in box:
                box['rubber_band'].hide()
                box['rubber_band'].deleteLater()
        self.boxes = []
        self.undo_btn.setEnabled(False)
        self.status_label.setText("Cleared all annotations")
            
    def save_annotations_json(self):
        """Save annotations to JSON file"""
        if not self.current_image_id or not self.boxes:
            QMessageBox.warning(self, "Warning", "No annotations to save")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Annotations", "", "JSON Files (*.json)"
        )
        
        if file_path:
            annotations = {
                'image_id': self.current_image_id,
                'boxes': [{
                    'x': box['box'].x(),
                    'y': box['box'].y(),
                    'width': box['box'].width(),
                    'height': box['box'].height(),
                    'category': box['category'],
                    'location': box['location'],
                    'body_map_id': box['body_map_id']
                } for box in self.boxes]
            }
            
            try:
                with open(file_path, 'w') as f:
                    json.dump(annotations, f, indent=4)
                self.status_label.setText(f"Saved annotations to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save annotations: {str(e)}")
                
    def save_annotations_csv(self):
        """Save annotations to CSV file"""
        if not self.current_image_id or not self.boxes:
            QMessageBox.warning(self, "Warning", "No annotations to save")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Annotations", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='') as f:
                    f.write("image_id,x,y,width,height,category,location,body_map_id\n")
                    for box in self.boxes:
                        f.write(f"{self.current_image_id},{box['box'].x()},{box['box'].y()},"
                               f"{box['box'].width()},{box['box'].height()},{box['category']},"
                               f"{box['location']},{box['body_map_id']}\n")
                self.status_label.setText(f"Saved annotations to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save annotations: {str(e)}")
    
    def show_body_map(self):
        dialog = BodyMapDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_id:
            self.body_map_input.setText(dialog.selected_id)
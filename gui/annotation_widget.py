from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QComboBox, QGroupBox, QScrollArea,
                           QMessageBox, QRubberBand, QLineEdit, QFrame)
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath, QPixmap
from datetime import datetime
from utils.image_utils import ImageHandler
import json
from config import Config

class AnnotationMode:
    CREATE = "Create"
    EDIT = "Edit"

class AnnotationWidget(QWidget):
    def __init__(self, db_connector, user_profile, parent=None):
        super().__init__(parent)
        self.db_connector = db_connector  # Store the entire connector, not just connection
        self.user_profile = user_profile
        self.image_handler = ImageHandler()
        self.current_wound_id = None
        self.current_mode = AnnotationMode.CREATE
        self.selected_box = None
        self.boxes = []
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
        self.body_location_display.setStyleSheet("color: #0000FF; font-weight: bold;")
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
        
        # Mode indicator
        self.mode_label = QLabel("Mode: Create")
        self.mode_label.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px; border-radius: 3px;")
        layout.addWidget(self.mode_label)
        
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
        
        # Mode toggle button
        self.mode_toggle_btn = QPushButton("Toggle Edit Mode")
        self.mode_toggle_btn.clicked.connect(self.toggle_mode)
        annotation_controls.addWidget(self.mode_toggle_btn)
        
        # Undo button
        self.undo_btn = QPushButton("Undo Last Box")
        self.undo_btn.clicked.connect(self.undo_last_box)
        self.undo_btn.setEnabled(False)
        annotation_controls.addWidget(self.undo_btn)
        
        # Delete button
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected_box)
        self.delete_btn.setEnabled(False)
        annotation_controls.addWidget(self.delete_btn)
        
        # Save button
        save_btn = QPushButton("Save Annotations")
        save_btn.clicked.connect(self.save_annotations_to_databricks)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        annotation_controls.addWidget(save_btn)
        
        layout.addLayout(annotation_controls)
        
        # Status bar
        self.status_label = QLabel()
        self.status_label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        layout.addWidget(self.status_label)
        
        # Drawing variables
        self.drawing = False
        self.start_point = None
        self.current_box = None

    def load_image(self, wound_id):
        """Load and display image with wound information"""
        try:
            self.clearAnnotations()
            self.current_wound_id = wound_id
            
            # Get wound info from Databricks
            wound_info = self.db_connector.get_wound_assessment(wound_id)
            print(f"Received wound info: {wound_info}")
            
            if wound_info:
                # Ensure we have image data
                if wound_info.image_data:
                    # Display image
                    pixmap = self.image_handler.decode_image_content(wound_info.image_data)
                    if pixmap:
                        pixmap = self.image_handler.resize_pixmap(pixmap)
                        self.image_label.setPixmap(pixmap)
                        
                        # Update wound info display
                        self.wound_type_display.setText(str(wound_info.wound_type))
                        self.body_location_display.setText(str(wound_info.body_location))
                        
                        # Update dropdowns
                        self.category_combo.setCurrentText(wound_info.wound_type)
                        self.location_combo.setCurrentText(wound_info.body_location)
                        
                        # Load existing annotations if any
                        if wound_info.annotations:
                            self.load_existing_annotations(wound_info.annotations)
                        
                        self.status_label.setText(f"Loaded wound assessment {wound_id}")
                    else:
                        QMessageBox.warning(self, "Error", "Failed to decode image")
                else:
                    QMessageBox.warning(self, "Error", "No image data found")
            else:
                QMessageBox.warning(self, "Error", f"No wound information found for ID: {wound_id}")
                
        except Exception as e:
            print(f"Error loading image: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to load image: {str(e)}")
            
    def load_existing_annotations(self, annotations_data):
        """Load existing annotations from database"""
        try:
            if isinstance(annotations_data, str):
                annotations_data = json.loads(annotations_data)
            
            for box_data in annotations_data.get('boxes', []):
                # Create rubber band
                rubber_band = QRubberBand(QRubberBand.Rectangle, self)
                rubber_band.setGeometry(
                    box_data['x'],
                    box_data['y'],
                    box_data['width'],
                    box_data['height']
                )
                rubber_band.show()
                
                # Store box information
                self.boxes.append({
                    'box': rubber_band.geometry(),
                    'rubber_band': rubber_band,
                    'category': box_data['category'],
                    'location': box_data['location'],
                    'body_map_id': box_data.get('body_map_id', ''),
                    'created_by': box_data.get('created_by', 'unknown'),
                    'created_at': box_data.get('created_at', '')
                })
            
            if self.boxes:
                self.undo_btn.setEnabled(True)
                
        except Exception as e:
            print(f"Error loading annotations: {str(e)}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.current_mode == AnnotationMode.CREATE:
                self.drawing = True
                self.start_point = event.pos()
            elif self.current_mode == AnnotationMode.EDIT:
                self.select_box_at_point(event.pos())

    def mouseMoveEvent(self, event):
        if self.drawing and self.current_mode == AnnotationMode.CREATE:
            if self.current_box:
                self.current_box.hide()
            self.current_box = QRubberBand(QRubberBand.Rectangle, self)
            self.current_box.setGeometry(QRect(self.start_point, event.pos()).normalized())
            self.current_box.show()
        elif self.current_mode == AnnotationMode.EDIT and self.selected_box:
            # Update selected box position
            if hasattr(self.selected_box, 'rubber_band'):
                new_rect = QRect(self.selected_box['rubber_band'].geometry())
                new_rect.moveCenter(event.pos())
                self.selected_box['rubber_band'].setGeometry(new_rect)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.current_mode == AnnotationMode.CREATE:
                self.finish_create_annotation(event)
            elif self.current_mode == AnnotationMode.EDIT:
                self.finish_edit_annotation(event)

    def finish_create_annotation(self, event):
        if self.drawing and self.current_box:
            box_geometry = self.current_box.geometry()
            permanent_box = QRubberBand(QRubberBand.Rectangle, self)
            permanent_box.setGeometry(box_geometry)
            permanent_box.show()
            
            # Store box information
            self.boxes.append({
                'box': box_geometry,
                'rubber_band': permanent_box,
                'category': self.category_combo.currentText(),
                'location': self.location_combo.currentText(),
                'body_map_id': self.body_map_input.text(),
                'created_by': self.user_profile.username,
                'created_at': datetime.now().isoformat()
            })
            
            self.current_box.hide()
            self.current_box = None
            self.drawing = False
            self.undo_btn.setEnabled(True)
            self.status_label.setText(f"Added annotation: {len(self.boxes)}")

    def finish_edit_annotation(self, event):
        if self.selected_box:
            # Update box geometry
            self.selected_box['box'] = self.selected_box['rubber_band'].geometry()
            self.selected_box = None
            self.status_label.setText("Updated annotation position")

    def toggle_mode(self):
        """Toggle between create and edit modes"""
        if self.current_mode == AnnotationMode.CREATE:
            self.current_mode = AnnotationMode.EDIT
            self.mode_label.setText("Mode: Edit")
            self.mode_label.setStyleSheet(
                "background-color: #2196F3; color: white; padding: 5px; border-radius: 3px;"
            )
        else:
            self.current_mode = AnnotationMode.CREATE
            self.mode_label.setText("Mode: Create")
            self.mode_label.setStyleSheet(
                "background-color: #4CAF50; color: white; padding: 5px; border-radius: 3px;"
            )
            self.selected_box = None
            self.delete_btn.setEnabled(False)
            self.clear_highlights()

    def select_box_at_point(self, point):
        """Select box at given point"""
        for box in self.boxes:
            if box['rubber_band'].geometry().contains(point):
                self.selected_box = box
                self.highlight_selected_box()
                self.delete_btn.setEnabled(True)
                return
        
        self.selected_box = None
        self.delete_btn.setEnabled(False)
        self.clear_highlights()

    def highlight_selected_box(self):
        """Highlight selected box"""
        self.clear_highlights()
        if self.selected_box:
            self.selected_box['rubber_band'].setStyleSheet(
                "border: 2px solid yellow;"
            )

    def clear_highlights(self):
        """Clear all box highlights"""
        for box in self.boxes:
            box['rubber_band'].setStyleSheet("")

    def undo_last_box(self):
        """Remove the last drawn box"""
        if self.boxes:
            last_box = self.boxes.pop()
            last_box['rubber_band'].hide()
            last_box['rubber_band'].deleteLater()
            
            if not self.boxes:
                self.undo_btn.setEnabled(False)
            self.status_label.setText("Undid last annotation")

    def delete_selected_box(self):
        """Delete the selected box"""
        if self.selected_box:
            reply = QMessageBox.question(
                self, 'Delete Annotation',
                'Are you sure you want to delete this annotation?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.selected_box['rubber_band'].hide()
                self.selected_box['rubber_band'].deleteLater()
                self.boxes.remove(self.selected_box)
                self.selected_box = None
                self.delete_btn.setEnabled(False)
                
                if not self.boxes:
                    self.undo_btn.setEnabled(False)
                self.status_label.setText("Deleted annotation")

    def save_annotations_to_databricks(self):
        """Save annotations back to Databricks"""
        if not self.current_wound_id or not self.boxes:
            QMessageBox.warning(self, "Warning", "No annotations to save")
            return

        try:
            self.status_label.setText("Saving annotations...")
            
            # Prepare annotations for saving
            current_time = datetime.now().isoformat()
            annotations = []
            
            for box in self.boxes:
                annotations.append({
                    'x': box['box'].x(),
                    'y': box['box'].y(),
                    'width': box['box'].width(),
                    'height': box['box'].height(),
                    'category': box['category'],
                    'location': box['location'],
                    'body_map_id': box['body_map_id'],
                    'created_by': box['created_by'],
                    'created_at': box['created_at'],
                    'last_modified_by': self.user_profile.username,
                    'last_modified_at': current_time
                })

            # Save to database
            success = self.db_connector.save_annotations(self.current_wound_id, annotations)
            
            if success:
                self.status_label.setText("Annotations saved successfully")
                QMessageBox.information(self, "Success", "Annotations saved to database")
            else:
                self.status_label.setText("Failed to save annotations")
                QMessageBox.warning(self, "Error", "Failed to save annotations")

        except Exception as e:
            print(f"Error saving annotations: {str(e)}")
            self.status_label.setText("Error saving annotations")
            QMessageBox.critical(self, "Error", f"Failed to save annotations: {str(e)}")

    def show_body_map(self):
        """Show body map dialog"""
        from .body_map_dialog import BodyMapDialog
        dialog = BodyMapDialog(self)
        dialog.exec_()

    def clearAnnotations(self):
        """Clear all annotations"""
        for box in self.boxes:
            if 'rubber_band' in box:
                box['rubber_band'].hide()
                box['rubber_band'].deleteLater()
        self.boxes = []
        self.undo_btn.setEnabled(False)
        self.selected_box = None
        self.delete_btn.setEnabled(False)
        self.status_label.setText("Cleared all annotations")

    def resizeEvent(self, event):
        """Handle widget resize"""
        super().resizeEvent(event)
        # Update box positions based on new size if needed
        if hasattr(self, 'boxes'):
            for box in self.boxes:
                if 'rubber_band' in box:
                    box['rubber_band'].setGeometry(box['box'])

    def show_annotation_info(self, box):
        """Show annotation information"""
        info = (
            f"Category: {box['category']}\n"
            f"Location: {box['location']}\n"
            f"Body Map ID: {box['body_map_id']}\n"
            f"Created by: {box['created_by']}\n"
            f"Created at: {box['created_at']}"
        )
        QMessageBox.information(self, "Annotation Information", info)

    def validate_annotation(self, box):
        """Validate annotation data"""
        if not box['category']:
            return False, "Category is required"
        if not box['location']:
            return False, "Location is required"
        return True, ""

    def export_annotations(self, format='json'):
        """Export annotations to file"""
        if not self.boxes:
            QMessageBox.warning(self, "Warning", "No annotations to export")
            return

        try:
            if format == 'json':
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Save Annotations", "", "JSON Files (*.json)"
                )
                if file_path:
                    annotations = {
                        'wound_id': self.current_wound_id,
                        'boxes': [{
                            'x': box['box'].x(),
                            'y': box['box'].y(),
                            'width': box['box'].width(),
                            'height': box['box'].height(),
                            'category': box['category'],
                            'location': box['location'],
                            'body_map_id': box['body_map_id'],
                            'created_by': box['created_by'],
                            'created_at': box['created_at']
                        } for box in self.boxes]
                    }
                    
                    with open(file_path, 'w') as f:
                        json.dump(annotations, f, indent=4)
                    
                    self.status_label.setText(f"Annotations exported to {file_path}")

        except Exception as e:
            print(f"Error exporting annotations: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to export annotations: {str(e)}")

    def import_annotations(self, file_path):
        """Import annotations from file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            if data.get('wound_id') != self.current_wound_id:
                reply = QMessageBox.question(
                    self,
                    'Import Annotations',
                    'Wound ID mismatch. Import anyway?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            self.clearAnnotations()
            
            for box_data in data.get('boxes', []):
                rubber_band = QRubberBand(QRubberBand.Rectangle, self)
                rubber_band.setGeometry(
                    box_data['x'],
                    box_data['y'],
                    box_data['width'],
                    box_data['height']
                )
                rubber_band.show()
                
                self.boxes.append({
                    'box': rubber_band.geometry(),
                    'rubber_band': rubber_band,
                    'category': box_data['category'],
                    'location': box_data['location'],
                    'body_map_id': box_data.get('body_map_id', ''),
                    'created_by': box_data.get('created_by', self.user_profile.username),
                    'created_at': box_data.get('created_at', datetime.now().isoformat())
                })
            
            if self.boxes:
                self.undo_btn.setEnabled(True)
                self.status_label.setText("Annotations imported successfully")

        except Exception as e:
            print(f"Error importing annotations: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to import annotations: {str(e)}")

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Delete and self.selected_box:
            self.delete_selected_box()
        elif event.key() == Qt.Key_Escape:
            if self.drawing:
                self.drawing = False
                if self.current_box:
                    self.current_box.hide()
                    self.current_box = None
            elif self.selected_box:
                self.selected_box = None
                self.delete_btn.setEnabled(False)
                self.clear_highlights()
        elif event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_S:
                self.save_annotations_to_databricks()
            elif event.key() == Qt.Key_Z:
                self.undo_last_box()
            elif event.key() == Qt.Key_E:
                self.toggle_mode()
        event.accept()
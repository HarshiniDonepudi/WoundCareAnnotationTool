# gui/annotation_widget.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QComboBox, QGroupBox, QScrollArea,
                              QMessageBox, QLineEdit, QFrame, QSizePolicy, 
                              QFileDialog, QRubberBand)
from PyQt5.QtCore import Qt, QRect, QEvent
from PyQt5.QtGui import QPainter, QColor, QPen, QPixmap
from datetime import datetime
from utils.image_utils import ImageHandler
from config import Config
import json
import uuid  # Ensure uuid is imported

# -------------------------------------------------------------------------
# Annotation mode enum
# -------------------------------------------------------------------------
class AnnotationMode:
    CREATE = "Create"
    EDIT = "Edit"

# -------------------------------------------------------------------------
# A custom QRubberBand subclass that draws a colored border and displays
# its coordinates (x, y, width, height) and annotation info (wound type,
# body map id, and location) on the rubber band.
# Also supports a "selected" flag so that a selected annotation is drawn in yellow.
# -------------------------------------------------------------------------
class ColoredRubberBand(QRubberBand):
    def __init__(self, shape, parent=None, color="#FF0000", annotation_info=""):
        super().__init__(shape, parent)
        self._color = color
        self.selected = False
        self.annotation_info = annotation_info

    def setSelected(self, selected: bool):
        self.selected = selected
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        draw_color = "yellow" if self.selected else self._color
        pen = QPen(QColor(draw_color))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        # Draw coordinate text in the upper-left corner.
        rect = self.rect()
        coord_text = f"{rect.x()},{rect.y()}  {rect.width()}x{rect.height()}"
        painter.setPen(QColor("black"))
        painter.drawText(rect.adjusted(3, 3, -3, -3), Qt.AlignLeft | Qt.AlignTop, coord_text)
        # Draw annotation info below the coordinates.
        if self.annotation_info:
            painter.drawText(rect.adjusted(3, 20, -3, -3), Qt.AlignLeft, self.annotation_info)
        painter.end()

# -------------------------------------------------------------------------
# (Optional) AnnotationOverlay – provided for future use if needed.
# Currently, ColoredRubberBand objects are used for drawing.
# -------------------------------------------------------------------------
class AnnotationOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.annotations = []  # List of dicts: each has keys 'rect' and 'color'

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen()
        pen.setWidth(2)
        for ann in self.annotations:
            pen.setColor(QColor(ann['color']))
            painter.setPen(pen)
            painter.drawRect(ann['rect'])
        painter.end()

    def add_annotation(self, rect, color):
        self.annotations.append({'rect': rect, 'color': color})
        self.update()

    def clear_annotations(self):
        self.annotations.clear()
        self.update()

# -------------------------------------------------------------------------
# Main AnnotationWidget class
# -------------------------------------------------------------------------
class AnnotationWidget(QWidget):
    def __init__(self, db_connector, user_profile, parent=None):
        super().__init__(parent)
        self.db_connector = db_connector
        self.user_profile = user_profile
        self.image_handler = ImageHandler()
        self.current_wound_id = None
        # We'll set the default mode to EDIT so that even if annotations exist,
        # you can add new ones.
        self.current_mode = AnnotationMode.EDIT  
        self.selected_box = None
        self.boxes = []  # List of dictionaries storing annotation info.
        self.category_colors = Config.CATEGORY_COLORS
        self.current_color = "#FF0000"
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Top info panel ---
        info_panel = QGroupBox("Wound Information")
        info_layout = QHBoxLayout()
        
        # Wound Type
        wound_type_layout = QVBoxLayout()
        wound_type_label = QLabel("Databricks Wound Type:")
        self.wound_type_display = QLabel("Not loaded")
        self.wound_type_display.setStyleSheet("font-weight: bold;")
        wound_type_layout.addWidget(wound_type_label)
        wound_type_layout.addWidget(self.wound_type_display)
        info_layout.addLayout(wound_type_layout)
        
        # Body Location
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
        
        patient_id_layout = QVBoxLayout()
        patient_id_label = QLabel("Patient ID:")
        self.patient_id_display = QLabel("Not loaded")
        self.patient_id_display.setStyleSheet("font-weight: bold;")
        patient_id_layout.addWidget(patient_id_label)
        patient_id_layout.addWidget(self.patient_id_display)
        info_layout.addLayout(patient_id_layout)
        
        info_panel.setLayout(info_layout)
        layout.addWidget(info_panel)
        
        # --- Mode indicator ---
        # Even though the default mode is EDIT, the label will display accordingly.
        self.mode_label = QLabel("Mode: Edit")
        self.mode_label.setStyleSheet("background-color: #2196F3; color: white; padding: 5px; border-radius: 3px;")
        layout.addWidget(self.mode_label)
        
        # --- Image display area with scroll ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
        
        # --- Annotation overlay ---
        self.annotation_overlay = AnnotationOverlay(self.image_label)
        self.annotation_overlay.setGeometry(self.image_label.rect())
        self.annotation_overlay.setStyleSheet("background: transparent;")
        self.annotation_overlay.show()
        
        # --- Controls: Category & Location ---
        controls_layout = QHBoxLayout()
        category_group = QGroupBox("Wound Category")
        category_layout = QVBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.addItems(Config.ETIOLOGY_OPTIONS)
        for i, category in enumerate(Config.ETIOLOGY_OPTIONS):
            self.category_combo.setItemData(i, QColor(self.category_colors.get(category, "#FF0000")), Qt.ForegroundRole)
        category_layout.addWidget(self.category_combo)
        category_group.setLayout(category_layout)
        controls_layout.addWidget(category_group)
        
        location_group = QGroupBox("Body Location")
        location_layout = QVBoxLayout()
        self.location_combo = QComboBox()
        self.location_combo.addItems(Config.BODY_LOCATIONS)
        location_layout.addWidget(self.location_combo)
        location_group.setLayout(location_layout)
        controls_layout.addWidget(location_group)
        layout.addLayout(controls_layout)
        
        # --- Annotation controls ---
        annotation_controls = QHBoxLayout()
        self.mode_toggle_btn = QPushButton("Toggle Edit Mode")
        self.mode_toggle_btn.clicked.connect(self.toggle_mode)
        # The toggle button remains visible so the user can switch if desired.
        annotation_controls.addWidget(self.mode_toggle_btn)
        
        self.undo_btn = QPushButton("Undo Last Box")
        self.undo_btn.clicked.connect(self.undo_last_box)
        self.undo_btn.setEnabled(False)
        annotation_controls.addWidget(self.undo_btn)
        
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected_box)
        self.delete_btn.setEnabled(False)
        annotation_controls.addWidget(self.delete_btn)
        
        self.update_btn = QPushButton("Update Annotation")
        self.update_btn.clicked.connect(self.update_selected_annotation)
        self.update_btn.setEnabled(False)
        annotation_controls.addWidget(self.update_btn)
        
        save_btn = QPushButton("Save Annotations")
        save_btn.clicked.connect(self.save_annotations_to_databricks)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        annotation_controls.addWidget(save_btn)
        layout.addLayout(annotation_controls)
        
        # --- Annotation Counter Screen ---
        counter_group = QGroupBox("Annotation Counters")
        counter_layout = QVBoxLayout()
        self.counter_label = QLabel("No annotations")
        counter_layout.addWidget(self.counter_label)
        counter_group.setLayout(counter_layout)
        layout.addWidget(counter_group)
        
        # --- Status bar ---
        self.status_label = QLabel()
        self.status_label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        layout.addWidget(self.status_label)
        
        # --- Drawing variables ---
        self.drawing = False
        self.start_point = None
        self.current_box = None
        self.current_color = "#FF0000"
        
        # Install event filter on the scroll area's viewport.
        self.scroll_area.viewport().installEventFilter(self)
        
    # ---------------------------------------------------------------------
    # Update UI fields from a selected annotation.
    # ---------------------------------------------------------------------
    def update_ui_fields_from_annotation(self, annotation):
        self.category_combo.setCurrentText(annotation['category'])
        self.location_combo.setCurrentText(annotation.get('location', ''))
        self.body_map_input.setText(annotation.get('body_map_id', ''))
        
    # ---------------------------------------------------------------------
    # Update the annotation counter.
    # ---------------------------------------------------------------------
    def update_annotation_counter(self):
        counts = {}
        for box in self.boxes:
            cat = box.get('category', 'Unknown')
            counts[cat] = counts.get(cat, 0) + 1
        counter_str = ", ".join(f"{cat}: {count}" for cat, count in counts.items())
        if not counter_str:
            counter_str = "No annotations"
        self.counter_label.setText(counter_str)
        
    # ---------------------------------------------------------------------
    # Image and Annotation Loading
    # ---------------------------------------------------------------------
    def load_image(self, wound_id):
        try:
            self.clearAnnotations()
            self.current_wound_id = wound_id
            wound_info = self.db_connector.get_wound_assessment(wound_id)
            print(f"Received wound info: {wound_info}")
            if wound_info:
                if wound_info.image_data:
                    pixmap = self.image_handler.decode_image_content(wound_info.image_data)
                    if pixmap:
                        scroll_size = self.scroll_area.size()
                        pixmap = pixmap.scaled(scroll_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.image_label.setPixmap(pixmap)
                        self.image_label.adjustSize()
                        self.annotation_overlay.setGeometry(self.image_label.rect())
                        self.wound_type_display.setText(str(wound_info.wound_type))
                        self.body_location_display.setText(str(wound_info.body_location))
                        self.category_combo.setCurrentText(wound_info.wound_type)
                        self.location_combo.setCurrentText(wound_info.body_location)
                        # Update patient id (if available)
                        if hasattr(wound_info, 'patient_id') and wound_info.patient_id:
                            self.patient_id_display.setText(str(wound_info.patient_id))
                        else:
                            self.patient_id_display.setText("Not loaded")
                        # Check if annotations exist.
                        annotations_data = self.db_connector.get_annotations(wound_info.wound_assessment_id)
                        if annotations_data and annotations_data.get('boxes'):
                            self.load_existing_annotations(annotations_data)
                            self.current_mode = AnnotationMode.EDIT
                            self.mode_label.setText("Mode: Edit")
                            self.mode_label.setStyleSheet("background-color: #2196F3; color: white; padding: 5px; border-radius: 3px;")
                        else:
                            self.current_mode = AnnotationMode.EDIT
                            self.mode_label.setText("Mode: Edit")
                            self.mode_label.setStyleSheet("background-color: #2196F3; color: white; padding: 5px; border-radius: 3px;")
                        self.status_label.setText(f"Loaded wound assessment {wound_id}")
                        self.update_annotation_counter()
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
        try:
            if isinstance(annotations_data, str):
                annotations_data = json.loads(annotations_data)
            if self.image_label.pixmap():
                displayed_size = self.image_label.pixmap().size()
                print("Displayed image size:", displayed_size)
            else:
                print("No pixmap found in image_label.")
            for box_data in annotations_data.get('boxes', []):
                print("Loading annotation:", box_data)
                color = self.category_colors.get(box_data['category'], "#FF0000")
                rect = QRect(
                    box_data['x'], box_data['y'],
                    box_data['width'], box_data['height']
                )
                annotation_info = f"Type: {box_data['category']}, Map: {box_data.get('body_map_id','')}, Loc: {box_data['location']}"
                rubber_band = ColoredRubberBand(QRubberBand.Rectangle, self.image_label, color, annotation_info)
                rubber_band.setGeometry(rect)
                rubber_band.show()
                self.boxes.append({
                    'box': rect,
                    'rubber_band': rubber_band,
                    'category': box_data['category'],
                    'location': box_data['location'],
                    'body_map_id': box_data.get('body_map_id', ''),
                    'created_by': box_data.get('created_by', 'unknown'),
                    'created_at': box_data.get('created_at', None),
                    'last_modified_by': box_data.get('last_modified_by', None),
                    'last_modified_at': box_data.get('last_modified_at', None)
                })
            if self.boxes:
                self.undo_btn.setEnabled(True)
                self.update_annotation_counter()
        except Exception as e:
            print(f"Error loading annotations: {str(e)}")
            
    # ---------------------------------------------------------------------
    # Mouse event handling for drawing/editing annotations.
    # Coordinates are mapped relative to image_label.
    # ---------------------------------------------------------------------
    def mousePressEvent(self, event):
        local_pos = self.image_label.mapFrom(self, event.pos())
        if event.button() == Qt.LeftButton:
            # In EDIT mode, try to select an existing annotation first.
            if self.current_mode == AnnotationMode.EDIT:
                found = False
                for box in self.boxes:
                    if box['rubber_band'].geometry().contains(local_pos):
                        self.selected_box = box
                        self.highlight_selected_box()
                        self.delete_btn.setEnabled(True)
                        self.update_ui_fields_from_annotation(box)
                        found = True
                        break
                if not found:
                    # If no annotation is hit, start drawing a new annotation.
                    self.drawing = True
                    self.start_point = local_pos
                    self.current_color = self.category_colors.get(self.category_combo.currentText(), "#FF0000")
            # In CREATE mode, start drawing a new annotation.
            elif self.current_mode == AnnotationMode.CREATE:
                self.drawing = True
                self.start_point = local_pos
                self.current_color = self.category_colors.get(self.category_combo.currentText(), "#FF0000")
                
    def mouseMoveEvent(self, event):
        if self.drawing:
            local_pos = self.image_label.mapFrom(self, event.pos())
            if self.current_box:
                self.current_box.hide()
            self.current_box = ColoredRubberBand(QRubberBand.Rectangle, self.image_label, self.current_color)
            self.current_box.setGeometry(QRect(self.start_point, local_pos).normalized())
            self.current_box.show()
        elif self.current_mode == AnnotationMode.EDIT and self.selected_box:
            local_pos = self.image_label.mapFrom(self, event.pos())
            new_rect = QRect(self.selected_box['rubber_band'].geometry())
            new_rect.moveCenter(local_pos)
            self.selected_box['rubber_band'].setGeometry(new_rect)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.drawing:
                self.finish_create_annotation()
            elif self.current_mode == AnnotationMode.EDIT and self.selected_box:
                self.finish_edit_annotation()
                
    def mouseDoubleClickEvent(self, event):
        local_pos = self.image_label.mapFrom(self, event.pos())
        for box in self.boxes:
            if box['rubber_band'].geometry().contains(local_pos):
                self.show_annotation_info(box)
                break

    # ---------------------------------------------------------------------
    # Finalizing annotation creation/editing
    # ---------------------------------------------------------------------
    def finish_create_annotation(self):
        if self.drawing and self.current_box:
            box_geometry = self.current_box.geometry()
            now = datetime.now()
            annotation_info = f"Type: {self.category_combo.currentText()}, Map: {self.body_map_input.text().strip()}, Loc: {self.location_combo.currentText()}"
            permanent_box = ColoredRubberBand(QRubberBand.Rectangle, self.image_label, self.current_color, annotation_info)
            permanent_box.setGeometry(box_geometry)
            permanent_box.show()
            self.boxes.append({
                'box': box_geometry,
                'rubber_band': permanent_box,
                'category': self.category_combo.currentText(),
                'location': self.location_combo.currentText(),
                'body_map_id': self.body_map_input.text().strip(),
                'created_by': self.user_profile.username,
                'created_at': now,
                'last_modified_by': self.user_profile.username,
                'last_modified_at': now
            })
            self.current_box.hide()
            self.current_box = None
            self.drawing = False
            self.undo_btn.setEnabled(True)
            self.status_label.setText(f"Added annotation: {len(self.boxes)}")
            self.update_annotation_counter()
            
    def finish_edit_annotation(self):
        if self.selected_box:
            self.selected_box['box'] = self.selected_box['rubber_band'].geometry()
            self.selected_box = None
            self.status_label.setText("Updated annotation position")
            self.update_annotation_counter()
            
    # ---------------------------------------------------------------------
    # Update selected annotation from UI fields.
    # ---------------------------------------------------------------------
    def update_selected_annotation(self):
        if self.selected_box:
            # Update the annotation dictionary from the UI fields.
            self.selected_box['category'] = self.category_combo.currentText()
            self.selected_box['location'] = self.location_combo.currentText()
            self.selected_box['body_map_id'] = self.body_map_input.text().strip()
            # Update the rubber band's overlay text.
            annotation_info = f"Type: {self.selected_box['category']}, Map: {self.selected_box['body_map_id']}, Loc: {self.selected_box['location']}"
            self.selected_box['rubber_band'].annotation_info = annotation_info
            self.selected_box['rubber_band'].update()
            self.status_label.setText("Updated selected annotation.")
            self.update_annotation_counter()
            
    # ---------------------------------------------------------------------
    # Mode toggling and selection.
    # ---------------------------------------------------------------------
    def toggle_mode(self):
        # We allow toggling even when annotations exist.
        if self.current_mode == AnnotationMode.CREATE:
            self.current_mode = AnnotationMode.EDIT
            self.mode_label.setText("Mode: Edit")
            self.mode_label.setStyleSheet("background-color: #2196F3; color: white; padding: 5px; border-radius: 3px;")
        else:
            self.current_mode = AnnotationMode.CREATE
            self.mode_label.setText("Mode: Create")
            self.mode_label.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px; border-radius: 3px;")
            self.selected_box = None
            self.delete_btn.setEnabled(False)
            self.clear_highlights()
            
    def select_box_at_point(self, point):
        for box in self.boxes:
            if box['rubber_band'].geometry().contains(point):
                self.selected_box = box
                self.highlight_selected_box()
                self.delete_btn.setEnabled(True)
                self.update_ui_fields_from_annotation(box)
                return
        self.selected_box = None
        self.delete_btn.setEnabled(False)
        self.clear_highlights()
        
    def update_ui_fields_from_annotation(self, annotation):
        self.category_combo.setCurrentText(annotation['category'])
        self.location_combo.setCurrentText(annotation.get('location', ''))
        self.body_map_input.setText(annotation.get('body_map_id', ''))
        
    def highlight_selected_box(self):
        self.clear_highlights()
        if self.selected_box:
            self.selected_box['rubber_band'].setSelected(True)
            
    def clear_highlights(self):
        for box in self.boxes:
            box['rubber_band'].setSelected(False)
            
    def undo_last_box(self):
        if self.boxes:
            last_box = self.boxes.pop()
            last_box['rubber_band'].hide()
            last_box['rubber_band'].deleteLater()
            if not self.boxes:
                self.undo_btn.setEnabled(False)
            self.status_label.setText("Undid last annotation")
            self.update_annotation_counter()
            
    def delete_selected_box(self):
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
                self.update_annotation_counter()
                
    # ---------------------------------------------------------------------
    # Saving and exporting/importing annotations.
    # ---------------------------------------------------------------------
    def save_annotations_to_databricks(self):
        if not self.current_wound_id or not self.boxes:
            QMessageBox.warning(self, "Warning", "No annotations to save")
            return
        try:
            self.status_label.setText("Saving annotations...")
            annotations = []
            for box in self.boxes:
                body_map_id_val = box.get('body_map_id', '').strip() or self.body_map_input.text().strip()
                created_at = (box['created_at'].isoformat() 
                              if isinstance(box['created_at'], datetime) 
                              else box['created_at'])
                last_modified_at = (box['last_modified_at'].isoformat() 
                                    if isinstance(box['last_modified_at'], datetime) 
                                    else box['last_modified_at'])
                annotations.append({
                    'x': box['box'].x(),
                    'y': box['box'].y(),
                    'width': box['box'].width(),
                    'height': box['box'].height(),
                    'category': box['category'],
                    'location': box.get('location', ''),
                    'body_map_id': body_map_id_val,
                    'created_by': box['created_by'],
                    'created_at': created_at,
                    'last_modified_by': box.get('last_modified_by', self.user_profile.username),
                    'last_modified_at': last_modified_at
                })
            print("Annotation JSON:")
            print(json.dumps(annotations, indent=4))
            
            success = self.db_connector.save_annotations(int(self.current_wound_id), annotations)
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
            
    def export_annotations(self, format='json'):
        if not self.boxes:
            QMessageBox.warning(self, "Warning", "No annotations to export")
            return
        try:
            if format == 'json':
                file_path, _ = QFileDialog.getSaveFileName(self, "Save Annotations", "", "JSON Files (*.json)")
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
                            'created_at': box['created_at'] if not isinstance(box['created_at'], datetime) else box['created_at'].isoformat()
                        } for box in self.boxes]
                    }
                    with open(file_path, 'w') as f:
                        json.dump(annotations, f, indent=4)
                    self.status_label.setText(f"Annotations exported to {file_path}")
        except Exception as e:
            print(f"Error exporting annotations: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to export annotations: {str(e)}")
        
    def import_annotations(self, file_path):
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
                color = self.category_colors.get(box_data['category'], "#FF0000")
                annotation_info = f"Type: {box_data['category']}, Map: {box_data.get('body_map_id','')}, Loc: {box_data['location']}"
                rubber_band = ColoredRubberBand(QRubberBand.Rectangle, self.image_label, color, annotation_info)
                rubber_band.setGeometry(QRect(
                    box_data['x'], box_data['y'],
                    box_data['width'], box_data['height']
                ))
                rubber_band.show()
                self.boxes.append({
                    'box': rubber_band.geometry(),
                    'rubber_band': rubber_band,
                    'category': box_data['category'],
                    'location': box_data['location'],
                    'body_map_id': box_data.get('body_map_id', ''),
                    'created_by': box_data.get('created_by', self.user_profile.username),
                    'created_at': box_data.get('created_at', datetime.now().isoformat()),
                    'last_modified_by': box_data.get('last_modified_by', self.user_profile.username),
                    'last_modified_at': box_data.get('last_modified_at', datetime.now().isoformat())
                })
            if self.boxes:
                self.undo_btn.setEnabled(True)
                self.status_label.setText("Annotations imported successfully")
                self.update_annotation_counter()
        except Exception as e:
            print(f"Error importing annotations: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to import annotations: {str(e)}")
        
    def show_body_map(self):
        from .body_map_dialog import BodyMapDialog
        dialog = BodyMapDialog(self)
        dialog.exec_()
        
    def clearAnnotations(self):
        for box in self.boxes:
            if 'rubber_band' in box:
                box['rubber_band'].hide()
                box['rubber_band'].deleteLater()
        self.boxes = []
        self.undo_btn.setEnabled(False)
        self.selected_box = None
        self.delete_btn.setEnabled(False)
        self.status_label.setText("Cleared all annotations")
        self.update_annotation_counter()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        for box in self.boxes:
            if 'rubber_band' in box:
                box['rubber_band'].setGeometry(box['box'])
        if self.image_label.pixmap():
            self.annotation_overlay.setGeometry(self.image_label.rect())
            
    def eventFilter(self, obj, event):
        if obj == self.scroll_area.viewport() and event.type() == QEvent.Resize:
            self.annotation_overlay.setGeometry(self.image_label.rect())
        return super().eventFilter(obj, event)
        
    def show_annotation_info(self, box):
        info = (
            f"Category: {box['category']}\n"
            f"Location: {box['location']}\n"
            f"Body Map ID: {box['body_map_id']}\n"
            f"Created by: {box['created_by']}\n"
            f"Created at: {box['created_at']}\n"
            f"Coordinates: {box['box'].getRect()}"
        )
        QMessageBox.information(self, "Annotation Information", info)
        
    def validate_annotation(self, box):
        if not box['category']:
            return False, "Category is required"
        if not box['location']:
            return False, "Location is required"
        return True, ""
        
    def keyPressEvent(self, event):
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

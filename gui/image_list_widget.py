from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
 QLabel, QProgressBar, QMessageBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor

class ImageListWidget(QWidget):
    image_selected = pyqtSignal(str)

    def __init__(self, db_connector, parent=None):
        super().__init__(parent)
        self.db_connector = db_connector  # Explicitly store the connector
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Wound Images")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

    def load_wound_list(self):
        """Load all wound assessments"""
        try:
            self.progress_bar.show()
            self.status_label.setText("Loading wound list...")
            
            # Use self.db_connector to get wound paths
            wound_list = self.db_connector.get_all_wound_paths()
            
            self.list_widget.clear()
            for path in wound_list:
                item = QListWidgetItem(path)
                # Color code based on annotation status
                item.setBackground(QColor("#E8F5E9"))  # Light green for new
                self.list_widget.addItem(item)
            
            self.status_label.setText(f"Loaded {len(wound_list)} images")
        
        except Exception as e:
            print(f"Error loading wound list: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load wound list: {str(e)}")
            self.status_label.setText("Error loading wound list")
        
        finally:
            self.progress_bar.hide()

    def on_item_clicked(self, item):
        """Handle item selection"""
        try:
            path = item.text()
            self.progress_bar.show()
            self.status_label.setText("Loading image...")
            
            # Get wound assessment using the path
            wound_assessment = self.db_connector.get_wound_assessment(self.extract_id_from_path(path))
            
            if wound_assessment:
                # Emit the wound assessment ID
                self.image_selected.emit(str(wound_assessment.wound_assessment_id))
                self.status_label.setText(f"Loaded image {wound_assessment.wound_assessment_id}")
                # Update item color to indicate viewed
                item.setBackground(QColor("#E3F2FD"))  # Light blue
            else:
                self.status_label.setText("Failed to load image")
        
        except Exception as e:
            print(f"Error loading image: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load image: {str(e)}")
            self.status_label.setText("Error loading image")
        
        finally:
            self.progress_bar.hide()

    @staticmethod
    def extract_id_from_path(path: str) -> str:
        """Extract wound assessment ID from path"""
        try:
            # Assuming the last part of the path is the assessment ID
            return path.split('/')[-1]
        except:
            return ""
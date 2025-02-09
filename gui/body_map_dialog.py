from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                           QScrollArea, QWidget)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class BodyMapDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Body Map Reference")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Scroll area for the image
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Image container
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        # Image label
        image_label = QLabel()
        pixmap = QPixmap("resources/Body-map-for-location-selection.png")
        if not pixmap.isNull():
            image_label.setPixmap(pixmap)
            image_label.setScaledContents(True)
            image_label.setMinimumSize(800, 600)
        else:
            error_label = QLabel("Error: Body map image not found")
            container_layout.addWidget(error_label)
            
        container_layout.addWidget(image_label)
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)
        
        # Instructions
        instructions = QLabel(
            "Click on a location to select the body map ID.\n"
            "Hover over regions to see detailed information."
        )
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        # Set dialog size
        self.setMinimumSize(900, 700)
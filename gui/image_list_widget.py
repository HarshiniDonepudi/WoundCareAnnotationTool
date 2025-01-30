from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from utils.image_utils import ImageHandler

class ImageListWidget(QWidget):
    image_selected = pyqtSignal(str, bytes)  # Modified to emit both image ID and binary data
    
    def __init__(self):
        super().__init__()
        self.image_data = {}  # Dictionary to store binary image data
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Image list
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_image_selected)
        layout.addWidget(self.list_widget)
    
    def load_binary_text_images(self, binary_text_files):
        """
        Load images from binary text files
        binary_text_files: Dictionary where key is image ID and value is the path to binary text file
        """
        self.list_widget.clear()
        self.image_data = {}
        
        for image_id, file_path in binary_text_files.items():
            try:
                with open(file_path, 'r') as f:
                    binary_text = f.read()
                self.image_data[image_id] = binary_text
                self.list_widget.addItem(image_id)
            except Exception as e:
                print(f"Error loading binary text file {file_path}: {str(e)}")
                
    def load_binary_text_data(self, binary_text_dict):
        """
        Load images directly from binary text data
        binary_text_dict: Dictionary where key is image ID and value is the binary text data
        """
        self.list_widget.clear()
        self.image_data = binary_text_dict
        
        for image_id in binary_text_dict.keys():
            self.list_widget.addItem(image_id)
    
    def on_image_selected(self, item):
        image_id = item.text()
        binary_data = self.image_data.get(image_id)
        if binary_data:
            self.image_selected.emit(image_id, binary_data)

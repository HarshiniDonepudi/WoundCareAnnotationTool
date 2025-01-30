# main_window.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                           QPushButton, QProgressBar, QGroupBox, QFileDialog, 
                           QMessageBox, QApplication)
from PyQt5.QtCore import Qt
import os
from gui.annotation_widget import AnnotationWidget
from gui.image_list_widget import ImageListWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wound Annotation Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Create left panel for file upload and image list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Add upload button
        upload_group = QGroupBox("File Upload")
        upload_layout = QVBoxLayout()
        
        # Single file upload
        single_upload_btn = QPushButton("Upload Single File")
        single_upload_btn.clicked.connect(self.upload_single_file)
        upload_layout.addWidget(single_upload_btn)
        
        # Multiple files upload
        multi_upload_btn = QPushButton("Upload Multiple Files")
        multi_upload_btn.clicked.connect(self.upload_multiple_files)
        upload_layout.addWidget(multi_upload_btn)
        
        # Directory upload
        dir_upload_btn = QPushButton("Upload Directory")
        dir_upload_btn.clicked.connect(self.upload_directory)
        upload_layout.addWidget(dir_upload_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        upload_layout.addWidget(self.progress_bar)
        
        upload_group.setLayout(upload_layout)
        left_layout.addWidget(upload_group)
        
        # Create image list widget
        self.image_list = ImageListWidget()
        left_layout.addWidget(self.image_list)
        
        layout.addWidget(left_panel, 1)
        
        # Create annotation widget
        self.annotation_widget = AnnotationWidget()
        layout.addWidget(self.annotation_widget, 3)
        
        # Connect signals
        self.image_list.image_selected.connect(self.annotation_widget.load_image)
    
    def upload_single_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*.*)"  # Accept all file types
        )
        if file_path:
            self.load_binary_files([file_path])
    
    def upload_multiple_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "All Files (*.*)"  # Accept all file types
        )
        if file_paths:
            self.load_binary_files(file_paths)
    
    def upload_directory(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory with Files"
        )
        if dir_path:
            file_paths = []
            for file_name in os.listdir(dir_path):
                file_paths.append(os.path.join(dir_path, file_name))
            if file_paths:
                self.load_binary_files(file_paths)
            else:
                QMessageBox.warning(self, "No Files Found", "No files found in the selected directory.")
    
    def load_binary_files(self, file_paths):
        """
        Load files and update progress bar
        """
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(file_paths))
        self.progress_bar.setValue(0)
        
        binary_text_files = {}
        
        for i, file_path in enumerate(file_paths):
            try:
                # Extract ID from filename
                file_name = os.path.basename(file_path)
                file_id = os.path.splitext(file_name)[0]  # Remove extension
                
                # Read file content
                with open(file_path, 'rb') as f:  # Open in binary mode
                    content = f.read()
                    
                # Try to decode as text if it's a text file
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    # If not text, use binary content as is
                    pass
                
                # Add to dictionary
                binary_text_files[file_id] = content
                
                # Update progress
                self.progress_bar.setValue(i + 1)
                QApplication.processEvents()  # Keep UI responsive
                
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error Loading File",
                    f"Error loading {file_path}: {str(e)}"
                )
        
        if binary_text_files:
            self.image_list.load_binary_text_data(binary_text_files)
            
        self.progress_bar.setVisible(False)
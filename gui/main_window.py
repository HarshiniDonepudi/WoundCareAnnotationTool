from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
 QPushButton, QLabel, QMessageBox, QToolBar, QStatusBar)
from PyQt5.QtCore import Qt
from .annotation_widget import AnnotationWidget
from .image_list_widget import ImageListWidget
from databricks import sql
from config import Config
from database.databricks_connecter import DatabricksConnector 

class MainWindow(QMainWindow):
    def __init__(self, user_manager, user_profile, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.user_profile = user_profile
        
        # Create Databricks connector
        self.db_connector = DatabricksConnector()
        
        # Pass db_connector to ImageListWidget
        self.image_list = ImageListWidget(self.db_connector)
        
        # Pass db_connector to AnnotationWidget
        self.annotation_widget = AnnotationWidget(
            db_connector=self.db_connector,
            user_profile=self.user_profile
        )

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Wound Annotation Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Setup status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Image list panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Initialize image_list with the Databricks connector
        self.image_list = ImageListWidget(self.db_connector)
        left_layout.addWidget(self.image_list)
        layout.addWidget(left_panel, 1)
        
        # Annotation widget - pass the Databricks connector
        self.annotation_widget = AnnotationWidget(
            db_connector=self.db_connector,
            user_profile=self.user_profile
        )
        layout.addWidget(self.annotation_widget, 3)
        
        # Connect signals
        self.image_list.image_selected.connect(self.annotation_widget.load_image)
        
        # Setup toolbar
        self.setup_toolbar()


    def setup_toolbar(self):
        toolbar = self.addToolBar("Main")

        # ✅ User info
        user_label = QLabel(f"User: {self.user_profile.full_name}")
        toolbar.addWidget(user_label)

        role_label = QLabel(f"Role: {self.user_profile.role}")
        toolbar.addWidget(role_label)

        toolbar.addSeparator()

        # ✅ Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.image_list.load_wound_list)  # ✅ `self.image_list` is now defined
        toolbar.addWidget(refresh_btn)

        toolbar.addSeparator()

        # ✅ Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout)
        toolbar.addWidget(logout_btn)

        
    def logout(self):
        reply = QMessageBox.question(
            self,
            'Logout',
            'Are you sure you want to logout?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.user_profile.session_token:
                self.user_manager.logout_user(self.user_profile.session_token)
            self.close()
            
    def closeEvent(self, event):
        if self.user_profile.session_token:
            self.user_manager.logout_user(self.user_profile.session_token)
        event.accept()
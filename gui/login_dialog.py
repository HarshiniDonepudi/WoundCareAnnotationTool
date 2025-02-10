from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt
from .register_dialog import RegisterDialog  # Import the registration dialog

class LoginDialog(QDialog):
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.user_profile = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Login - Wound Annotation Tool")
        self.setModal(True)
        layout = QVBoxLayout(self)
        
        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)
        
        # Password
        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.try_login)
        button_layout.addWidget(login_btn)
        
        register_btn = QPushButton("Register")
        register_btn.clicked.connect(self.open_register_dialog)
        button_layout.addWidget(register_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set default button and connect Enter key navigation.
        login_btn.setDefault(True)
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.try_login)
        
    def try_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password")
            return
            
        self.user_profile = self.user_manager.authenticate_user(username, password)
        if self.user_profile:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Invalid username or password")
            self.password_input.clear()
            self.password_input.setFocus()
            
    def open_register_dialog(self):
        # Create and show the registration dialog.
        dialog = RegisterDialog(self.user_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            # If registration is successful, store the user profile and accept the dialog.
            self.user_profile = dialog.user_profile
            self.accept()

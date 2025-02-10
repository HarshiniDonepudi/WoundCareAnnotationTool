# register_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox
from PyQt5.QtCore import Qt

class RegisterDialog(QDialog):
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.user_profile = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Register New User")
        self.setModal(True)
        layout = QVBoxLayout(self)
        
        # Full Name
        full_name_layout = QHBoxLayout()
        full_name_label = QLabel("Full Name:")
        self.full_name_input = QLineEdit()
        full_name_layout.addWidget(full_name_label)
        full_name_layout.addWidget(self.full_name_input)
        layout.addLayout(full_name_layout)
        
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
        
        # Confirm Password
        confirm_layout = QHBoxLayout()
        confirm_label = QLabel("Confirm Password:")
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        confirm_layout.addWidget(confirm_label)
        confirm_layout.addWidget(self.confirm_input)
        layout.addLayout(confirm_layout)
        
        # Role Selection
        role_layout = QHBoxLayout()
        role_label = QLabel("Role:")
        self.role_combo = QComboBox()
        # Add role options: "annotator" and "admin"
        self.role_combo.addItems(["annotator", "admin"])
        role_layout.addWidget(role_label)
        role_layout.addWidget(self.role_combo)
        layout.addLayout(role_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        register_btn = QPushButton("Register")
        register_btn.clicked.connect(self.register_user)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(register_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # Set default button and connect Enter key navigation.
        register_btn.setDefault(True)
        self.full_name_input.returnPressed.connect(self.username_input.setFocus)
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.confirm_input.setFocus)
        self.confirm_input.returnPressed.connect(self.register_user)
        
    def register_user(self):
        full_name = self.full_name_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_input.text()
        role = self.role_combo.currentText()
        
        if not full_name or not username or not password or not confirm_password:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            self.password_input.clear()
            self.confirm_input.clear()
            self.password_input.setFocus()
            return
        
        # Attempt to create a new user with the selected role.
        new_user = self.user_manager.create_user(username, password, full_name, role=role)
        if new_user:
            QMessageBox.information(self, "Success", "User registered successfully.")
            self.user_profile = new_user
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Username already exists or an error occurred.")
            self.username_input.setFocus()

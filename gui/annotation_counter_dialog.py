# annotation_counter_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

class AnnotationCounterDialog(QDialog):
    def __init__(self, db_connector, parent=None):
        super().__init__(parent)
        self.db_connector = db_connector
        self.setWindowTitle("Total Annotation Counter")
        self.resize(400, 300)
        # Set the window flags to make it a floating, modeless tool window.
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setup_ui()
        self.load_counts()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.count_label = QLabel("Loading counts...", self)
        self.count_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.count_label)
        
        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def load_counts(self):
        try:
            if not self.db_connector.connection:
                self.db_connector.connect()
            cursor = self.db_connector.connection.cursor()
            # Query to aggregate annotation counts by category.
            query = """
                SELECT category, COUNT(*) 
                FROM wcr_wound_detection.wcr_wound.wound_annotations 
                GROUP BY category
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            if results:
                counts_text = "\n".join(f"{row[0]}: {row[1]}" for row in results)
            else:
                counts_text = "No annotations found."
                
            self.count_label.setText(counts_text)
        except Exception as e:
            self.count_label.setText(f"Error loading counts: {str(e)}")

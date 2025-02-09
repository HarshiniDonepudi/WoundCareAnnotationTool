# main.py
import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from database.connection_manager import DatabaseConnectionManager
from database.user_manager import UserManager
from gui.login_dialog import LoginDialog
from gui.main_window import MainWindow
import logging
from datetime import datetime

# Setup logging
def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class WoundAnnotationApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.logger = setup_logging()
        self.db_manager = None
        self.user_manager = None
        self.main_window = None
        
    def initialize_database(self):
        """Initialize database connection"""
        try:
            self.db_manager = DatabaseConnectionManager()
            self.db_manager.get_connector().connect()
            self.user_manager = UserManager(self.db_manager.get_connector())
            return True
        except Exception as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
            QMessageBox.critical(None, "Error", 
                               "Failed to connect to database. Please check your connection settings.")
            return False
            
    def show_splash_screen(self):
        """Show splash screen while loading"""
        splash_pix = QPixmap("resources/splash.png")
        if splash_pix.isNull():
            # If splash image not found, create a basic splash screen
            splash_pix = QPixmap(400, 200)
            splash_pix.fill(Qt.white)
            
        splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        splash.show()
        splash.showMessage("Connecting to database...", 
                         Qt.AlignBottom | Qt.AlignCenter, 
                         Qt.black)
        self.app.processEvents()
        
        return splash
        
    def show_login(self):
        """Show login dialog"""
        login_dialog = LoginDialog(self.user_manager)
        if login_dialog.exec_() == LoginDialog.Accepted:
            return login_dialog.user_profile
        return None
        
    def run(self):
        """Run the application"""
        try:
            # Show splash screen
            splash = self.show_splash_screen()
            
            # Initialize database
            if not self.initialize_database():
                return 1
                
            splash.showMessage("Database connected. Loading application...", 
                             Qt.AlignBottom | Qt.AlignCenter, 
                             Qt.black)
                             
            # Show login dialog
            user_profile = self.show_login()
            if not user_profile:
                self.logger.info("Login cancelled by user")
                return 0
                
            # Create and show main window
            self.main_window = MainWindow(self.db_manager.get_connector(), user_profile)
            self.main_window.show()
            
            # Close splash screen
            splash.finish(self.main_window)
            
            # Start event loop
            return self.app.exec_()
            
        except Exception as e:
            self.logger.error(f"Application error: {str(e)}")
            QMessageBox.critical(None, "Error", 
                               f"An unexpected error occurred: {str(e)}")
            return 1
            
        finally:
            # Cleanup
            if self.db_manager:
                self.db_manager.close_connection()

def main():
    """Main entry point"""
    app = WoundAnnotationApp()
    return app.run()

if __name__ == "__main__":
    # Add the current directory to Python path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the application
    sys.exit(main())
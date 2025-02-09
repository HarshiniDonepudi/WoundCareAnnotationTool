from PIL import Image
from io import BytesIO
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

class ImageHandler:
    @staticmethod
    def decode_image_content(image_data: bytes) -> QPixmap:
        """
        Convert binary image data to QPixmap for display
        Args:
            image_data: Binary image data from database
        Returns:
            QPixmap object for display
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Convert to numpy array
            img_array = np.array(image)
            height, width, channels = img_array.shape
            
            # Create QImage from numpy array
            bytes_per_line = channels * width
            q_img = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            return QPixmap.fromImage(q_img)
            
        except Exception as e:
            print(f"Error decoding image: {str(e)}")
            return None

    @staticmethod
    def resize_pixmap(pixmap: QPixmap, max_size: int = 800) -> QPixmap:
        """
        Resize pixmap while maintaining aspect ratio
        Args:
            pixmap: Input QPixmap
            max_size: Maximum size for width or height
        Returns:
            Resized QPixmap
        """
        if pixmap.width() > max_size or pixmap.height() > max_size:
            return pixmap.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pixmap

    @staticmethod
    def convert_to_grayscale(pixmap: QPixmap) -> QPixmap:
        """Convert image to grayscale"""
        image = pixmap.toImage()
        grayscale = image.convertToFormat(QImage.Format_Grayscale8)
        return QPixmap.fromImage(grayscale)

    @staticmethod
    def adjust_brightness_contrast(pixmap: QPixmap, brightness: float = 1.0, contrast: float = 1.0) -> QPixmap:
        """
        Adjust image brightness and contrast
        Args:
            pixmap: Input QPixmap
            brightness: Brightness factor (1.0 = no change)
            contrast: Contrast factor (1.0 = no change)
        Returns:
            Adjusted QPixmap
        """
        try:
            # Convert QPixmap to PIL Image
            image = Image.fromqpixmap(pixmap)
            
            # Adjust brightness and contrast
            enhanced = image.point(lambda x: ((x - 128) * contrast + 128) * brightness)
            
            # Convert back to QPixmap
            return QPixmap.fromImage(QImage(enhanced.tobytes(), 
                                          enhanced.width, 
                                          enhanced.height, 
                                          QImage.Format_RGB888))
        except Exception as e:
            print(f"Error adjusting image: {str(e)}")
            return pixmap

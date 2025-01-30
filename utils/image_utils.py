
import base64
from io import BytesIO
from PIL import Image
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

class ImageHandler:
    @staticmethod
    def decode_image_content(content):
        """
        Decode image content that could be binary text or binary data
        """
        try:
            # If content is bytes, try direct image decoding first
            if isinstance(content, bytes):
                try:
                    return ImageHandler._decode_binary_image(content)
                except:
                    # If direct decoding fails, try converting to text
                    try:
                        text_content = content.decode('utf-8')
                        return ImageHandler._decode_binary_text_to_image(text_content)
                    except:
                        pass
            
            # If content is string, try binary text decoding
            elif isinstance(content, str):
                return ImageHandler._decode_binary_text_to_image(content)
            
            raise Exception("Unable to decode image content")
            
        except Exception as e:
            print(f"Error decoding image content: {str(e)}")
            return None

    @staticmethod
    def _decode_binary_image(binary_data):
        """Try to decode binary data directly as an image"""
        try:
            # Try to detect image format and decode
            image = None
            
            # Try different image formats
            for format_handler in [
                ImageHandler._try_decode_png,
                ImageHandler._try_decode_jpeg,
                ImageHandler._try_decode_raw
            ]:
                try:
                    image = format_handler(binary_data)
                    if image:
                        break
                except:
                    continue
            
            if not image:
                raise Exception("Unable to decode binary as image")
            
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
            print(f"Error decoding binary image: {str(e)}")
            raise

    @staticmethod
    def _decode_binary_text_to_image(binary_text):
        """Decode binary text (computer code representation) to a QPixmap"""
        try:
            # Convert binary text to actual binary data
            binary_data = b''
            # Remove any whitespace and newlines
            binary_text = binary_text.replace(" ", "").replace("\n", "")
            
            # Try to convert hexadecimal first
            try:
                binary_data = bytes.fromhex(binary_text)
            except ValueError:
                # If not hex, try binary
                try:
                    # Convert binary text to bytes
                    for i in range(0, len(binary_text), 8):
                        byte = binary_text[i:i+8]
                        if len(byte) == 8:  # Ensure we have a full byte
                            binary_data += bytes([int(byte, 2)])
                except:
                    raise Exception("Unable to parse binary text")
            
            return ImageHandler._decode_binary_image(binary_data)
            
        except Exception as e:
            print(f"Error decoding binary text: {str(e)}")
            raise

    @staticmethod
    def _try_decode_png(binary_data):
        """Try to decode as PNG"""
        png_signature = b'\x89PNG\r\n\x1a\n'
        if png_signature in binary_data:
            start_idx = binary_data.index(png_signature)
            image_data = binary_data[start_idx:]
            return Image.open(BytesIO(image_data))
        return None

    @staticmethod
    def _try_decode_jpeg(binary_data):
        """Try to decode as JPEG"""
        jpeg_signature = b'\xff\xd8'
        if jpeg_signature in binary_data:
            start_idx = binary_data.index(jpeg_signature)
            image_data = binary_data[start_idx:]
            return Image.open(BytesIO(image_data))
        return None

    @staticmethod
    def _try_decode_raw(binary_data):
        """Try to decode as raw pixel data"""
        try:
            # Try several common image dimensions
            dimensions = [(256, 256), (512, 512), (1024, 1024)]
            for width, height in dimensions:
                try:
                    image = Image.frombytes('RGB', (width, height), binary_data)
                    return image
                except:
                    continue
            return None
        except:
            return None

    @staticmethod
    def resize_pixmap(pixmap, max_size=800):
        """Resize pixmap while maintaining aspect ratio"""
        if pixmap.width() > max_size or pixmap.height() > max_size:
            return pixmap.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pixmap
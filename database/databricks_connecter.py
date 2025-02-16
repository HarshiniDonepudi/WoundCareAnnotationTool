from databricks import sql
from config import Config
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import json
import uuid

@dataclass
class WoundInfo:
    wound_assessment_id: int
    wound_type: str
    body_location: str
    patient_id: Optional[str] = None        
    image_data: Optional[bytes] = None
    path: Optional[str] = None
    annotations: Optional[Dict[str, Any]] = None
    
class DatabricksConnector:
    def __init__(self):
        self.connection = None
        
    def connect(self):
        """Establish connection to Databricks"""
        try:
            self.connection = sql.connect(
                server_hostname=Config.DATABRICKS_HOST,
                http_path=Config.DATABRICKS_HTTP_PATH,
                access_token=Config.DATABRICKS_TOKEN
            )
            print("Successfully connected to Databricks")
        except Exception as e:
            print(f"Error connecting to Databricks: {str(e)}")
            raise

    def get_image_by_path(self, image_path: str) -> Optional[bytes]:
        """Fetch image data from images table using path"""
        try:
            if not self.connection:
                self.connect()

            query = f"""
            SELECT content 
            FROM wcr_wound_detection.wcr_wound.wcr_annotation_initial
            WHERE path = '{image_path}'
            """
            
            print(f"Executing image query: {query}")
            cursor = self.connection.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()

            if result and result[0]:
                return result[0]  # Return binary image data
            return None

        except Exception as e:
            print(f"Error fetching image: {str(e)}")
            return None
    
    def get_wound_assessment(self, assessment_id: str) -> Optional[WoundInfo]:
        try:
            if not self.connection:
                self.connect()
                    
            assessment_id_int = int(assessment_id)
                
            query = f"""
            SELECT 
                WoundAssessmentID,
                WoundType,
                WoundLocationLocation,
                PatientID,             
                path
            FROM wcr_wound_detection.wcr_wound.wcr_annotation_initial
            WHERE WoundAssessmentID = {assessment_id_int}
            """
            print(f"Executing wound query: {query}")
            cursor = self.connection.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
                
            if result:
                image_path = result[4]
                image_data = self.get_image_by_path(image_path)
                    
                return WoundInfo(
                    wound_assessment_id=result[0],
                    wound_type=result[1] if result[1] else "Unknown",
                    body_location=result[2] if result[2] else "Unknown",
                    patient_id=result[3],  # Set patient id here
                    image_data=image_data,
                    path=image_path,
                    annotations=None
                )
            return None
        except Exception as e:
            print(f"Error fetching wound assessment: {str(e)}")
            return None


    def create_annotations_table(self):
        """Create annotations table if it doesn't exist"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS wcr_wound_detection.wcr_wound.wound_annotations (
                annotation_id STRING,
                wound_assessment_id BIGINT,
                category STRING,
                location STRING,
                body_map_id STRING,
                x INT,
                y INT,
                width INT,
                height INT,
                created_by STRING,
                created_at TIMESTAMP,
                last_modified_by STRING,
                last_modified_at TIMESTAMP,
                PRIMARY KEY (annotation_id)
            )
            """
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            cursor.close()
        except Exception as e:
            print(f"Error creating annotations table: {str(e)}")
            raise

    

    def get_annotations(self, wound_assessment_id: int) -> Optional[Dict]:
        """Get all annotations for a wound assessment"""
        try:
            query = f"""
            SELECT *
            FROM wcr_wound_detection.wcr_wound.wound_annotations
            WHERE wound_assessment_id = {wound_assessment_id}
            ORDER BY created_at
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            if results:
                annotations = {
                    'boxes': [{
                        'annotation_id': row[0],
                        'category': row[2],
                        'location': row[3],
                        'body_map_id': row[4],
                        'x': row[5],
                        'y': row[6],
                        'width': row[7],
                        'height': row[8],
                        'created_by': row[9],
                        'created_at': row[10].isoformat() if row[10] else None,
                        'last_modified_by': row[11],
                        'last_modified_at': row[12].isoformat() if row[12] else None
                    } for row in results]
                }
                return annotations
                
            return None
            
        except Exception as e:
            print(f"Error fetching annotations: {str(e)}")
            return None

    def save_annotations(self, wound_assessment_id: int, annotations: list) -> bool:
        """Save annotations to database"""
        try:
            if not self.connection:
                self.connect()

            cursor = self.connection.cursor()
            
            # First, delete existing annotations for this wound assessment.
            delete_query = f"""
            DELETE FROM wcr_wound_detection.wcr_wound.wound_annotations
            WHERE wound_assessment_id = {wound_assessment_id}
            """
            cursor.execute(delete_query)
            
            # Use a raw string literal with %s placeholders.
            insert_query = r"""
            INSERT INTO wcr_wound_detection.wcr_wound.wound_annotations (
                annotation_id, wound_assessment_id, category, location, body_map_id,
                x, y, width, height, created_by, created_at, last_modified_by, last_modified_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for annotation in annotations:
                # Debug print the parameters to verify their types:
                params = (
                    str(uuid.uuid4()),
                    wound_assessment_id,
                    annotation['category'],
                    annotation['location'],
                    annotation.get('body_map_id', ''),
                    annotation['x'],
                    annotation['y'],
                    annotation['width'],
                    annotation['height'],
                    annotation['created_by'],
                    annotation['created_at'],       # Pass as ISO string or as a datetime object if supported.
                    annotation['last_modified_by'],
                    annotation['last_modified_at']    # Same note as above.
                )
                print("Executing query with parameters:", params)
                cursor.execute(insert_query, params)
            
            self.connection.commit()
            cursor.close()
            return True
            
        except Exception as e:
            print(f"Error saving annotations: {str(e)}")
            return False



    def get_all_wound_paths(self) -> list:
        """Get all unique image paths"""
        try:
            if not self.connection:
                self.connect()

            query = """
            SELECT DISTINCT path 
            FROM wcr_wound_detection.wcr_wound.wcr_annotation_initial
            ORDER BY path
            """

            cursor = self.connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            return [row[0] for row in results]

        except Exception as e:
            print(f"Error fetching image paths: {str(e)}")
            return []

    def get_wound_types(self) -> list:
        """Get all unique wound types"""
        try:
            if not self.connection:
                self.connect()

            query = """
            SELECT DISTINCT WoundType 
            FROM wcr_wound_detection.wcr_wound.wcr_annotation_initial
            WHERE WoundType IS NOT NULL
            ORDER BY WoundType
            """

            cursor = self.connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            return [row[0] for row in results]

        except Exception as e:
            print(f"Error fetching wound types: {str(e)}")
            return []

    def get_body_locations(self) -> list:
        """Get all unique body locations"""
        try:
            if not self.connection:
                self.connect()

            query = """
            SELECT DISTINCT WoundLocationLocation 
            FROM wcr_wound_detection.wcr_wound.wcr_annotation_initial
            WHERE WoundLocationLocation IS NOT NULL
            ORDER BY WoundLocationLocation
            """

            cursor = self.connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            return [row[0] for row in results]

        except Exception as e:
            print(f"Error fetching body locations: {str(e)}")
            return []

    def close(self):
        """Close the Databricks connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
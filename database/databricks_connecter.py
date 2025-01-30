from databricks import sql
from config import Config
from dataclasses import dataclass
from typing import Optional

@dataclass
class WoundInfo:
    wound_assessment_id: int
    wound_type: str
    body_location: str
    body_map_id: Optional[str] = None

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
    
    def get_wound_assessment(self, assessment_id: str) -> Optional[WoundInfo]:
        """
        Fetch wound assessment information from Databricks
        assessment_id: The ID extracted from image filename
        """
        try:
            if not self.connection:
                self.connect()
                
            # Convert assessment_id to integer
            assessment_id_int = int(assessment_id)
            
            query = f"""
            SELECT 
                WoundAssessmentID,
                WoundType,
                WoundLocationLocation
            FROM wcr_wound_detection.wcr_wound.joined_wound_assessments
            WHERE WoundAssessmentID = {assessment_id_int}
            """
            
            print(f"Executing query: {query}")  # Debug print
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return WoundInfo(
                    wound_assessment_id=result[0],
                    wound_type=result[1],
                    body_location=result[2]
                )
            else:
                print(f"No wound information found for assessment ID: {assessment_id_int}")
                return None
                
        except Exception as e:
            print(f"Error fetching wound assessment: {str(e)}")
            return None
        
    def close(self):
        """Close the Databricks connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
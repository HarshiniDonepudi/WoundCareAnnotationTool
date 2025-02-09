from .databricks_connecter import DatabricksConnector

class DatabaseConnectionManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnectionManager, cls).__new__(cls)
            cls._instance.connector = DatabricksConnector()
        return cls._instance
    
    def get_connector(self):
        return self.connector
    
    def close_connection(self):
        if self.connector:
            self.connector.close()
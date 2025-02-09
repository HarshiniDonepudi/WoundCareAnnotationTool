# database/user_manager.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict
import hashlib
import uuid
import jwt
import time

@dataclass
class UserProfile:
    user_id: str
    username: str
    full_name: str
    role: str
    last_login: Optional[datetime] = None
    session_token: Optional[str] = None

class UserManager:
    def __init__(self, db_connector):
        self.db = db_connector
        self.active_sessions: Dict[str, str] = {}  # session_token -> user_id
        self.SECRET_KEY = "your_secret_key"  # In production, use secure key from environment variables
        
    def create_user_table(self):
        """Create users table if it doesn't exist"""
        try:
            if not self.db.connection:
                self.db.connect()
                
            query = """
            CREATE TABLE IF NOT EXISTS wcr_wound_detection.wcr_wound.users (
                user_id STRING,
                username STRING,
                password_hash STRING,
                full_name STRING,
                role STRING,
                created_at TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN,
                PRIMARY KEY (user_id)
            )
            """
            
            cursor = self.db.connection.cursor()
            cursor.execute(query)
            self.db.connection.commit()
            cursor.close()
            
        except Exception as e:
            print(f"Error creating users table: {str(e)}")
            raise

    def create_user(self, username: str, password: str, full_name: str, role: str = "annotator") -> Optional[UserProfile]:
        """Create a new user"""
        try:
            if not self.db.connection:
                self.db.connect()

            # Check if username exists
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT 1 FROM wcr_wound_detection.wcr_wound.users WHERE username = ?", (username,))
            if cursor.fetchone():
                print(f"Username {username} already exists")
                return None

            # Generate user_id and hash password
            user_id = str(uuid.uuid4())
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            current_time = datetime.now()

            # Insert new user
            query = """
            INSERT INTO wcr_wound_detection.wcr_wound.users 
            (user_id, username, password_hash, full_name, role, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, TRUE)
            """
            
            cursor.execute(query, (user_id, username, password_hash, full_name, role, current_time))
            self.db.connection.commit()
            cursor.close()

            return UserProfile(
                user_id=user_id,
                username=username,
                full_name=full_name,
                role=role
            )

        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[UserProfile]:
        """Authenticate user and create session"""
        try:
            if not self.db.connection:
                self.db.connect()

            # Get user information
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            query = """
            SELECT user_id, full_name, role, last_login 
            FROM wcr_wound_detection.wcr_wound.users
            WHERE username = '{username}' AND password_hash = '{password_hash}' AND is_active = TRUE
            """.format(username=username, password_hash=password_hash)

            cursor = self.db.connection.cursor()
            
            # Debug: Print out query details
            print(f"Executing query: {query}")

            try:
                # Use formatted query for Databricks
                cursor.execute(query)
                result = cursor.fetchone()
                
                # Debugging for no result
                if result is None:
                    print("No user found. Checking username existence...")
                    
                    # Check if username exists
                    exist_query = """
                    SELECT 1 
                    FROM wcr_wound_detection.wcr_wound.users 
                    WHERE username = '{username}'
                    """.format(username=username)
                    cursor.execute(exist_query)
                    username_exists = cursor.fetchone()
                    
                    if username_exists:
                        print("Username exists, but password is incorrect")
                    else:
                        print("Username does not exist in the database")
                    
                    cursor.close()
                    return None

                # Rest of the authentication process remains the same
                current_time = datetime.now()
                update_query = """
                UPDATE wcr_wound_detection.wcr_wound.users
                SET last_login = '{current_time}'
                WHERE user_id = '{user_id}'
                """.format(current_time=current_time, user_id=result[0])
                
                cursor.execute(update_query)
                self.db.connection.commit()

                # Create session token
                session_token = self.create_session_token(result[0])

                user = UserProfile(
                    user_id=result[0],
                    username=username,
                    full_name=result[1],
                    role=result[2],
                    last_login=current_time,
                    session_token=session_token
                )

                # Store session
                self.active_sessions[session_token] = user.user_id

                cursor.close()
                return user

            except Exception as e:
                print(f"Detailed query execution error: {str(e)}")
                cursor.close()
                return None

        except Exception as e:
            print(f"Error authenticating user: {str(e)}")
            return None

    def create_session_token(self, user_id: str) -> str:
        """Create JWT session token"""
        payload = {
            'user_id': user_id,
            'exp': int(time.time()) + 86400,  # 24 hour expiration
            'iat': int(time.time())
        }
        return jwt.encode(payload, self.SECRET_KEY, algorithm='HS256')

    def validate_session(self, session_token: str) -> Optional[UserProfile]:
        """Validate session token and return user profile"""
        try:
            if session_token not in self.active_sessions:
                return None

            # Decode and validate token
            try:
                payload = jwt.decode(session_token, self.SECRET_KEY, algorithms=['HS256'])
                user_id = payload['user_id']
            except jwt.ExpiredSignatureError:
                self.logout_user(session_token)
                return None
            except jwt.InvalidTokenError:
                return None

            # Get user information
            query = """
            SELECT username, full_name, role, last_login 
            FROM wcr_wound_detection.wcr_wound.users
            WHERE user_id = ? AND is_active = TRUE
            """

            cursor = self.db.connection.cursor()
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            cursor.close()

            if result:
                return UserProfile(
                    user_id=user_id,
                    username=result[0],
                    full_name=result[1],
                    role=result[2],
                    last_login=result[3],
                    session_token=session_token
                )

            return None

        except Exception as e:
            print(f"Error validating session: {str(e)}")
            return None

    def logout_user(self, session_token: str):
        """Log out user by removing session"""
        if session_token in self.active_sessions:
            del self.active_sessions[session_token]

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            if not self.db.connection:
                self.db.connect()

            # Verify old password
            old_hash = hashlib.sha256(old_password.encode()).hexdigest()
            new_hash = hashlib.sha256(new_password.encode()).hexdigest()

            query = """
            UPDATE wcr_wound_detection.wcr_wound.users
            SET password_hash = ?
            WHERE user_id = ? AND password_hash = ?
            """

            cursor = self.db.connection.cursor()
            cursor.execute(query, (new_hash, user_id, old_hash))
            success = cursor.rowcount > 0
            self.db.connection.commit()
            cursor.close()

            return success

        except Exception as e:
            print(f"Error changing password: {str(e)}")
            return False

    def update_user_role(self, user_id: str, new_role: str) -> bool:
        """Update user role"""
        try:
            if not self.db.connection:
                self.db.connect()

            query = """
            UPDATE wcr_wound_detection.wcr_wound.users
            SET role = ?
            WHERE user_id = ?
            """

            cursor = self.db.connection.cursor()
            cursor.execute(query, (new_role, user_id))
            success = cursor.rowcount > 0
            self.db.connection.commit()
            cursor.close()

            return success

        except Exception as e:
            print(f"Error updating user role: {str(e)}")
            return False

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account"""
        try:
            if not self.db.connection:
                self.db.connect()

            query = """
            UPDATE wcr_wound_detection.wcr_wound.users
            SET is_active = FALSE
            WHERE user_id = ?
            """

            cursor = self.db.connection.cursor()
            cursor.execute(query, (user_id,))
            success = cursor.rowcount > 0
            self.db.connection.commit()
            cursor.close()

            # Remove any active sessions for this user
            for token, uid in list(self.active_sessions.items()):
                if uid == user_id:
                    del self.active_sessions[token]

            return success

        except Exception as e:
            print(f"Error deactivating user: {str(e)}")
            return False
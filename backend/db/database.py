import os
from typing import Any, Dict, List, Optional

import mysql.connector
from mysql.connector import Error, pooling


class Database:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "3306"))
        self.database = os.getenv("DB_NAME", "havana_dev")
        self.user = os.getenv("DB_USER", "admin")
        self.password = os.getenv("DB_PASSWORD", "password")
        self.connection_pool = None

    def connect(self):
        """Establish database connection pool"""
        try:
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name="havana_pool",
                pool_size=5,
                pool_reset_session=True,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
            )
            print(f"Successfully created connection pool to MySQL database: {self.database}")
            return True
        except Error as e:
            print(f"Error creating connection pool: {e}")
            return False

    def disconnect(self):
        """Close database connection pool"""
        if self.connection_pool:
            # Connection pools don't have a close method, connections are automatically managed
            self.connection_pool = None
            print("MySQL connection pool closed")

    def _get_connection(self):
        """Get a connection from the pool"""
        if not self.connection_pool:
            raise Exception("Connection pool not initialized")
        return self.connection_pool.get_connection()

    def execute_query(self, query: str, params: tuple = None) -> bool:
        """Execute a query that doesn't return results (INSERT, UPDATE, DELETE)"""
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            connection.commit()
            return True
        except Error as e:
            print(f"Error executing query: {e}")
            if connection:
                connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Fetch a single row"""
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Error fetching data: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def fetch_all(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Fetch all rows"""
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            return results
        except Error as e:
            print(f"Error fetching data: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_last_insert_id(self, connection) -> Optional[int]:
        """Get the last inserted ID from a given connection"""
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT LAST_INSERT_ID()")
            result = cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            print(f"Error getting last insert ID: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    # Chat operations
    def create_chat(self) -> Optional[int]:
        """Create a new chat and return its ID"""
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            query = "INSERT INTO chats (is_human_enabled) VALUES (FALSE)"
            cursor.execute(query)
            connection.commit()
            last_id = self.get_last_insert_id(connection)
            return last_id
        except Error as e:
            print(f"Error creating chat: {e}")
            if connection:
                connection.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_all_chats(self) -> List[Dict[str, Any]]:
        """Get all non-deleted chats"""
        query = """
            SELECT id, is_human_enabled, created_at
            FROM chats
            WHERE deleted_at IS NULL
            ORDER BY created_at DESC
        """
        return self.fetch_all(query)

    def get_chat_by_id(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific chat by ID"""
        query = """
            SELECT id, is_human_enabled, created_at
            FROM chats
            WHERE id = %s AND deleted_at IS NULL
        """
        return self.fetch_one(query, (chat_id,))

    def update_chat_human_enabled(self, chat_id: int, is_enabled: bool) -> bool:
        """Update the is_human_enabled flag for a chat"""
        query = """
            UPDATE chats
            SET is_human_enabled = %s
            WHERE id = %s AND deleted_at IS NULL
        """
        return self.execute_query(query, (is_enabled, chat_id))

    # Chat history operations
    def add_message(self, chat_id: int, role: str, message: str) -> bool:
        """Add a message to chat history"""
        query = """
            INSERT INTO chat_history (chat_id, role, message)
            VALUES (%s, %s, %s)
        """
        return self.execute_query(query, (chat_id, role, message))

    def get_chat_history(self, chat_id: int) -> List[Dict[str, Any]]:
        """Get all messages for a chat"""
        query = """
            SELECT id, chat_id, role, message, created_at
            FROM chat_history
            WHERE chat_id = %s AND deleted_at IS NULL
            ORDER BY created_at ASC
        """
        return self.fetch_all(query, (chat_id,))

    # Booking operations
    def get_available_bookings(self) -> List[Dict[str, Any]]:
        """Get all available booking slots (where chat_id is NULL)"""
        query = """
            SELECT id, date, time
            FROM bookings
            WHERE chat_id IS NULL AND deleted_at IS NULL AND date >= CURDATE()
            ORDER BY date ASC, time ASC
        """
        return self.fetch_all(query)

    def book_slot(self, booking_id: int, chat_id: int) -> bool:
        """Book a slot for a chat"""
        query = """
            UPDATE bookings
            SET chat_id = %s
            WHERE id = %s AND chat_id IS NULL AND deleted_at IS NULL
        """
        return self.execute_query(query, (chat_id, booking_id))

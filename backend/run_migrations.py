#!/usr/bin/env python3
"""
Database migration script for Havana University Chat Bot
Run this script to create tables and seed initial data
"""

import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

# Load environment variables
load_dotenv()


def run_migrations():
    """Execute all SQL migration files in order"""

    # Database connection parameters
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "3306"))
    database = os.getenv("DB_NAME", "havana_dev")
    user = os.getenv("DB_USER", "admin")
    password = os.getenv("DB_PASSWORD", "password")

    print(f"Connecting to MySQL database: {database}")

    try:
        # Connect to MySQL
        connection = mysql.connector.connect(host=host, port=port, database=database, user=user, password=password)

        if connection.is_connected():
            print("Successfully connected to MySQL database")
            cursor = connection.cursor()

            # List of migration files in order
            migration_files = [
                "db/migrations/001_create_chats_table.sql",
                "db/migrations/002_create_chat_history_table.sql",
                "db/migrations/003_create_bookings_table.sql",
                "db/migrations/004_seed_booking_slots.sql",
            ]

            # Execute each migration file
            for migration_file in migration_files:
                print(f"\nExecuting migration: {migration_file}")

                try:
                    with open(migration_file, "r") as file:
                        sql_script = file.read()

                        # Split by semicolon to handle multiple statements
                        statements = [stmt.strip() for stmt in sql_script.split(";") if stmt.strip()]

                        for statement in statements:
                            cursor.execute(statement)
                            connection.commit()

                        print(f"✓ Successfully executed {migration_file}")

                except FileNotFoundError:
                    print(f"✗ Migration file not found: {migration_file}")
                except Error as e:
                    print(f"✗ Error executing {migration_file}: {e}")

            cursor.close()
            connection.close()
            print("\n✓ All migrations completed successfully!")

    except Error as e:
        print(f"✗ Error connecting to MySQL: {e}")
        print("\nMake sure:")
        print("1. MySQL is running")
        print("2. Database exists (CREATE DATABASE havana_dev;)")
        print("3. User has proper permissions")
        print("4. .env file has correct credentials")


if __name__ == "__main__":
    run_migrations()

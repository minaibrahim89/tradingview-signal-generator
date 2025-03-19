"""
Script to update the database schema.
Run this script directly when you need to update the database schema.
"""
from app.models.database import initialize_db

if __name__ == "__main__":
    print("Updating database schema...")
    initialize_db()
    print("Database schema update complete.") 
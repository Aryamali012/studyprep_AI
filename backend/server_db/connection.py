"""
server_db/connection.py
MySQL database connection helper.

Schema is managed by schema.sql — run it once before starting the server:
    mysql -u root -p < schema.sql

Install driver:
    pip install mysql-connector-python
"""

import os
import mysql.connector

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "3306")),
    "user":     os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME",     "studyprep"),
}


def get_connection():
    """Return a new MySQL connection with autocommit off."""
    return mysql.connector.connect(**DB_CONFIG, autocommit=False)

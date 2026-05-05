"""
db.py:  Database connection layer.
All queries throughout the app go through get_connection().
Using psycopg2 with RealDictCursor so rows behave like dicts.
"""

import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "snickr"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgres"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
}


# Instead of writing this in every route we can use this function to get the connection.
def get_connection():
    """Return a new psycopg2 connection. Caller must close it."""
    return psycopg2.connect(**DB_CONFIG)


# It is used to access the database and return the results as a dictionary.
# I used RealDictCursor so query results can be accessed by column names instead of numeric indexes.
def dict_cursor(conn):
    """Return a RealDictCursor on the given connection."""
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

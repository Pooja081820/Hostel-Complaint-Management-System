"""
Hostel Complaint Management System (HCMS)
Database Access & Connection Pooling Layer (db.py)

Uses mysql-connector-python with MySQLConnectionPool for high-throughput,
leak-safe database interaction via context managers.
"""
import certifi
import time
import logging
from contextlib import contextmanager
import mysql.connector
from mysql.connector import pooling, errorcode
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global connection pool instance
_connection_pool = None

def init_db_pool():
    """Initializes the thread-safe MySQL connection pool."""
    global _connection_pool
    if _connection_pool is None:
        try:
            logger.info("Initializing MySQL connection pool [%s]...", Config.DB_POOL_NAME)
            _connection_pool = pooling.MySQLConnectionPool(
                pool_name=Config.DB_POOL_NAME,
                pool_size=Config.DB_POOL_SIZE,
                pool_reset_session=True,
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                ssl_ca=certifi.where(),
                 ssl_verify_cert=True,
                autocommit=False,  # Enforce explicit transaction control
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci"
            )
            logger.info("MySQL connection pool created successfully (size: %d).", Config.DB_POOL_SIZE)
        except mysql.connector.Error as err:
            logger.error("Failed to initialize MySQL pool: %s", err)
            raise err
    return _connection_pool

def get_pool():
    """Returns the active pool, creating it if needed."""
    global _connection_pool
    if _connection_pool is None:
        init_db_pool()
    return _connection_pool

@contextmanager
def get_db_connection():
    """
    Context manager yielding a connection from the pool.
    Guarantees that connections are cleanly returned to the pool upon exit.
    """
    pool = get_pool()
    conn = None
    try:
        conn = pool.get_connection()
        yield conn
    except mysql.connector.Error as err:
        logger.error("Database connection error: %s", err)
        if conn and conn.is_connected():
            conn.rollback()
        raise err
    finally:
        if conn and conn.is_connected():
            conn.close()  # Returns connection back to the pool

@contextmanager
def get_db_cursor(dictionary=True, commit=False):
    """
    Convenience context manager yielding (conn, cursor).
    Automatically commits if commit=True and no exception occurred;
    rolls back if an exception is raised.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=dictionary)
        try:
            yield conn, cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("Transaction rolled back due to error: %s", e)
            raise e
        finally:
            cursor.close()

# ----------------------------------------------------------------------------
# Helper Execution Utilities
# ----------------------------------------------------------------------------
def query_one(sql, params=None, dictionary=True):
    """Executes a parameterized SELECT query returning a single row."""
    with get_db_cursor(dictionary=dictionary) as (_, cursor):
        cursor.execute(sql, params or ())
        return cursor.fetchone()

def query_all(sql, params=None, dictionary=True):
    """Executes a parameterized SELECT query returning all matching rows."""
    with get_db_cursor(dictionary=dictionary) as (_, cursor):
        cursor.execute(sql, params or ())
        return cursor.fetchall()

def execute_dml(sql, params=None):
    """
    Executes a parameterized INSERT/UPDATE/DELETE query.
    Returns (affected_rows, last_inserted_id).
    """
    with get_db_cursor(commit=True) as (_, cursor):
        cursor.execute(sql, params or ())
        return cursor.rowcount, cursor.lastrowid

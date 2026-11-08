"""
Hostel Complaint Management System (HCMS)
Database Initialization & Verification Script (init_db.py)

Executes all DDL, Triggers, Stored Procedures, Views, and Seed Data scripts
using direct parameterized connections via mysql-connector-python.
"""

import os
import sys
import getpass
import mysql.connector
from mysql.connector import errorcode

# Load environment configuration if available
def load_env(env_path=".env"):
    config = {
        "DB_HOST": "localhost",
        "DB_PORT": "3306",
        "DB_USER": "root",
        "DB_PASSWORD": "",
        "DB_NAME": "hostel_complaint_db"
    }
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip().strip("'\"")
    return config

CONFIG = load_env()

def strip_comments(raw_sql):
    """Strips full-line SQL comments (-- and #) while preserving executable clauses."""
    clean_lines = []
    for line in raw_sql.splitlines():
        trimmed = line.strip()
        if not trimmed.startswith("--") and not trimmed.startswith("#"):
            clean_lines.append(line)
    return "\n".join(clean_lines).strip()

def split_sql_statements(content, delimiter=";"):
    """Splits SQL text by delimiter while strictly respecting quoted strings."""
    statements = []
    current = []
    in_single_quote = False
    in_double_quote = False
    escape = False
    
    i = 0
    n = len(content)
    delim_len = len(delimiter)
    
    while i < n:
        if not in_single_quote and not in_double_quote and content[i:i+delim_len] == delimiter:
            stmt = strip_comments("".join(current))
            if stmt:
                statements.append(stmt)
            current = []
            i += delim_len
            continue
            
        char = content[i]
        if char == "'" and not in_double_quote and not escape:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote and not escape:
            in_double_quote = not in_double_quote
            
        if char == '\\' and not escape:
            escape = True
        else:
            escape = False
            
        current.append(char)
        i += 1
        
    leftover = strip_comments("".join(current))
    if leftover:
        statements.append(leftover)
        
    return statements

def execute_sql_file(cursor, file_path, multi=False):
    """Executes SQL statements from a file with support for DELIMITER blocks."""
    print(f"[*] Executing {os.path.basename(file_path)}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Handle MySQL DELIMITER blocks properly for procedures & triggers
    if "DELIMITER $$" in content:
        parts = content.split("DELIMITER $$")
        for stmt in split_sql_statements(parts[0], ";"):
            cursor.execute(stmt)
        
        for part in parts[1:]:
            subparts = part.split("DELIMITER ;")
            for sub_stmt in split_sql_statements(subparts[0], "$$"):
                cursor.execute(sub_stmt)
            if len(subparts) > 1:
                for after_stmt in split_sql_statements(subparts[1], ";"):
                    cursor.execute(after_stmt)
    else:
        for stmt in split_sql_statements(content, ";"):
            cursor.execute(stmt)

def main():
    print("=" * 70)
    print(" HOSTEL COMPLAINT MANAGEMENT SYSTEM - DATABASE INITIALIZER")
    print("=" * 70)

    host = os.environ.get("DB_HOST", CONFIG["DB_HOST"])
    port = int(os.environ.get("DB_PORT", CONFIG["DB_PORT"]))
    user = os.environ.get("DB_USER", CONFIG["DB_USER"])
    password = os.environ.get("DB_PASSWORD", CONFIG["DB_PASSWORD"])

    # If password is empty and in interactive terminal, prompt or use empty
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print(f"[!] Access Denied for user '{user}' with current password.")
            print("    Please set DB_PASSWORD in your .env file or environment.")
            if sys.stdin.isatty():
                password = getpass.getpass("Enter MySQL password for user 'root': ")
                conn = mysql.connector.connect(host=host, port=port, user=user, password=password)
            else:
                sys.exit(1)
        else:
            print(f"[!] Database Connection Error: {err}")
            sys.exit(1)

    cursor = conn.cursor()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(base_dir, "database")

    files_to_run = [
        os.path.join(db_dir, "schema.sql"),
        os.path.join(db_dir, "triggers.sql"),
        os.path.join(db_dir, "procedures.sql"),
        os.path.join(db_dir, "views.sql"),
        os.path.join(db_dir, "seed.sql")
    ]

    for file_path in files_to_run:
        if not os.path.exists(file_path):
            print(f"[!] Missing required SQL file: {file_path}")
            sys.exit(1)
        execute_sql_file(cursor, file_path)

    conn.commit()

    # Verification Query & Table Statistics Summary
    cursor.execute("USE `hostel_complaint_db`;")
    tables = [
        "users", "hostels", "rooms", "students", "wardens", "staff",
        "hostel_wardens", "complaint_categories", "complaints",
        "complaint_affected_hostels", "complaint_assignments",
        "complaint_responses", "complaint_history", "complaint_priority_history",
        "complaint_attachments", "notifications", "complaint_feedback", "audit_logs"
    ]

    print("\n" + "=" * 70)
    print(f"{'TABLE NAME':<35} | {'RECORD COUNT':>15}")
    print("-" * 70)
    total_records = 0
    for tbl in tables:
        cursor.execute(f"SELECT COUNT(*) FROM `{tbl}`;")
        count = cursor.fetchone()[0]
        total_records += count
        print(f"{tbl:<35} | {count:>15}")
    print("-" * 70)
    print(f"{'TOTAL SEEDED RECORDS':<35} | {total_records:>15}")
    print("=" * 70)

    # Verify Views
    cursor.execute("SELECT COUNT(*) FROM `vw_complaint_full_details`;")
    view_count = cursor.fetchone()[0]
    print(f"[✓] Verification: vw_complaint_full_details returned {view_count} aggregated rows.")

    cursor.close()
    conn.close()
    print("\n[SUCCESS] Hostel Complaint Database successfully initialized and seeded!\n")

if __name__ == "__main__":
    main()

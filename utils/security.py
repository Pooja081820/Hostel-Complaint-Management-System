"""
Hostel Complaint Management System (HCMS)
Security & Cryptography Utilities (utils/security.py)
"""

import os
import re
import secrets
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import session, request, abort
from config import Config

def hash_password(plain_password: str) -> str:
    """Generates a secure cryptographic password hash using Werkzeug (scrypt/pbkdf2)."""
    return generate_password_hash(plain_password, method="scrypt")

def verify_password(stored_hash: str, candidate_password: str) -> bool:
    """Verifies a plaintext password against the stored cryptographic hash."""
    return check_password_hash(stored_hash, candidate_password)

def generate_csrf_token() -> str:
    """Generates a cryptographically strong CSRF token and binds it to the user session."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]

def validate_csrf_token(token: str) -> bool:
    """Validates the candidate CSRF token against the session token."""
    session_token = session.get("_csrf_token")
    if not session_token or not token:
        return False
    return secrets.compare_digest(session_token, token)

def allowed_file(filename: str) -> bool:
    """Verifies that the uploaded file extension is strictly within the allowed whitelist."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS

def save_uploaded_file(file_storage, subfolder="evidence") -> tuple:
    """
    Saves an uploaded file safely:
    - Generates a collision-resistant UUID filename
    - Prevents directory traversal attacks
    - Returns (saved_relative_path, original_filename, file_size_kb, mime_type)
    """
    if not file_storage or not file_storage.filename:
        return None, None, 0, None
    
    orig_name = secure_filename(file_storage.filename)
    ext = orig_name.rsplit(".", 1)[1].lower() if "." in orig_name else "dat"
    unique_name = f"{uuid.uuid4().hex}_{secrets.token_hex(4)}.{ext}"
    
    target_dir = os.path.join(Config.UPLOAD_FOLDER, subfolder)
    os.makedirs(target_dir, exist_ok=True)
    
    full_path = os.path.join(target_dir, unique_name)
    file_storage.save(full_path)
    
    file_size_kb = os.path.getsize(full_path) // 1024
    mime_type = file_storage.content_type or "application/octet-stream"
    relative_path = os.path.join(subfolder, unique_name).replace("\\", "/")
    
    return relative_path, orig_name, file_size_kb, mime_type

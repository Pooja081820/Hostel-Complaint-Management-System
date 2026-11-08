"""
Hostel Complaint Management System (HCMS)
Server-Side Input Validation Suite (utils/validators.py)
"""

import re

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^[0-9]{10,15}$")
ENROLLMENT_REGEX = re.compile(r"^[A-Z0-9]{6,20}$", re.IGNORECASE)

# Restrict student self-registration to NIT Patna institutional email domain
ALLOWED_STUDENT_EMAIL_DOMAIN = "nitp.ac.in"

def validate_registration_data(data: dict) -> list:
    """Validates user registration payload. Returns a list of error strings."""
    errors = []
    
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    phone = data.get("phone", "").strip()
    enrollment = data.get("enrollment_number", "").strip()
    hostel_id = data.get("hostel_id")
    room_id = data.get("room_id")
    room_number = data.get("room_number", "").strip()
    
    if not first_name or len(first_name) < 2:
        errors.append("First name must be at least 2 characters long.")
    if not last_name or len(last_name) < 2:
        errors.append("Last name must be at least 2 characters long.")
    if not email or not EMAIL_REGEX.match(email):
        errors.append("Please provide a valid institutional email address.")
    elif not email.lower().endswith(f"@{ALLOWED_STUDENT_EMAIL_DOMAIN}"):
        errors.append(f"Student registration is restricted to @{ALLOWED_STUDENT_EMAIL_DOMAIN} email addresses only.")
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not phone or not PHONE_REGEX.match(phone):
        errors.append("Phone number must contain between 10 and 15 digits.")
    if not enrollment or not ENROLLMENT_REGEX.match(enrollment):
        errors.append("Enrollment number must be alphanumeric and 6-20 characters long.")
    if not hostel_id:
        errors.append("Hostel selection is required.")
    if not room_id and not room_number:
        errors.append("Allocated room number is required.")
        
    return errors

def validate_complaint_data(data: dict) -> list:
    """Validates complaint submission payload. Returns a list of error strings.
    
    Note: Priority is NOT validated here as it is auto-assigned from the complaint
    category and can only be changed by Admin / Warden — not by the student.
    """
    errors = []
    
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    category_id = data.get("category_id")
    visibility = data.get("visibility", "private")
    
    if not title or len(title) < 5 or len(title) > 150:
        errors.append("Complaint title must be between 5 and 150 characters.")
    if not description or len(description) < 15:
        errors.append("Please provide a detailed description (at least 15 characters).")
    if not category_id:
        errors.append("Please select a valid complaint category.")
    if visibility not in ("private", "general"):
        errors.append("Invalid visibility option selected.")
        
    return errors

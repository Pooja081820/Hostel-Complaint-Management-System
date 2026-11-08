"""
Hostel Complaint Management System (HCMS)
Role-Based Access Control (RBAC) & Route Decorators (utils/decorators.py)
"""

import json
from functools import wraps
from flask import session, redirect, url_for, flash, request, abort, render_template
from db import execute_dml

def log_audit_event(action: str, target_entity: str, target_id=None, details=None):
    """Logs an operational or security event into the audit_logs table."""
    try:
        user_id = session.get("user_id")
        ip_addr = request.remote_addr or "127.0.0.1"
        user_agent = request.headers.get("User-Agent", "Unknown")[:250]
        details_str = json.dumps(details) if details else None
        
        sql = """
            INSERT INTO `audit_logs` 
            (`user_id`, `action`, `target_entity`, `target_id`, `ip_address`, `user_agent`, `details_json`)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        execute_dml(sql, (user_id, action, target_entity, target_id, ip_addr, user_agent, details_str))
    except Exception as e:
        # Non-blocking logging failure
        print(f"[AUDIT LOGGING ERROR] {e}")

def login_required(f):
    """Ensures that the client has an active authenticated session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """
    Restricts endpoint access to specific roles.
    Example: @role_required(['warden', 'admin'])
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
        
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for("auth.login", next=request.url))
            
            user_role = session.get("role")
            if user_role not in allowed_roles:
                log_audit_event(
                    action="UNAUTHORIZED_ACCESS_ATTEMPT",
                    target_entity="endpoint",
                    target_id=None,
                    details={"attempted_url": request.path, "user_role": user_role, "required_roles": allowed_roles}
                )
                return render_template("errors/403.html", required_roles=allowed_roles), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

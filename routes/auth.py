"""
Hostel Complaint Management System (HCMS)
Authentication & Session Controller (routes/auth.py)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from db import query_one, query_all, get_db_cursor, execute_dml
from utils.security import hash_password, verify_password, validate_csrf_token, generate_csrf_token
from utils.decorators import log_audit_event, login_required
from utils.validators import validate_registration_data

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticates users across all roles and establishes secure sessions."""
    # If user already authenticated, redirect to their role home
    if "user_id" in session:
        role = session.get("role")
        if role == "student":
            return redirect(url_for("student.dashboard"))
        elif role == "warden":
            return redirect(url_for("warden.dashboard"))
        elif role == "staff":
            return redirect(url_for("staff.dashboard"))
        elif role == "admin":
            return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        csrf_token = request.form.get("csrf_token")
        if not validate_csrf_token(csrf_token):
            flash("Security check failed: Invalid CSRF token. Please refresh and try again.", "danger")
            return redirect(url_for("auth.login"))

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "warning")
            return render_template("auth/login.html")

        # Query user record securely using parameterized statement
        sql_user = """
            SELECT user_id, email, password_hash, role, first_name, last_name, phone, is_active
            FROM users 
            WHERE email = %s
        """
        try:
            user = query_one(sql_user, (email,))
        except Exception as e:
            flash(f"Database Connection Error: {e}. Please check that MySQL is running and DB_PASSWORD in your .env file is correct.", "danger")
            return render_template("auth/login.html", email=email)

        if not user or not verify_password(user["password_hash"], password):
            log_audit_event("LOGIN_FAILED", "users", None, {"attempted_email": email})
            flash("Invalid email or password. Please verify credentials.", "danger")
            return render_template("auth/login.html", email=email)

        if not user["is_active"]:
            log_audit_event("LOGIN_INACTIVE_BLOCKED", "users", user["user_id"])
            flash("Your account is currently deactivated. Please contact the Chief Warden or Administrator.", "danger")
            return render_template("auth/login.html")

        # Establish server-side session attributes
        session.clear()
        session["user_id"] = user["user_id"]
        session["email"] = user["email"]
        session["role"] = user["role"]
        session["name"] = f"{user['first_name']} {user['last_name']}"
        session.permanent = True

        # Load role-specific profile IDs
        role = user["role"]
        target_dashboard = "auth.login"

        if role == "student":
            stud = query_one("""
                SELECT s.student_id, s.hostel_id, s.room_id, s.enrollment_number, r.room_number, h.code AS hostel_code
                FROM students s
                LEFT JOIN rooms r ON s.room_id = r.room_id
                LEFT JOIN hostels h ON s.hostel_id = h.hostel_id
                WHERE s.user_id = %s
            """, (user["user_id"],))
            if stud:
                session["student_id"] = stud["student_id"]
                session["hostel_id"] = stud["hostel_id"]
                session["room_id"] = stud["room_id"]
                session["room_number"] = stud.get("room_number") or ""
                session["hostel_code"] = stud.get("hostel_code") or ""
                session["enrollment_number"] = stud["enrollment_number"]
            target_dashboard = "student.dashboard"

        elif role == "warden":
            warden = query_one("SELECT warden_id, employee_code FROM wardens WHERE user_id = %s", (user["user_id"],))
            if warden:
                session["warden_id"] = warden["warden_id"]
                session["employee_code"] = warden["employee_code"]
                # Fetch assigned hostels for warden multi-tenancy enforcement
                hostel_rows = query_all("SELECT hostel_id FROM hostel_wardens WHERE warden_id = %s", (warden["warden_id"],))
                session["assigned_hostels"] = [row["hostel_id"] for row in hostel_rows]
            target_dashboard = "warden.dashboard"

        elif role == "staff":
            staff = query_one("SELECT staff_id, employee_code, specialization FROM staff WHERE user_id = %s", (user["user_id"],))
            if staff:
                session["staff_id"] = staff["staff_id"]
                session["employee_code"] = staff["employee_code"]
                session["specialization"] = staff["specialization"]
            target_dashboard = "staff.dashboard"

        elif role == "admin":
            target_dashboard = "admin.dashboard"

        log_audit_event("LOGIN_SUCCESS", "users", user["user_id"], {"role": role})
        flash(f"Welcome back, {session['name']}!", "success")
        return redirect(url_for(target_dashboard))

    return render_template("auth/login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Allows new residential students to register and link their hostel room."""
    if request.method == "POST":
        csrf_token = request.form.get("csrf_token")
        if not validate_csrf_token(csrf_token):
            flash("Security check failed: Invalid CSRF token. Please try again.", "danger")
            return redirect(url_for("auth.register"))

        room_number_input = request.form.get("room_number", "").strip()
        room_id_input = request.form.get("room_id")

        form_data = {
            "first_name": request.form.get("first_name", "").strip(),
            "last_name": request.form.get("last_name", "").strip(),
            "email": request.form.get("email", "").strip().lower(),
            "password": request.form.get("password", ""),
            "phone": request.form.get("phone", "").strip(),
            "enrollment_number": request.form.get("enrollment_number", "").strip().upper(),
            "hostel_id": request.form.get("hostel_id"),
            "room_id": room_id_input if room_id_input else None,
            "room_number": room_number_input,
            "branch": request.form.get("branch", "").strip(),
            "academic_year": request.form.get("academic_year", "1")
        }

        # Resolve or create room if room_number entered
        if form_data.get("room_number") and form_data.get("hostel_id"):
            r_match = query_one(
                "SELECT room_id FROM rooms WHERE hostel_id = %s AND LOWER(room_number) = LOWER(%s)",
                (form_data["hostel_id"], form_data["room_number"])
            )
            if r_match:
                form_data["room_id"] = r_match["room_id"]
            else:
                try:
                    flr = int(form_data["room_number"][0]) if form_data["room_number"][0].isdigit() else 1
                except Exception:
                    flr = 1
                _, created_rid = execute_dml(
                    "INSERT INTO rooms (hostel_id, room_number, floor_number) VALUES (%s, %s, %s)",
                    (form_data["hostel_id"], form_data["room_number"][:10], flr)
                )
                form_data["room_id"] = created_rid

        validation_errors = validate_registration_data(form_data)
        if validation_errors:
            for err in validation_errors:
                flash(err, "warning")
            hostels = query_all("SELECT hostel_id, name, code, type FROM hostels WHERE is_active = 1 ORDER BY name")
            return render_template("auth/register.html", hostels=hostels, form=form_data)

        # Check for unique email or enrollment conflict
        existing_email = query_one("SELECT user_id FROM users WHERE email = %s", (form_data["email"],))
        if existing_email:
            flash("An account with this email address already exists.", "danger")
            hostels = query_all("SELECT hostel_id, name, code, type FROM hostels WHERE is_active = 1 ORDER BY name")
            return render_template("auth/register.html", hostels=hostels, form=form_data)

        existing_enr = query_one("SELECT student_id FROM students WHERE enrollment_number = %s", (form_data["enrollment_number"],))
        if existing_enr:
            flash("A student with this enrollment number is already registered.", "danger")
            hostels = query_all("SELECT hostel_id, name, code, type FROM hostels WHERE is_active = 1 ORDER BY name")
            return render_template("auth/register.html", hostels=hostels, form=form_data)

        # Atomic transaction: Insert into users + students
        pwd_hash = hash_password(form_data["password"])
        try:
            with get_db_cursor(commit=True) as (_, cursor):
                # 1. Insert User
                sql_insert_user = """
                    INSERT INTO users (email, password_hash, role, first_name, last_name, phone, is_active)
                    VALUES (%s, %s, 'student', %s, %s, %s, 1)
                """
                cursor.execute(sql_insert_user, (
                    form_data["email"], pwd_hash, form_data["first_name"], 
                    form_data["last_name"], form_data["phone"]
                ))
                new_user_id = cursor.lastrowid

                # 2. Insert Student Extension
                sql_insert_student = """
                    INSERT INTO students (user_id, enrollment_number, hostel_id, room_id, branch, academic_year)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_insert_student, (
                    new_user_id, form_data["enrollment_number"], form_data["hostel_id"],
                    form_data["room_id"], form_data["branch"], int(form_data["academic_year"])
                ))
                new_student_id = cursor.lastrowid

                # 3. Create initial welcome notification
                sql_notif = """
                    INSERT INTO notifications (user_id, title, message)
                    VALUES (%s, 'Welcome to HCMS', 'Your account has been successfully created. You may now lodge and track hostel complaints.')
                """
                cursor.execute(sql_notif, (new_user_id,))

            log_audit_event("STUDENT_REGISTER", "students", new_student_id, {"email": form_data["email"]})
            flash("Registration successful! You may now log in with your credentials.", "success")
            return redirect(url_for("auth.login"))

        except Exception as e:
            flash(f"Registration failed due to a database error: {e}", "danger")
            hostels = query_all("SELECT hostel_id, name, code, type FROM hostels WHERE is_active = 1 ORDER BY name")
            return render_template("auth/register.html", hostels=hostels, form=form_data)

    try:
        hostels = query_all("SELECT hostel_id, name, code, type FROM hostels WHERE is_active = 1 ORDER BY name")
    except Exception:
        hostels = []
    return render_template("auth/register.html", hostels=hostels)

@auth_bp.route("/api/rooms/<int:hostel_id>", methods=["GET"])
def get_rooms_by_hostel(hostel_id):
    """Asynchronous API endpoint providing rooms belonging to a selected hostel."""
    sql = """
        SELECT room_id, room_number, floor_number
        FROM rooms 
        WHERE hostel_id = %s 
        ORDER BY floor_number, room_number
    """
    rooms = query_all(sql, (hostel_id,))
    return jsonify({"success": True, "rooms": rooms})

@auth_bp.route("/logout")
def logout():
    """Terminates session and logs audit trail."""
    user_id = session.get("user_id")
    if user_id:
        log_audit_event("LOGOUT", "users", user_id)
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for("auth.login"))

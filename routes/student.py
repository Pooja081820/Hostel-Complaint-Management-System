"""
Hostel Complaint Management System (HCMS)
Student Module Controller (routes/student.py)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.decorators import login_required, role_required
from utils.validators import validate_complaint_data
from utils.security import validate_csrf_token
from services.complaint_service import ComplaintService
from services.notification_service import NotificationService
from db import query_all, query_one, get_db_cursor, execute_dml

student_bp = Blueprint("student", __name__, url_prefix="/student")

@student_bp.route("/dashboard")
@login_required
@role_required(["student"])
def dashboard():
    """Renders student dashboard with real database KPI counters, recent complaints, and notifications."""
    student_id = session.get("student_id")
    user_id = session.get("user_id")

    if not student_id:
        flash("Student profile not found. Please contact administration.", "danger")
        return redirect(url_for("auth.login"))

    metrics = ComplaintService.get_student_metrics(student_id)
    recent_complaints = ComplaintService.get_student_complaints(student_id)[:5]
    notifications = NotificationService.get_user_notifications(user_id, limit=5)

    return render_template(
        "student/dashboard.html",
        metrics=metrics,
        recent_complaints=recent_complaints,
        notifications=notifications
    )

@student_bp.route("/submit", methods=["GET", "POST"])
@login_required
@role_required(["student"])
def submit_complaint():
    """Lodges a new complaint with category selection, priority, visibility, and evidence upload."""
    student_id = session.get("student_id")
    user_id = session.get("user_id")
    hostel_id = session.get("hostel_id")
    room_id = session.get("room_id")

    if request.method == "POST":
        csrf_token = request.form.get("csrf_token")
        if not validate_csrf_token(csrf_token):
            flash("Security check failed: Invalid CSRF token.", "danger")
            return redirect(url_for("student.submit_complaint"))

        entered_room_number = request.form.get("room_number", "").strip()
        target_room_id = room_id

        # Resolve or register the entered room number in the student's hostel
        if entered_room_number and hostel_id:
            existing_room = query_one(
                "SELECT room_id FROM rooms WHERE hostel_id = %s AND LOWER(room_number) = LOWER(%s)",
                (hostel_id, entered_room_number)
            )
            if existing_room:
                target_room_id = existing_room["room_id"]
            else:
                try:
                    flr = int(entered_room_number[0]) if entered_room_number[0].isdigit() else 1
                except Exception:
                    flr = 1
                _, new_rid = execute_dml(
                    "INSERT INTO rooms (hostel_id, room_number, floor_number, capacity, current_occupancy) VALUES (%s, %s, %s, 4, 0)",
                    (hostel_id, entered_room_number[:10], flr)
                )
                target_room_id = new_rid

        # Priority is governed by administration; defaults to category baseline upon initial lodge
        cat_id = request.form.get("category_id")
        cat_meta = query_one("SELECT default_priority FROM complaint_categories WHERE category_id = %s", (cat_id,)) if cat_id else None
        auto_priority = cat_meta["default_priority"] if cat_meta and cat_meta.get("default_priority") else "Medium"

        form_data = {
            "title": request.form.get("title", "").strip(),
            "description": request.form.get("description", "").strip(),
            "category_id": cat_id,
            "priority": auto_priority,
            "visibility": request.form.get("visibility", "private"),
            "room_number": entered_room_number
        }

        # Multi-hostel checkboxes for general issues
        affected_hostel_ids = request.form.getlist("affected_hostels")

        validation_errors = validate_complaint_data(form_data)
        if validation_errors:
            for err in validation_errors:
                flash(err, "warning")
            categories = query_all("SELECT * FROM complaint_categories WHERE is_active = 1 ORDER BY name")
            hostels = query_all("SELECT * FROM hostels WHERE is_active = 1 ORDER BY name")
            return render_template("student/submit.html", categories=categories, hostels=hostels, form=form_data)

        # Duplicate Check Warning Check (if user didn't explicitly override)
        confirm_duplicate = request.form.get("confirm_duplicate")
        if not confirm_duplicate:
            dups = ComplaintService.check_potential_duplicates(
                hostel_id=hostel_id,
                category_id=int(form_data["category_id"]),
                title=form_data["title"]
            )
            if dups:
                flash(f"Notice: We found {len(dups)} similar active complaint(s) in your hostel. Review them below or submit anyway.", "warning")
                categories = query_all("SELECT * FROM complaint_categories WHERE is_active = 1 ORDER BY name")
                hostels = query_all("SELECT * FROM hostels WHERE is_active = 1 ORDER BY name")
                return render_template(
                    "student/submit.html", 
                    categories=categories, 
                    hostels=hostels, 
                    form=form_data, 
                    duplicates=dups
                )

        # File upload
        attachment = request.files.get("evidence_photo")

        try:
            result = ComplaintService.create_complaint(
                student_id=student_id,
                user_id=user_id,
                hostel_id=hostel_id,
                room_id=target_room_id,
                category_id=int(form_data["category_id"]),
                title=form_data["title"],
                description=form_data["description"],
                priority=form_data["priority"],
                visibility=form_data["visibility"],
                affected_hostel_ids=affected_hostel_ids,
                attachment_file=attachment
            )
            flash(f"Complaint successfully lodged! Ticket Number: {result['ticket_number']}", "success")
            return redirect(url_for("student.complaint_detail", complaint_id=result["complaint_id"]))

        except Exception as e:
            flash(f"Error submitting complaint: {e}", "danger")
            categories = query_all("SELECT * FROM complaint_categories WHERE is_active = 1 ORDER BY name")
            hostels = query_all("SELECT * FROM hostels WHERE is_active = 1 ORDER BY name")
            return render_template("student/submit.html", categories=categories, hostels=hostels, form=form_data)

    categories = query_all("SELECT * FROM complaint_categories WHERE is_active = 1 ORDER BY name")
    hostels = query_all("SELECT * FROM hostels WHERE is_active = 1 ORDER BY name")
    return render_template("student/submit.html", categories=categories, hostels=hostels)

@student_bp.route("/api/check-duplicates", methods=["POST"])
@login_required
@role_required(["student"])
def api_check_duplicates():
    """Asynchronous AJAX endpoint for duplicate warning alerts on the submission form."""
    data = request.get_json() or {}
    category_id = data.get("category_id")
    title = data.get("title", "")
    hostel_id = session.get("hostel_id")

    if not category_id or not title or len(title) < 4:
        return jsonify({"duplicates": []})

    dups = ComplaintService.check_potential_duplicates(
        hostel_id=hostel_id,
        category_id=int(category_id),
        title=title
    )
    return jsonify({"duplicates": dups})

@student_bp.route("/complaints")
@login_required
@role_required(["student"])
def my_complaints():
    """Displays all complaints submitted by the student with multi-criteria filtering."""
    student_id = session.get("student_id")
    status_filter = request.args.get("status", "all")
    category_filter = request.args.get("category", "all")
    search = request.args.get("q", "").strip()

    complaints = ComplaintService.get_student_complaints(
        student_id=student_id,
        status_filter=status_filter,
        category_filter=category_filter,
        search_term=search
    )
    categories = query_all("SELECT * FROM complaint_categories WHERE is_active = 1 ORDER BY name")

    return render_template(
        "student/complaints_list.html",
        complaints=complaints,
        categories=categories,
        current_status=status_filter,
        current_category=category_filter,
        search_query=search
    )

@student_bp.route("/complaints/<int:complaint_id>")
@login_required
@role_required(["student"])
def complaint_detail(complaint_id):
    """Renders comprehensive complaint view with progress tracker and dialogue thread."""
    student_id = session.get("student_id")
    try:
        complaint = ComplaintService.get_complaint_details(complaint_id, student_id=student_id)
        if not complaint:
            flash("Complaint not found.", "warning")
            return redirect(url_for("student.my_complaints"))
    except PermissionError:
        flash("You are not authorized to view this complaint.", "danger")
        return redirect(url_for("student.my_complaints"))

    return render_template("student/detail.html", complaint=complaint)

@student_bp.route("/complaints/<int:complaint_id>/cancel", methods=["POST"])
@login_required
@role_required(["student"])
def cancel_complaint(complaint_id):
    """Cancels a complaint before maintenance staff assignment."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("student.complaint_detail", complaint_id=complaint_id))

    student_id = session.get("student_id")
    user_id = session.get("user_id")
    reason = request.form.get("cancel_reason", "Cancelled by student").strip()

    success, msg = ComplaintService.cancel_complaint(complaint_id, student_id, user_id, reason)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("student.complaint_detail", complaint_id=complaint_id))

@student_bp.route("/complaints/<int:complaint_id>/reopen", methods=["POST"])
@login_required
@role_required(["student"])
def reopen_complaint(complaint_id):
    """Reopens a resolved complaint within 48h limit using stored procedure."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("student.complaint_detail", complaint_id=complaint_id))

    user_id = session.get("user_id")
    reason = request.form.get("reopen_reason", "").strip()
    if not reason or len(reason) < 10:
        flash("Please provide a substantive reason for reopening (at least 10 characters).", "warning")
        return redirect(url_for("student.complaint_detail", complaint_id=complaint_id))

    # Call MySQL stored procedure sp_reopen_complaint
    try:
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.callproc("sp_reopen_complaint", [complaint_id, user_id, reason, 0, ""])
            cursor.execute("SELECT @_sp_reopen_complaint_3, @_sp_reopen_complaint_4")
            out_res = cursor.fetchone()
            success = out_res["@_sp_reopen_complaint_3"] if out_res else 0
            message = out_res["@_sp_reopen_complaint_4"] if out_res else "Reopen procedure executed."

        flash(message, "success" if success else "danger")
    except Exception as e:
        flash(f"Error reopening complaint: {e}", "danger")

    return redirect(url_for("student.complaint_detail", complaint_id=complaint_id))

@student_bp.route("/complaints/<int:complaint_id>/feedback", methods=["POST"])
@login_required
@role_required(["student"])
def submit_feedback(complaint_id):
    """Records rating (1-5) and feedback on a resolved ticket."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("student.complaint_detail", complaint_id=complaint_id))

    student_id = session.get("student_id")
    rating = int(request.form.get("rating", 5))
    comments = request.form.get("comments", "").strip()

    success, msg = ComplaintService.submit_feedback(complaint_id, student_id, rating, comments)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("student.complaint_detail", complaint_id=complaint_id))

@student_bp.route("/notifications")
@login_required
@role_required(["student"])
def notifications():
    """Renders user notifications feed."""
    user_id = session.get("user_id")
    notifs = NotificationService.get_user_notifications(user_id, limit=50)
    return render_template("student/notifications.html", notifications=notifs)

@student_bp.route("/notifications/read-all", methods=["POST"])
@login_required
@role_required(["student"])
def mark_all_read():
    """Marks all user alerts as read."""
    user_id = session.get("user_id")
    NotificationService.mark_all_as_read(user_id)
    flash("All notifications marked as read.", "info")
    return redirect(url_for("student.notifications"))

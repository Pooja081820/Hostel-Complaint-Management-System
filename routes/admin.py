"""
Hostel Complaint Management System (HCMS)
Administrator Controller (routes/admin.py)
"""

import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, Response
from utils.decorators import login_required, role_required
from utils.security import validate_csrf_token
from services.admin_service import AdminService
from services.complaint_service import ComplaintService
from services.assignment_service import AssignmentService
from services.notification_service import NotificationService
from db import query_all, query_one, execute_dml

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
@login_required
@role_required(["admin"])
def dashboard():
    """System-wide executive governance command with KPI counters, analytics, and audit highlights."""
    user_id = session.get("user_id")
    try:
        kpis = AdminService.get_system_kpis()
        analytics = AdminService.get_advanced_analytics()
        recent_audits = AdminService.get_audit_logs(limit=8)
        notifications = NotificationService.get_user_notifications(user_id, limit=5)
    except Exception:
        kpis = {}
        analytics = {"categories": [], "staff_ranking": [], "hostels": []}
        recent_audits = []
        notifications = []

    return render_template(
        "admin/dashboard.html",
        kpis=kpis,
        analytics=analytics,
        recent_audits=recent_audits,
        notifications=notifications
    )

@admin_bp.route("/users")
@login_required
@role_required(["admin"])
def users_list():
    """Master user account management table across all roles."""
    role_filter = request.args.get("role", "all")
    status_filter = request.args.get("status", "all")
    search = request.args.get("q", "").strip()

    try:
        users = AdminService.get_all_users(role_filter, status_filter, search)
        hostels = query_all("SELECT hostel_id, name, code, type FROM hostels WHERE is_active = 1 ORDER BY name")
    except Exception:
        users = []
        hostels = []

    return render_template(
        "admin/users.html",
        users=users,
        hostels=hostels,
        current_role=role_filter,
        current_status=status_filter,
        search_query=search
    )

@admin_bp.route("/users/create", methods=["POST"])
@login_required
@role_required(["admin"])
def create_user():
    """Creates a new Warden or Maintenance Staff member account."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("admin.users_list"))

    data = {
        "role": request.form.get("role"),
        "email": request.form.get("email"),
        "password": request.form.get("password"),
        "first_name": request.form.get("first_name"),
        "last_name": request.form.get("last_name"),
        "phone": request.form.get("phone"),
        "employee_code": request.form.get("employee_code"),
        "office_location": request.form.get("office_location"),
        "hostel_id": request.form.get("hostel_id"),
        "specialization": request.form.get("specialization")
    }

    success, msg = AdminService.create_staff_or_warden(data)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("admin.users_list"))

@admin_bp.route("/users/<int:user_id>/toggle-status", methods=["POST"])
@login_required
@role_required(["admin"])
def toggle_user_status(user_id):
    """Activates or deactivates a user account."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("admin.users_list"))

    admin_user_id = session.get("user_id")
    success, msg = AdminService.toggle_user_status(user_id, admin_user_id)
    flash(msg, "info" if success else "danger")
    return redirect(url_for("admin.users_list"))

@admin_bp.route("/hostels")
@login_required
@role_required(["admin"])
def hostels_list():
    """Campus residential hostel blocks management."""
    try:
        hostels = AdminService.get_all_hostels_with_stats()
        wardens = query_all("SELECT w.warden_id, w.employee_code, CONCAT(u.first_name, ' ', u.last_name) AS warden_name FROM wardens w JOIN users u ON w.user_id = u.user_id WHERE u.is_active = 1")
    except Exception:
        hostels = []
        wardens = []

    return render_template("admin/hostels.html", hostels=hostels, wardens=wardens)

@admin_bp.route("/hostels/create", methods=["POST"])
@login_required
@role_required(["admin"])
def create_hostel():
    """Registers a new hostel block."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("admin.hostels_list"))

    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip()
    htype = request.form.get("type", "boys")
    floors = int(request.form.get("total_floors", 3))

    success, msg = AdminService.create_hostel(name, code, htype, floors)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("admin.hostels_list"))

@admin_bp.route("/hostels/<int:hostel_id>/assign-warden", methods=["POST"])
@login_required
@role_required(["admin"])
def assign_warden(hostel_id):
    """Assigns or unassigns a warden to a hostel block."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("admin.hostels_list"))

    action = request.form.get("action", "assign")
    warden_id = int(request.form.get("warden_id"))

    if action == "assign":
        success, msg = AdminService.assign_warden_to_hostel(hostel_id, warden_id)
    else:
        success, msg = AdminService.remove_warden_from_hostel(hostel_id, warden_id)

    flash(msg, "success" if success else "danger")
    return redirect(url_for("admin.hostels_list"))

@admin_bp.route("/hostels/<int:hostel_id>/rooms")
@login_required
@role_required(["admin"])
def rooms_list(hostel_id):
    """Room allocation registry for a specific hostel block."""
    try:
        hostel = query_all("SELECT * FROM hostels WHERE hostel_id = %s", (hostel_id,))
        hostel = hostel[0] if hostel else None
        rooms = AdminService.get_hostel_rooms(hostel_id)
    except Exception:
        hostel = None
        rooms = []

    if not hostel:
        flash("Hostel not found.", "warning")
        return redirect(url_for("admin.hostels_list"))

    return render_template("admin/rooms.html", hostel=hostel, rooms=rooms)

@admin_bp.route("/hostels/<int:hostel_id>/rooms/create", methods=["POST"])
@login_required
@role_required(["admin"])
def create_room(hostel_id):
    """Adds a new room to the specified hostel block."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("admin.rooms_list", hostel_id=hostel_id))

    room_number = request.form.get("room_number", "").strip()
    floor = int(request.form.get("floor_number", 1))
    capacity = int(request.form.get("capacity", 2))

    success, msg = AdminService.create_room(hostel_id, room_number, floor, capacity)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("admin.rooms_list", hostel_id=hostel_id))

@admin_bp.route("/categories")
@login_required
@role_required(["admin"])
def categories_list():
    """Complaint categories and SLA hours configuration."""
    try:
        categories = AdminService.get_all_categories_with_stats()
    except Exception:
        categories = []

    return render_template("admin/categories.html", categories=categories)

@admin_bp.route("/categories/create", methods=["POST"])
@login_required
@role_required(["admin"])
def create_category():
    """Adds a new complaint category."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("admin.categories_list"))

    name = request.form.get("name", "").strip()
    sla_hours = int(request.form.get("default_sla_hours", 24))
    priority = request.form.get("default_priority", "Medium")
    desc = request.form.get("description", "").strip()

    success, msg = AdminService.create_category(name, sla_hours, priority, desc)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("admin.categories_list"))

@admin_bp.route("/complaints")
@login_required
@role_required(["admin"])
def all_complaints():
    """University-wide complaint registry."""
    status_filter = request.args.get("status", "all")
    hostel_filter = request.args.get("hostel_id", "all")
    search = request.args.get("q", "").strip()

    try:
        # Fetch all active hostels for filter
        all_hostels = query_all("SELECT hostel_id FROM hostels WHERE is_active = 1")
        all_h_ids = [h["hostel_id"] for h in all_hostels]
        
        filters = {
            "status": status_filter,
            "hostel_id": hostel_filter,
            "search": search
        }
        complaints = ComplaintService.get_warden_complaints(all_h_ids, filters)
        hostels_meta = query_all("SELECT hostel_id, name, code FROM hostels WHERE is_active = 1 ORDER BY name")
    except Exception:
        complaints = []
        hostels_meta = []

    return render_template(
        "admin/all_complaints.html",
        complaints=complaints,
        hostels=hostels_meta,
        current_status=status_filter,
        current_hostel=hostel_filter,
        search_query=search
    )

@admin_bp.route("/complaints/<int:complaint_id>")
@login_required
@role_required(["admin"])
def complaint_detail(complaint_id):
    """Admin full inspection and triage console for complaints."""
    complaint = ComplaintService.get_complaint_details(complaint_id)
    if not complaint:
        flash("Complaint record not found.", "warning")
        return redirect(url_for("admin.all_complaints"))

    available_staff = AssignmentService.get_staff_with_workload()
    sql_prio_hist = """
        SELECT cph.*, CONCAT(u.first_name, ' ', u.last_name) AS changed_by_name
        FROM complaint_priority_history cph
        JOIN users u ON cph.changed_by_user_id = u.user_id
        WHERE cph.complaint_id = %s
        ORDER BY cph.created_at DESC
    """
    priority_history = query_all(sql_prio_hist, (complaint_id,))

    return render_template(
        "admin/complaint_detail.html",
        complaint=complaint,
        available_staff=available_staff,
        priority_history=priority_history
    )

@admin_bp.route("/complaints/<int:complaint_id>/change-priority", methods=["POST"])
@login_required
@role_required(["admin"])
def change_priority(complaint_id):
    """Adjusts complaint priority level by Administrator with audit justification."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(request.referrer or url_for("admin.all_complaints"))

    new_priority = request.form.get("priority")
    reason = request.form.get("reason", "").strip() or "Priority designated by Campus Administrator"
    admin_user_id = session.get("user_id")

    success, msg = ComplaintService.update_complaint_priority(
        complaint_id=complaint_id,
        warden_user_id=admin_user_id,
        new_priority=new_priority,
        reason=reason
    )
    
    if success:
        # Notify student that priority was designated/updated by Admin
        c_info = query_one(
            "SELECT c.ticket_number, s.user_id FROM complaints c JOIN students s ON c.student_id = s.student_id WHERE c.complaint_id = %s",
            (complaint_id,)
        )
        if c_info:
            try:
                execute_dml(
                    "INSERT INTO notifications (user_id, complaint_id, title, message) VALUES (%s, %s, %s, %s)",
                    (c_info["user_id"], complaint_id, "Priority Designated by Admin",
                     f"Administrator designated ticket {c_info['ticket_number']} priority to {new_priority}. Reason: {reason[:80]}")
                )
            except Exception:
                pass

    flash(msg, "success" if success else "danger")
    return redirect(request.referrer or url_for("admin.all_complaints"))

@admin_bp.route("/complaints/<int:complaint_id>/respond", methods=["POST"])
@login_required
@role_required(["admin"])
def respond(complaint_id):
    """Adds an administrative remark to the complaint dialogue."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("admin.complaint_detail", complaint_id=complaint_id))

    message = request.form.get("message", "").strip()
    is_internal = bool(request.form.get("is_internal"))
    admin_user_id = session.get("user_id")

    success, msg = ComplaintService.add_management_response(
        complaint_id=complaint_id,
        user_id=admin_user_id,
        message=message,
        is_internal=is_internal
    )
    flash("Comment posted." if success else msg, "success" if success else "danger")
    return redirect(url_for("admin.complaint_detail", complaint_id=complaint_id))

@admin_bp.route("/audit-logs")
@login_required
@role_required(["admin"])
def audit_logs():
    """Security and compliance audit trail viewer."""
    action_filter = request.args.get("action", "all")
    try:
        logs = AdminService.get_audit_logs(limit=100, action_filter=action_filter)
    except Exception:
        logs = []

    return render_template("admin/audit_logs.html", logs=logs, current_action=action_filter)

@admin_bp.route("/complaints/export")
@login_required
@role_required(["admin"])
def export_complaints_csv():
    """Generates and downloads a CSV export of university-wide complaints."""
    try:
        all_hostels = query_all("SELECT hostel_id FROM hostels WHERE is_active = 1")
        all_h_ids = [h["hostel_id"] for h in all_hostels]
        complaints = ComplaintService.get_warden_complaints(all_h_ids, {})
    except Exception:
        complaints = []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Ticket Number", "Student Name", "Enrollment", "Hostel", "Room",
        "Category", "Title", "Priority", "Status", "Is Overdue", "Created At", "Resolved At"
    ])
    for c in complaints:
        writer.writerow([
            c.get("ticket_number", ""),
            f"{c.get('first_name', '')} {c.get('last_name', '')}",
            c.get("enrollment_number", ""),
            c.get("hostel_name", ""),
            c.get("room_number", ""),
            c.get("category_name", ""),
            c.get("title", ""),
            c.get("priority", ""),
            c.get("status", ""),
            "Yes" if c.get("is_overdue") else "No",
            c.get("created_at", ""),
            c.get("resolved_at", "")
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=complaints_registry.csv"}
    )


"""
Hostel Complaint Management System (HCMS)
Maintenance Staff Controller (routes/staff.py)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from utils.decorators import login_required, role_required
from utils.security import validate_csrf_token
from services.assignment_service import AssignmentService
from services.notification_service import NotificationService
from db import query_one

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")

@staff_bp.route("/dashboard")
@login_required
@role_required(["staff"])
def dashboard():
    """Renders maintenance technician task queue, priority assignments, and workload metrics."""
    staff_id = session.get("staff_id")
    user_id = session.get("user_id")
    if not staff_id:
        flash("Staff technician profile not found.", "warning")
        return redirect(url_for("auth.login"))

    try:
        metrics = AssignmentService.get_staff_metrics(staff_id)
        active_tasks = AssignmentService.get_staff_tasks(staff_id)
        notifications = NotificationService.get_user_notifications(user_id, limit=5)
    except Exception:
        metrics = {}
        active_tasks = []
        notifications = []

    return render_template(
        "staff/dashboard.html",
        metrics=metrics,
        tasks=active_tasks,
        notifications=notifications
    )

@staff_bp.route("/tasks/complaint/<int:complaint_id>")
@login_required
@role_required(["staff"])
def task_by_complaint(complaint_id):
    """Direct work order lookup from notification link for maintenance technician."""
    staff_id = session.get("staff_id")
    assignment = query_one(
        "SELECT assignment_id FROM complaint_assignments WHERE complaint_id = %s AND staff_id = %s ORDER BY assignment_id DESC LIMIT 1",
        (complaint_id, staff_id)
    )
    if assignment:
        return redirect(url_for("staff.task_detail", assignment_id=assignment["assignment_id"]))
    flash("Task assignment for this ticket was not found or is currently assigned to another technician.", "info")
    return redirect(url_for("staff.dashboard"))

@staff_bp.route("/tasks/<int:assignment_id>")
@login_required
@role_required(["staff"])
def task_detail(assignment_id):
    """Detailed work order view: Review student issue, location, initial evidence, and post updates."""
    staff_id = session.get("staff_id")
    try:
        task = AssignmentService.get_staff_task_detail(assignment_id, staff_id)
        if not task:
            flash("Task assignment not found or access denied.", "warning")
            return redirect(url_for("staff.dashboard"))
    except Exception as e:
        flash(f"Error loading work order: {e}", "danger")
        return redirect(url_for("staff.dashboard"))

    return render_template("staff/task_detail.html", task=task)

@staff_bp.route("/tasks/<int:assignment_id>/accept", methods=["POST"])
@login_required
@role_required(["staff"])
def accept_task(assignment_id):
    """Accepts a work order, transitioning status to 'In Progress'."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("staff.task_detail", assignment_id=assignment_id))

    staff_id = session.get("staff_id")
    user_id = session.get("user_id")

    success, msg = AssignmentService.accept_task(assignment_id, staff_id, user_id)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("staff.task_detail", assignment_id=assignment_id))

@staff_bp.route("/tasks/<int:assignment_id>/update-notes", methods=["POST"])
@login_required
@role_required(["staff"])
def update_notes(assignment_id):
    """Appends technician work progress notes to the work order."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("staff.task_detail", assignment_id=assignment_id))

    staff_id = session.get("staff_id")
    user_id = session.get("user_id")
    notes = request.form.get("work_notes", "").strip()

    success, msg = AssignmentService.add_task_notes(assignment_id, staff_id, user_id, notes)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("staff.task_detail", assignment_id=assignment_id))

@staff_bp.route("/tasks/<int:assignment_id>/complete", methods=["POST"])
@login_required
@role_required(["staff"])
def complete_task(assignment_id):
    """Marks work order completed and uploads evidentiary completion proof."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("staff.task_detail", assignment_id=assignment_id))

    staff_id = session.get("staff_id")
    user_id = session.get("user_id")
    work_notes = request.form.get("completion_summary", "").strip()
    completion_photo = request.files.get("completion_photo")

    success, msg = AssignmentService.complete_task(
        assignment_id=assignment_id,
        staff_id=staff_id,
        user_id=user_id,
        work_notes=work_notes,
        completion_photo=completion_photo
    )
    flash(msg, "success" if success else "danger")
    return redirect(url_for("staff.dashboard"))

@staff_bp.route("/history")
@login_required
@role_required(["staff"])
def history():
    """Displays completed work history with student ratings and feedback reviews."""
    staff_id = session.get("staff_id")
    try:
        completed_tasks = AssignmentService.get_staff_history(staff_id)
    except Exception:
        completed_tasks = []

    return render_template("staff/history.html", tasks=completed_tasks)

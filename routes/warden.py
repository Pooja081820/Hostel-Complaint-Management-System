"""
Hostel Complaint Management System (HCMS)
Warden Module Controller (routes/warden.py)
"""

import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, Response
from utils.decorators import login_required, role_required
from utils.security import validate_csrf_token
from services.complaint_service import ComplaintService
from services.assignment_service import AssignmentService
from db import query_all, query_one

warden_bp = Blueprint("warden", __name__, url_prefix="/warden")

def get_authorized_hostels():
    """Helper retrieving the list of hostel IDs assigned to the current warden."""
    assigned = session.get("assigned_hostels")
    if not assigned:
        warden_id = session.get("warden_id")
        if warden_id:
            rows = query_all("SELECT hostel_id FROM hostel_wardens WHERE warden_id = %s", (warden_id,))
            assigned = [r["hostel_id"] for r in rows]
            session["assigned_hostels"] = assigned
        else:
            assigned = []
    return assigned

@warden_bp.route("/dashboard")
@login_required
@role_required(["warden"])
def dashboard():
    """Warden Operational Command dashboard with aggregated metrics, urgent tickets, and staff workload."""
    assigned_hostels = get_authorized_hostels()
    if not assigned_hostels:
        flash("You are not currently assigned to any campus hostel blocks.", "warning")

    try:
        metrics = ComplaintService.get_warden_metrics(assigned_hostels)
        urgent_complaints = ComplaintService.get_warden_complaints(assigned_hostels, filters={"status": "all"})[:6]
        staff_workload = AssignmentService.get_staff_with_workload()[:6]
        hostels = []
        if assigned_hostels:
            placeholders = ",".join(["%s"] * len(assigned_hostels))
            hostels = query_all(f"SELECT hostel_id, name, code FROM hostels WHERE hostel_id IN ({placeholders})", tuple(assigned_hostels))
    except Exception:
        metrics = {}
        urgent_complaints = []
        staff_workload = []
        hostels = []

    return render_template(
        "warden/dashboard.html",
        metrics=metrics,
        urgent_complaints=urgent_complaints,
        staff_workload=staff_workload,
        hostels=hostels
    )

@warden_bp.route("/complaints")
@login_required
@role_required(["warden"])
def complaints():
    """Master triage table for complaints in warden's assigned hostels."""
    assigned_hostels = get_authorized_hostels()
    
    filters = {
        "hostel_id": request.args.get("hostel_id", "all"),
        "category_id": request.args.get("category_id", "all"),
        "priority": request.args.get("priority", "all"),
        "status": request.args.get("status", "all"),
        "overdue_only": request.args.get("overdue") == "1",
        "search": request.args.get("q", "").strip()
    }

    try:
        complaints_list = ComplaintService.get_warden_complaints(assigned_hostels, filters)
        categories = query_all("SELECT * FROM complaint_categories WHERE is_active = 1 ORDER BY name")
        hostels = []
        if assigned_hostels:
            placeholders = ",".join(["%s"] * len(assigned_hostels))
            hostels = query_all(f"SELECT hostel_id, name, code FROM hostels WHERE hostel_id IN ({placeholders})", tuple(assigned_hostels))
    except Exception:
        complaints_list = []
        categories = []
        hostels = []

    return render_template(
        "warden/complaints.html",
        complaints=complaints_list,
        categories=categories,
        hostels=hostels,
        filters=filters
    )

@warden_bp.route("/complaints/<int:complaint_id>")
@login_required
@role_required(["warden"])
def complaint_detail(complaint_id):
    """Management review console: Inspect evidence, delegate to technicians, alter priority, or verify."""
    assigned_hostels = get_authorized_hostels()
    complaint = ComplaintService.get_complaint_details(complaint_id)
    if not complaint:
        flash("Complaint record not found.", "warning")
        return redirect(url_for("warden.complaints"))

    # Multi-tenant isolation: verify complaint belongs to warden's assigned hostels
    if complaint["hostel_id"] not in assigned_hostels:
        flash("Security Alert: You are not authorized to inspect complaints belonging to this hostel block.", "danger")
        return render_template("errors/403.html", required_roles=["Assigned Warden"]), 403

    # Available staff technicians with workload counts
    available_staff = AssignmentService.get_staff_with_workload()

    # Priority history trail
    sql_prio_hist = """
        SELECT cph.*, CONCAT(u.first_name, ' ', u.last_name) AS changed_by_name
        FROM complaint_priority_history cph
        JOIN users u ON cph.changed_by_user_id = u.user_id
        WHERE cph.complaint_id = %s
        ORDER BY cph.created_at DESC
    """
    priority_history = query_all(sql_prio_hist, (complaint_id,))

    return render_template(
        "warden/detail.html",
        complaint=complaint,
        available_staff=available_staff,
        priority_history=priority_history
    )

@warden_bp.route("/complaints/<int:complaint_id>/assign", methods=["POST"])
@login_required
@role_required(["warden"])
def assign_staff(complaint_id):
    """Delegates a work order to a maintenance staff technician."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("warden.complaint_detail", complaint_id=complaint_id))

    assigned_hostels = get_authorized_hostels()
    complaint = query_one("SELECT hostel_id FROM complaints WHERE complaint_id = %s", (complaint_id,))
    if not complaint or complaint["hostel_id"] not in assigned_hostels:
        abort(403)

    staff_id = int(request.form.get("staff_id"))
    warden_id = session.get("warden_id")
    warden_user_id = session.get("user_id")
    work_notes = request.form.get("work_notes", "").strip()

    success, msg = AssignmentService.assign_staff_to_complaint(
        complaint_id=complaint_id,
        staff_id=staff_id,
        warden_id=warden_id,
        warden_user_id=warden_user_id,
        work_notes=work_notes
    )
    flash(msg, "success" if success else "danger")
    return redirect(url_for("warden.complaint_detail", complaint_id=complaint_id))

@warden_bp.route("/complaints/<int:complaint_id>/change-priority", methods=["POST"])
@login_required
@role_required(["warden"])
def change_priority(complaint_id):
    """Adjusts complaint priority level with mandatory audit reason."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("warden.complaint_detail", complaint_id=complaint_id))

    assigned_hostels = get_authorized_hostels()
    complaint = query_one("SELECT hostel_id FROM complaints WHERE complaint_id = %s", (complaint_id,))
    if not complaint or complaint["hostel_id"] not in assigned_hostels:
        abort(403)

    new_priority = request.form.get("priority")
    reason = request.form.get("reason", "").strip()
    warden_user_id = session.get("user_id")

    success, msg = ComplaintService.update_complaint_priority(
        complaint_id=complaint_id,
        warden_user_id=warden_user_id,
        new_priority=new_priority,
        reason=reason
    )
    flash(msg, "success" if success else "danger")
    return redirect(url_for("warden.complaint_detail", complaint_id=complaint_id))

@warden_bp.route("/complaints/<int:complaint_id>/respond", methods=["POST"])
@login_required
@role_required(["warden"])
def respond(complaint_id):
    """Adds a management remark (public to student or internal warden note)."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("warden.complaint_detail", complaint_id=complaint_id))

    assigned_hostels = get_authorized_hostels()
    complaint = query_one("SELECT hostel_id FROM complaints WHERE complaint_id = %s", (complaint_id,))
    if not complaint or complaint["hostel_id"] not in assigned_hostels:
        abort(403)

    message = request.form.get("message", "").strip()
    is_internal = request.form.get("is_internal") == "1"
    warden_user_id = session.get("user_id")

    success, msg = ComplaintService.add_management_response(
        complaint_id=complaint_id,
        user_id=warden_user_id,
        message=message,
        is_internal=is_internal
    )
    flash(msg, "success" if success else "danger")
    return redirect(url_for("warden.complaint_detail", complaint_id=complaint_id))

@warden_bp.route("/complaints/<int:complaint_id>/resolve", methods=["POST"])
@login_required
@role_required(["warden"])
def resolve(complaint_id):
    """Verifies completion quality and closes ticket."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("warden.complaint_detail", complaint_id=complaint_id))

    assigned_hostels = get_authorized_hostels()
    complaint = query_one("SELECT hostel_id FROM complaints WHERE complaint_id = %s", (complaint_id,))
    if not complaint or complaint["hostel_id"] not in assigned_hostels:
        abort(403)

    remarks = request.form.get("remarks", "Resolution verified by warden.").strip()
    warden_user_id = session.get("user_id")

    success, msg = ComplaintService.resolve_complaint_by_warden(
        complaint_id=complaint_id,
        warden_user_id=warden_user_id,
        remarks=remarks
    )
    flash(msg, "success" if success else "danger")
    return redirect(url_for("warden.complaint_detail", complaint_id=complaint_id))

@warden_bp.route("/complaints/<int:complaint_id>/reject", methods=["POST"])
@login_required
@role_required(["warden"])
def reject(complaint_id):
    """Rejects an invalid or policy-violating complaint."""
    csrf_token = request.form.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        flash("Security check failed: Invalid CSRF token.", "danger")
        return redirect(url_for("warden.complaint_detail", complaint_id=complaint_id))

    assigned_hostels = get_authorized_hostels()
    complaint = query_one("SELECT hostel_id FROM complaints WHERE complaint_id = %s", (complaint_id,))
    if not complaint or complaint["hostel_id"] not in assigned_hostels:
        abort(403)

    reason = request.form.get("rejection_reason", "").strip()
    warden_user_id = session.get("user_id")

    success, msg = ComplaintService.reject_complaint_by_warden(
        complaint_id=complaint_id,
        warden_user_id=warden_user_id,
        reason=reason
    )
    flash(msg, "info" if success else "danger")
    return redirect(url_for("warden.complaint_detail", complaint_id=complaint_id))

@warden_bp.route("/reports")
@login_required
@role_required(["warden"])
def reports():
    """Generates SLA compliance and turnaround analytics for warden's hostels."""
    assigned_hostels = get_authorized_hostels()
    try:
        hostel_reports = ComplaintService.get_warden_reports(assigned_hostels)
    except Exception:
        hostel_reports = []
    return render_template("warden/reports.html", reports=hostel_reports)

@warden_bp.route("/reports/export")
@login_required
@role_required(["warden"])
def export_reports_csv():
    """Exports warden hostel turnaround and SLA metrics to CSV."""
    assigned_hostels = get_authorized_hostels()
    try:
        hostel_reports = ComplaintService.get_warden_reports(assigned_hostels)
    except Exception:
        hostel_reports = []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Hostel Name", "Hostel Code", "Total Complaints", "Resolved Complaints",
        "Overdue Complaints", "Resolution Rate (%)", "Avg Turnaround (Hours)", "Avg Student Rating"
    ])
    for r in hostel_reports:
        writer.writerow([
            r.get("hostel_name", ""),
            r.get("hostel_code", ""),
            r.get("total_complaints", 0),
            r.get("resolved_complaints", 0),
            r.get("overdue_complaints", 0),
            r.get("resolution_rate", 0),
            r.get("avg_turnaround_hours", 0),
            r.get("avg_satisfaction_rating", "N/A")
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=warden_sla_report.csv"}
    )


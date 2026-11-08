"""
Hostel Complaint Management System (HCMS)
Unified Notifications Blueprint (routes/notifications.py)
Supports in-app alerts and real-time polling across all roles.
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from utils.decorators import login_required
from services.notification_service import NotificationService
from db import query_one

notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.route("/notifications")
@login_required
def view_notifications():
    """Universal in-app notifications inbox for students, wardens, staff, and admins."""
    user_id = session.get("user_id")
    role = session.get("role")
    try:
        notifs = NotificationService.get_user_notifications(user_id, limit=60)
    except Exception:
        notifs = []

    return render_template("notifications.html", notifications=notifs, user_role=role)

@notifications_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_read():
    """Marks all notifications as read for current user."""
    user_id = session.get("user_id")
    try:
        NotificationService.mark_all_as_read(user_id)
        flash("All alerts marked as read.", "info")
    except Exception:
        pass
    return redirect(url_for("notifications.view_notifications"))

@notifications_bp.route("/api/notifications/poll")
@login_required
def poll_notifications():
    """Lightweight JSON API for real-time unread counter polling."""
    user_id = session.get("user_id")
    try:
        row = query_one(
            "SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = %s AND is_read = 0", 
            (user_id,)
        )
        unread = row["cnt"] if row else 0
    except Exception:
        unread = 0

    return jsonify({"success": True, "unread_count": unread})

@notifications_bp.route("/api/notifications/<int:notification_id>/mark-read", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    """AJAX endpoint to dismiss / mark a specific notification as read."""
    user_id = session.get("user_id")
    try:
        success = NotificationService.mark_as_read(notification_id, user_id)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

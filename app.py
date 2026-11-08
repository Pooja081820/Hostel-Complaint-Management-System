"""
Hostel Complaint Management System (HCMS)
Main Application Factory & Entry Point (app.py)
"""

import os
import logging
from flask import Flask, redirect, url_for, session, render_template, send_from_directory
from config import Config
from db import init_db_pool, query_one
from utils.security import generate_csrf_token

# Configure application logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("HCMS")

def create_app():
    """Application factory initializing extensions, security handlers, and blueprints."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure uploads directory exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, "evidence"), exist_ok=True)
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, "completion"), exist_ok=True)

    # Attempt database connection pool initialization gracefully
    try:
        init_db_pool()
        logger.info("Database connection pool initialized.")
    except Exception as e:
        logger.warning("Could not initialize DB pool at startup (will retry on first request): %s", e)

    # Context processors to supply global helpers into all Jinja2 templates
    @app.context_processor
    def inject_template_globals():
        unread_count = 0
        user_id = session.get("user_id")
        if user_id:
            try:
                row = query_one(
                    "SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = %s AND is_read = 0", 
                    (user_id,)
                )
                unread_count = row["cnt"] if row else 0
            except Exception:
                unread_count = 0

        return {
            "csrf_token": generate_csrf_token,
            "unread_notif_count": unread_count,
            "app_name": Config.APP_NAME,
            "app_version": Config.APP_VERSION
        }

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.warden import warden_bp
    from routes.staff import staff_bp
    from routes.admin import admin_bp
    from routes.notifications import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(warden_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notifications_bp)

    # Root Gateway
    @app.route("/")
    def index():
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
        return redirect(url_for("auth.login"))

    # Secure Uploaded File Serving
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

    # Global HTTP Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("errors/500.html"), 500

    return app

app = create_app()

if __name__ == "__main__":
    print(f"\n========================================================")
    print(f" {Config.APP_NAME} v{Config.APP_VERSION}")
    print(f" Server running at: http://127.0.0.1:5000")
    print(f" Default Demo Accounts Password: password123")
    print(f"========================================================\n")
    app.run(host="127.0.0.1", port=5000, debug=True)

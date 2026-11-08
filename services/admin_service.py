"""
Hostel Complaint Management System (HCMS)
Administrator Domain Service (services/admin_service.py)

Manages system-wide governance, user account activation/deactivation,
hostels, rooms, categories, warden assignments, and high-level analytics.
"""

from db import query_one, query_all, execute_dml, get_db_cursor
from utils.security import hash_password
from utils.decorators import log_audit_event

class AdminService:

    @staticmethod
    def get_system_kpis() -> dict:
        """Retrieves global university-wide metrics for the executive dashboard."""
        sql = """
            SELECT 
                (SELECT COUNT(*) FROM students) AS total_students,
                (SELECT COUNT(*) FROM wardens) AS total_wardens,
                (SELECT COUNT(*) FROM staff) AS total_staff,
                (SELECT COUNT(*) FROM hostels WHERE is_active = 1) AS total_hostels,
                (SELECT COUNT(*) FROM rooms) AS total_rooms,
                (SELECT COUNT(*) FROM complaints) AS total_complaints,
                (SELECT COUNT(*) FROM complaints WHERE status = 'Resolved') AS total_resolved,
                (SELECT COUNT(*) FROM complaints WHERE status IN ('Submitted', 'Under Review')) AS total_pending,
                (SELECT COUNT(*) FROM complaints WHERE status IN ('Assigned', 'In Progress', 'Awaiting Verification')) AS total_in_progress,
                (SELECT COUNT(*) FROM complaints WHERE is_overdue = 1 AND status NOT IN ('Resolved', 'Rejected', 'Cancelled')) AS total_overdue,
                (SELECT ROUND(AVG(TIMESTAMPDIFF(HOUR, created_at, resolved_at)), 1) 
                 FROM complaints WHERE status = 'Resolved' AND resolved_at IS NOT NULL) AS avg_turnaround_hours
        """
        kpis = query_one(sql)
        if not kpis:
            return {}

        total = kpis.get("total_complaints") or 0
        resolved = kpis.get("total_resolved") or 0
        kpis["resolution_rate"] = round((resolved / total * 100), 1) if total > 0 else 0.0
        return kpis

    @staticmethod
    def get_all_users(role_filter=None, status_filter=None, search=None) -> list:
        """Queries users with joined role-specific details and optional filters."""
        where_clauses = ["1=1"]
        params = []

        if role_filter and role_filter != "all":
            where_clauses.append("u.role = %s")
            params.append(role_filter)

        if status_filter in ("0", "1"):
            where_clauses.append("u.is_active = %s")
            params.append(int(status_filter))

        if search:
            where_clauses.append("(u.first_name LIKE %s OR u.last_name LIKE %s OR u.email LIKE %s OR u.phone LIKE %s)")
            like_s = f"%{search}%"
            params.extend([like_s, like_s, like_s, like_s])

        where_sql = " AND ".join(where_clauses)
        sql = f"""
            SELECT 
                u.user_id, u.email, u.role, u.first_name, u.last_name, u.phone, 
                u.is_active, u.created_at,
                s.enrollment_number, s.branch, s.academic_year,
                w.warden_id, w.employee_code AS warden_emp_code, w.office_location,
                st.staff_id, st.employee_code AS staff_emp_code, st.specialization, st.is_available,
                h.code AS student_hostel_code,
                r.room_number AS student_room_number,
                (
                    SELECT GROUP_CONCAT(wh.code SEPARATOR ', ')
                    FROM hostel_wardens hw
                    JOIN hostels wh ON hw.hostel_id = wh.hostel_id
                    WHERE hw.warden_id = w.warden_id
                ) AS warden_hostel_codes
            FROM users u
            LEFT JOIN students s ON u.user_id = s.user_id
            LEFT JOIN hostels h ON s.hostel_id = h.hostel_id
            LEFT JOIN rooms r ON s.room_id = r.room_id
            LEFT JOIN wardens w ON u.user_id = w.user_id
            LEFT JOIN staff st ON u.user_id = st.user_id
            WHERE {where_sql}
            ORDER BY u.created_at DESC
        """
        return query_all(sql, tuple(params))

    @staticmethod
    def toggle_user_status(user_id: int, admin_user_id: int) -> tuple:
        """Activates or deactivates a user account."""
        if user_id == admin_user_id:
            return False, "You cannot deactivate your own administrative account."

        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT is_active, email, role FROM users WHERE user_id = %s FOR UPDATE", (user_id,))
            u = cursor.fetchone()
            if not u:
                return False, "User not found."

            new_status = 0 if u["is_active"] == 1 else 1
            cursor.execute("UPDATE users SET is_active = %s WHERE user_id = %s", (new_status, user_id))

        action_name = "USER_ACTIVATED" if new_status == 1 else "USER_DEACTIVATED"
        log_audit_event(action_name, "users", user_id, {"email": u["email"], "new_status": new_status})
        status_text = "activated" if new_status == 1 else "deactivated"
        return True, f"Account for {u['email']} successfully {status_text}."

    @staticmethod
    def create_staff_or_warden(data: dict) -> tuple:
        """Creates a new Warden or Maintenance Staff member profile atomically."""
        role = data.get("role")
        email = data.get("email", "").strip().lower()
        pwd = data.get("password")
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        phone = data.get("phone", "").strip()
        emp_code = data.get("employee_code", "").strip().upper()

        if role not in ("warden", "staff"):
            return False, "Invalid role selection."
        if not email or not pwd or len(pwd) < 8 or not emp_code:
            return False, "Please fill in all mandatory fields with a password of at least 8 characters."

        # Check existing email
        if query_one("SELECT user_id FROM users WHERE email = %s", (email,)):
            return False, "Email address is already in use."

        pwd_hash = hash_password(pwd)
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute(
                "INSERT INTO users (email, password_hash, role, first_name, last_name, phone, is_active) VALUES (%s, %s, %s, %s, %s, %s, 1)",
                (email, pwd_hash, role, first_name, last_name, phone)
            )
            new_uid = cursor.lastrowid

            if role == "warden":
                office = data.get("office_location", "Warden Office")
                cursor.execute(
                    "INSERT INTO wardens (user_id, employee_code, office_location) VALUES (%s, %s, %s)",
                    (new_uid, emp_code, office)
                )
                new_warden_id = cursor.lastrowid
                hostel_id = data.get("hostel_id")
                if hostel_id:
                    cursor.execute(
                        "INSERT INTO hostel_wardens (hostel_id, warden_id, assigned_date) VALUES (%s, %s, CURDATE())",
                        (int(hostel_id), new_warden_id)
                    )
                # Welcome alert
                cursor.execute(
                    "INSERT INTO notifications (user_id, title, message) VALUES (%s, %s, %s)",
                    (new_uid, "Welcome to HCMS", f"Warden account created by administrator. Code: {emp_code}. You may now triage hostel complaints.")
                )
            elif role == "staff":
                spec = data.get("specialization", "general")
                cursor.execute(
                    "INSERT INTO staff (user_id, employee_code, specialization, is_available) VALUES (%s, %s, %s, 1)",
                    (new_uid, emp_code, spec)
                )
                # Welcome alert
                cursor.execute(
                    "INSERT INTO notifications (user_id, title, message) VALUES (%s, %s, %s)",
                    (new_uid, "Welcome to HCMS", f"Maintenance Staff technician account ({spec.capitalize()}) registered by administrator. Work orders will appear here.")
                )

        log_audit_event("CREATE_USER", "users", new_uid, {"role": role, "email": email, "emp_code": emp_code})
        return True, f"Successfully created new {role.capitalize()} account ({email})."

    @staticmethod
    def get_all_hostels_with_stats() -> list:
        """Retrieves hostels with floor counts, total rooms, occupancy, and assigned wardens."""
        sql = """
            SELECT 
                h.hostel_id, h.name, h.code, h.type, h.total_floors, h.is_active,
                COUNT(DISTINCT r.room_id) AS total_rooms,
                IFNULL(SUM(r.current_occupancy), 0) AS total_students_housed,
                IFNULL(SUM(r.capacity), 0) AS total_capacity,
                COUNT(DISTINCT c.complaint_id) AS total_complaints,
                SUM(CASE WHEN c.status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_complaints
            FROM hostels h
            LEFT JOIN rooms r ON h.hostel_id = r.hostel_id
            LEFT JOIN complaints c ON h.hostel_id = c.hostel_id
            GROUP BY h.hostel_id, h.name, h.code, h.type, h.total_floors, h.is_active
            ORDER BY h.name ASC
        """
        hostels = query_all(sql)
        for h in hostels:
            # Query assigned wardens for this hostel
            sql_w = """
                SELECT w.warden_id, w.employee_code, CONCAT(u.first_name, ' ', u.last_name) AS warden_name
                FROM hostel_wardens hw
                JOIN wardens w ON hw.warden_id = w.warden_id
                JOIN users u ON w.user_id = u.user_id
                WHERE hw.hostel_id = %s
            """
            h["assigned_wardens"] = query_all(sql_w, (h["hostel_id"],))
        return hostels

    @staticmethod
    def create_hostel(name: str, code: str, hostel_type: str, total_floors: int) -> tuple:
        """Creates a new residential hostel block."""
        if not name or not code or hostel_type not in ('boys', 'girls', 'co-ed'):
            return False, "Invalid hostel details."

        existing = query_one("SELECT hostel_id FROM hostels WHERE name = %s OR code = %s", (name, code))
        if existing:
            return False, "A hostel with this name or code already exists."

        sql = "INSERT INTO hostels (name, code, type, total_floors, is_active) VALUES (%s, %s, %s, %s, 1)"
        execute_dml(sql, (name.strip(), code.strip().upper(), hostel_type, total_floors))
        log_audit_event("CREATE_HOSTEL", "hostels", None, {"name": name, "code": code})
        return True, f"Hostel '{name}' ({code}) registered successfully."

    @staticmethod
    def assign_warden_to_hostel(hostel_id: int, warden_id: int) -> tuple:
        """Maps a warden to a hostel block in hostel_wardens."""
        sql = """
            INSERT INTO hostel_wardens (hostel_id, warden_id, assigned_date)
            VALUES (%s, %s, CURDATE())
            ON DUPLICATE KEY UPDATE assigned_date = CURDATE()
        """
        execute_dml(sql, (hostel_id, warden_id))
        log_audit_event("ASSIGN_HOSTEL_WARDEN", "hostel_wardens", hostel_id, {"warden_id": warden_id})
        return True, "Warden successfully assigned to hostel block."

    @staticmethod
    def remove_warden_from_hostel(hostel_id: int, warden_id: int) -> tuple:
        """Removes warden mapping from hostel_wardens."""
        sql = "DELETE FROM hostel_wardens WHERE hostel_id = %s AND warden_id = %s"
        execute_dml(sql, (hostel_id, warden_id))
        log_audit_event("REMOVE_HOSTEL_WARDEN", "hostel_wardens", hostel_id, {"warden_id": warden_id})
        return True, "Warden assignment removed."

    @staticmethod
    def get_hostel_rooms(hostel_id: int) -> list:
        """Retrieves all rooms in a hostel."""
        sql = """
            SELECT room_id, hostel_id, room_number, floor_number, capacity, current_occupancy
            FROM rooms
            WHERE hostel_id = %s
            ORDER BY floor_number ASC, room_number ASC
        """
        return query_all(sql, (hostel_id,))

    @staticmethod
    def create_room(hostel_id: int, room_number: str, floor_number: int, capacity: int) -> tuple:
        """Adds a room to a hostel block."""
        existing = query_one(
            "SELECT room_id FROM rooms WHERE hostel_id = %s AND room_number = %s", 
            (hostel_id, room_number)
        )
        if existing:
            return False, f"Room {room_number} already exists in this hostel block."

        sql = """
            INSERT INTO rooms (hostel_id, room_number, floor_number, capacity, current_occupancy)
            VALUES (%s, %s, %s, %s, 0)
        """
        execute_dml(sql, (hostel_id, room_number.strip(), floor_number, capacity))
        log_audit_event("CREATE_ROOM", "rooms", None, {"hostel_id": hostel_id, "room": room_number})
        return True, f"Room {room_number} successfully created."

    @staticmethod
    def get_all_categories_with_stats() -> list:
        """Retrieves master categories and complaint volume breakdown."""
        sql = """
            SELECT 
                cat.category_id, cat.name, cat.description, cat.default_sla_hours, 
                cat.default_priority, cat.is_active,
                COUNT(c.complaint_id) AS total_complaints,
                SUM(CASE WHEN c.status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_complaints,
                ROUND(AVG(CASE WHEN c.status = 'Resolved' AND c.resolved_at IS NOT NULL 
                               THEN TIMESTAMPDIFF(HOUR, c.created_at, c.resolved_at) ELSE NULL END), 1) AS avg_turnaround
            FROM complaint_categories cat
            LEFT JOIN complaints c ON cat.category_id = c.category_id
            GROUP BY cat.category_id, cat.name, cat.description, cat.default_sla_hours, cat.default_priority, cat.is_active
            ORDER BY total_complaints DESC
        """
        return query_all(sql)

    @staticmethod
    def create_category(name: str, sla_hours: int, default_priority: str, description: str) -> tuple:
        """Creates a new complaint category with SLA."""
        existing = query_one("SELECT category_id FROM complaint_categories WHERE name = %s", (name,))
        if existing:
            return False, f"Category '{name}' already exists."

        sql = """
            INSERT INTO complaint_categories (name, description, default_sla_hours, default_priority, is_active)
            VALUES (%s, %s, %s, %s, 1)
        """
        execute_dml(sql, (name.strip(), description.strip(), sla_hours, default_priority))
        log_audit_event("CREATE_CATEGORY", "complaint_categories", None, {"name": name, "sla": sla_hours})
        return True, f"Category '{name}' created."

    @staticmethod
    def get_audit_logs(limit: int = 50, action_filter: str = None) -> list:
        """Retrieves system-wide immutable security audit logs."""
        where = ""
        params = []
        if action_filter and action_filter != "all":
            where = "WHERE al.action = %s"
            params.append(action_filter)
        params.append(limit)

        sql = f"""
            SELECT 
                al.log_id, al.user_id, al.action, al.target_entity, al.target_id,
                al.ip_address, al.user_agent, al.details_json, al.created_at,
                u.email AS user_email, u.role AS user_role,
                CONCAT(u.first_name, ' ', u.last_name) AS actor_name
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.user_id
            {where}
            ORDER BY al.created_at DESC
            LIMIT %s
        """
        return query_all(sql, tuple(params))

    @staticmethod
    def get_advanced_analytics() -> dict:
        """Executes DBMS analytical queries for charts and visualizations."""
        # 1. Category Distribution
        sql_cat = """
            SELECT cat.name AS label, COUNT(c.complaint_id) AS val
            FROM complaint_categories cat
            LEFT JOIN complaints c ON cat.category_id = c.category_id
            GROUP BY cat.category_id, cat.name
            HAVING val > 0
            ORDER BY val DESC
        """
        cat_dist = query_all(sql_cat)

        # 2. Staff Performance Ranking using Window Function DENSE_RANK()
        sql_staff = """
            WITH StaffStats AS (
                SELECT 
                    st.staff_id,
                    CONCAT(u.first_name, ' ', u.last_name) AS staff_name,
                    st.specialization,
                    COUNT(ca.assignment_id) AS total_assigned,
                    SUM(CASE WHEN ca.status = 'completed' THEN 1 ELSE 0 END) AS completed_count,
                    ROUND(AVG(CASE WHEN ca.status = 'completed' THEN TIMESTAMPDIFF(HOUR, ca.assigned_at, ca.completed_at) END), 1) AS avg_hours,
                    ROUND(AVG(cf.rating), 2) AS avg_rating
                FROM staff st
                JOIN users u ON st.user_id = u.user_id
                LEFT JOIN complaint_assignments ca ON st.staff_id = ca.staff_id
                LEFT JOIN complaints c ON ca.complaint_id = c.complaint_id
                LEFT JOIN complaint_feedback cf ON c.complaint_id = cf.complaint_id
                GROUP BY st.staff_id, staff_name, st.specialization
            )
            SELECT *,
                DENSE_RANK() OVER (ORDER BY completed_count DESC, avg_hours ASC) AS efficiency_rank
            FROM StaffStats
            ORDER BY efficiency_rank ASC
        """
        staff_ranking = query_all(sql_staff)

        # 3. Hostel Comparison
        sql_hostel = """
            SELECT 
                h.code AS label,
                COUNT(c.complaint_id) AS total,
                SUM(CASE WHEN c.status = 'Resolved' THEN 1 ELSE 0 END) AS resolved,
                SUM(CASE WHEN c.is_overdue = 1 THEN 1 ELSE 0 END) AS overdue
            FROM hostels h
            LEFT JOIN complaints c ON h.hostel_id = c.hostel_id
            GROUP BY h.hostel_id, h.code
            ORDER BY total DESC
        """
        hostel_comp = query_all(sql_hostel)

        return {
            "categories": cat_dist,
            "staff_ranking": staff_ranking,
            "hostels": hostel_comp
        }

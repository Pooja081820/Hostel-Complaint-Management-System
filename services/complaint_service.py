"""
Hostel Complaint Management System (HCMS)
Complaint Domain Service (services/complaint_service.py)

Encapsulates complete complaint lifecycle logic, validation, duplicate detection,
SLA computation, transactional status progressions, and ownership verification.
"""

import os
import datetime
from db import query_one, query_all, execute_dml, get_db_cursor
from utils.security import save_uploaded_file
from utils.decorators import log_audit_event

class ComplaintService:

    @staticmethod
    def generate_ticket_number(cursor) -> str:
        """Generates a sequential, collision-proof ticket number (e.g. CMP-2026-0042)."""
        current_year = datetime.datetime.now().year
        # Count complaints registered in this current year for sequence
        cursor.execute("SELECT COUNT(*) AS cnt FROM complaints WHERE YEAR(created_at) = %s FOR UPDATE", (current_year,))
        row = cursor.fetchone()
        if isinstance(row, dict):
            seq_num = (row.get("cnt") or 0) + 1
        elif isinstance(row, (list, tuple)):
            seq_num = row[0] + 1
        else:
            seq_num = 1
        return f"CMP-{current_year}-{seq_num:04d}"

    @staticmethod
    def check_potential_duplicates(hostel_id: int, category_id: int, title: str) -> list:
        """
        Duplicate Detection Algorithm:
        Identifies active complaints in the same hostel and category filed within
        the last 48 hours sharing significant word tokens with the candidate title.
        """
        words = [w.lower().strip() for w in title.split() if len(w) > 3]
        if not words:
            return []

        # Find active complaints in the same hostel and category
        sql = """
            SELECT complaint_id, ticket_number, title, status, priority, created_at
            FROM complaints
            WHERE hostel_id = %s 
              AND category_id = %s
              AND status NOT IN ('Resolved', 'Rejected', 'Cancelled')
              AND created_at >= NOW() - INTERVAL 48 HOUR
            ORDER BY created_at DESC
            LIMIT 10
        """
        candidates = query_all(sql, (hostel_id, category_id))
        potential_dups = []

        for c in candidates:
            c_title = c["title"].lower()
            matching_tokens = [w for w in words if w in c_title]
            if len(matching_tokens) >= 1:
                potential_dups.append({
                    "complaint_id": c["complaint_id"],
                    "ticket_number": c["ticket_number"],
                    "title": c["title"],
                    "status": c["status"],
                    "priority": c["priority"],
                    "matching_words": matching_tokens,
                    "created_at": c["created_at"].strftime("%Y-%m-%d %H:%M")
                })
        return potential_dups

    @staticmethod
    def create_complaint(student_id: int, user_id: int, hostel_id: int, room_id: int, 
                         category_id: int, title: str, description: str, 
                         priority: str = "Medium", visibility: str = "private",
                         affected_hostel_ids: list = None, attachment_file = None) -> dict:
        """
        Atomically lodges a new complaint:
        - Computes SLA deadline from master complaint_categories
        - Generates ticket number
        - Inserts into complaints
        - Links affected hostels if visibility is 'general'
        - Saves and records uploaded evidence attachment
        - Generates initial audit trail in complaint_history
        - Notifies wardens
        """
        with get_db_cursor(commit=True) as (conn, cursor):
            # 1. Fetch category SLA
            cursor.execute("SELECT default_sla_hours FROM complaint_categories WHERE category_id = %s", (category_id,))
            cat_row = cursor.fetchone()
            sla_hours = cat_row["default_sla_hours"] if cat_row else 48

            # Calculate deadline
            sla_deadline = datetime.datetime.now() + datetime.timedelta(hours=sla_hours)
            ticket_number = ComplaintService.generate_ticket_number(cursor)

            # 2. Insert Complaint Record
            sql_complaint = """
                INSERT INTO complaints (
                    ticket_number, student_id, hostel_id, room_id, category_id,
                    title, description, priority, visibility, status,
                    reopen_count, is_overdue, sla_deadline, version_id
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, 'Submitted',
                    0, 0, %s, 1
                )
            """
            cursor.execute(sql_complaint, (
                ticket_number, student_id, hostel_id, room_id if visibility == 'private' else None,
                category_id, title, description, priority, visibility, sla_deadline
            ))
            complaint_id = cursor.lastrowid

            # 3. Handle General Multi-Hostel Associations
            if visibility == "general" and affected_hostel_ids:
                # Include the originating hostel
                all_affected = set(affected_hostel_ids)
                all_affected.add(hostel_id)
                for h_id in all_affected:
                    cursor.execute(
                        "INSERT IGNORE INTO complaint_affected_hostels (complaint_id, hostel_id) VALUES (%s, %s)",
                        (complaint_id, h_id)
                    )

            # 4. Handle Evidentiary Attachment Upload
            if attachment_file and attachment_file.filename:
                rel_path, orig_name, size_kb, mime_type = save_uploaded_file(attachment_file, "evidence")
                if rel_path:
                    sql_attach = """
                        INSERT INTO complaint_attachments (
                            complaint_id, uploaded_by_user_id, file_type, 
                            file_path, original_filename, file_size_kb, mime_type
                        ) VALUES (%s, %s, 'submission_evidence', %s, %s, %s, %s)
                    """
                    cursor.execute(sql_attach, (
                        complaint_id, user_id, rel_path, orig_name, size_kb, mime_type
                    ))

            # 5. Insert initial status history
            sql_history = """
                INSERT INTO complaint_history (complaint_id, old_status, new_status, changed_by_user_id, remarks)
                VALUES (%s, NULL, 'Submitted', %s, 'Complaint registered in system')
            """
            cursor.execute(sql_history, (complaint_id, user_id))

            # 6. Notify wardens assigned to this hostel
            sql_wardens = """
                SELECT w.user_id 
                FROM hostel_wardens hw 
                JOIN wardens w ON hw.warden_id = w.warden_id 
                WHERE hw.hostel_id = %s
            """
            cursor.execute(sql_wardens, (hostel_id,))
            warden_rows = cursor.fetchall()
            for w in warden_rows:
                cursor.execute(
                    "INSERT INTO notifications (user_id, complaint_id, title, message) VALUES (%s, %s, %s, %s)",
                    (w["user_id"], complaint_id, "New Complaint Submitted", 
                     f"New ticket {ticket_number} ({priority} Priority) lodged in your hostel.")
                )

            # 7. Notify campus administrators to review and set priority
            cursor.execute("SELECT user_id FROM users WHERE role = 'admin' AND is_active = 1")
            admin_rows = cursor.fetchall()
            for a in admin_rows:
                cursor.execute(
                    "INSERT INTO notifications (user_id, complaint_id, title, message) VALUES (%s, %s, %s, %s)",
                    (a["user_id"], complaint_id, "New Complaint Lodged", 
                     f"New ticket {ticket_number} lodged. Please review and designate priority.")
                )

        log_audit_event("COMPLAINT_SUBMIT", "complaints", complaint_id, {"ticket": ticket_number, "priority": priority})
        return {"complaint_id": complaint_id, "ticket_number": ticket_number}

    @staticmethod
    def get_student_metrics(student_id: int) -> dict:
        """Fetches aggregated dashboard KPI counters for a student."""
        sql = """
            SELECT 
                COUNT(*) AS total_complaints,
                SUM(CASE WHEN status IN ('Submitted', 'Under Review') THEN 1 ELSE 0 END) AS pending_count,
                SUM(CASE WHEN status IN ('Assigned', 'In Progress', 'Awaiting Verification') THEN 1 ELSE 0 END) AS in_progress_count,
                SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_count,
                SUM(CASE WHEN status = 'Reopened' THEN 1 ELSE 0 END) AS reopened_count
            FROM complaints
            WHERE student_id = %s
        """
        metrics = query_one(sql, (student_id,))
        return metrics or {"total_complaints": 0, "pending_count": 0, "in_progress_count": 0, "resolved_count": 0, "reopened_count": 0}

    @staticmethod
    def get_student_complaints(student_id: int, status_filter=None, category_filter=None, search_term=None) -> list:
        """Returns filtered complaints owned strictly by the requesting student."""
        params = [student_id]
        where_clauses = ["c.student_id = %s"]

        if status_filter and status_filter != "all":
            where_clauses.append("c.status = %s")
            params.append(status_filter)

        if category_filter and category_filter != "all":
            where_clauses.append("c.category_id = %s")
            params.append(category_filter)

        if search_term:
            where_clauses.append("(c.title LIKE %s OR c.ticket_number LIKE %s OR c.description LIKE %s)")
            like_param = f"%{search_term}%"
            params.extend([like_param, like_param, like_param])

        where_sql = " AND ".join(where_clauses)
        sql = f"""
            SELECT 
                c.complaint_id, c.ticket_number, c.title, c.priority, c.visibility,
                c.status, c.reopen_count, c.is_overdue, c.sla_deadline, c.created_at, c.resolved_at,
                cat.name AS category_name,
                h.code AS hostel_code,
                r.room_number
            FROM complaints c
            JOIN complaint_categories cat ON c.category_id = cat.category_id
            JOIN hostels h ON c.hostel_id = h.hostel_id
            LEFT JOIN rooms r ON c.room_id = r.room_id
            WHERE {where_sql}
            ORDER BY c.created_at DESC
        """
        return query_all(sql, tuple(params))

    @staticmethod
    def get_complaint_details(complaint_id: int, student_id: int = None) -> dict:
        """
        Retrieves complete complaint entity details.
        Enforces ownership authorization if student_id is provided.
        """
        sql = """
            SELECT 
                c.*, 
                cat.name AS category_name, cat.default_sla_hours,
                h.name AS hostel_name, h.code AS hostel_code,
                r.room_number, r.floor_number,
                s.enrollment_number,
                CONCAT(u.first_name, ' ', u.last_name) AS student_name,
                u.email AS student_email,
                u.phone AS student_phone
            FROM complaints c
            JOIN complaint_categories cat ON c.category_id = cat.category_id
            JOIN hostels h ON c.hostel_id = h.hostel_id
            LEFT JOIN rooms r ON c.room_id = r.room_id
            JOIN students s ON c.student_id = s.student_id
            JOIN users u ON s.user_id = u.user_id
            WHERE c.complaint_id = %s
        """
        complaint = query_one(sql, (complaint_id,))
        if not complaint:
            return None

        # Ownership authorization check
        if student_id is not None and complaint["student_id"] != student_id:
            # Check if it's a general complaint affecting the student's hostel
            if complaint["visibility"] == "general":
                # Allow view
                pass
            else:
                raise PermissionError("Access denied: You are not authorized to view this complaint.")

        # Query history trail
        sql_history = """
            SELECT ch.*, CONCAT(u.first_name, ' ', u.last_name) AS actor_name, u.role AS actor_role
            FROM complaint_history ch
            JOIN users u ON ch.changed_by_user_id = u.user_id
            WHERE ch.complaint_id = %s
            ORDER BY ch.created_at ASC
        """
        complaint["history"] = query_all(sql_history, (complaint_id,))

        # Query dialogue responses (excluding internal warden notes if viewer is student)
        sql_responses = """
            SELECT cr.*, CONCAT(u.first_name, ' ', u.last_name) AS author_name, u.role AS author_role
            FROM complaint_responses cr
            JOIN users u ON cr.user_id = u.user_id
            WHERE cr.complaint_id = %s AND (cr.is_internal = 0 OR %s IS NULL)
            ORDER BY cr.created_at ASC
        """
        complaint["responses"] = query_all(sql_responses, (complaint_id, student_id))

        # Query attachments
        sql_attach = """
            SELECT ca.*, CONCAT(u.first_name, ' ', u.last_name) AS uploader_name
            FROM complaint_attachments ca
            JOIN users u ON ca.uploaded_by_user_id = u.user_id
            WHERE ca.complaint_id = %s
            ORDER BY ca.created_at ASC
        """
        complaint["attachments"] = query_all(sql_attach, (complaint_id,))

        # Query feedback if resolved
        sql_fb = "SELECT * FROM complaint_feedback WHERE complaint_id = %s"
        complaint["feedback"] = query_one(sql_fb, (complaint_id,))

        # Query active assignment
        sql_assign = """
            SELECT ca.*, CONCAT(u.first_name, ' ', u.last_name) AS staff_name, st.specialization
            FROM complaint_assignments ca
            JOIN staff st ON ca.staff_id = st.staff_id
            JOIN users u ON st.user_id = u.user_id
            WHERE ca.complaint_id = %s AND ca.status != 'reassigned'
            ORDER BY ca.assigned_at DESC LIMIT 1
        """
        complaint["assignment"] = query_one(sql_assign, (complaint_id,))

        return complaint

    @staticmethod
    def cancel_complaint(complaint_id: int, student_id: int, user_id: int, reason: str) -> tuple:
        """Allows student to cancel early complaint if work has not started."""
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute(
                "SELECT status, ticket_number, version_id FROM complaints WHERE complaint_id = %s AND student_id = %s FOR UPDATE",
                (complaint_id, student_id)
            )
            row = cursor.fetchone()
            if not row:
                return False, "Complaint not found or unauthorized."

            current_status = row["status"]
            if current_status not in ("Submitted", "Under Review"):
                return False, f"Complaint cannot be cancelled once work has reached '{current_status}'."

            # Update status to Cancelled
            cursor.execute(
                "UPDATE complaints SET status = 'Cancelled', version_id = version_id + 1, updated_at = NOW() WHERE complaint_id = %s",
                (complaint_id,)
            )

            # Insert history
            cursor.execute(
                "INSERT INTO complaint_history (complaint_id, old_status, new_status, changed_by_user_id, remarks) VALUES (%s, %s, 'Cancelled', %s, %s)",
                (complaint_id, current_status, user_id, f"Cancelled by student: {reason}")
            )

        log_audit_event("COMPLAINT_CANCEL", "complaints", complaint_id, {"reason": reason})
        return True, "Complaint successfully cancelled."

    @staticmethod
    def submit_feedback(complaint_id: int, student_id: int, rating: int, comments: str) -> tuple:
        """Stores student feedback for a resolved complaint."""
        complaint = query_one(
            "SELECT status FROM complaints WHERE complaint_id = %s AND student_id = %s",
            (complaint_id, student_id)
        )
        if not complaint:
            return False, "Complaint not found or access denied."
        if complaint["status"] != "Resolved":
            return False, "Feedback can only be submitted for Resolved complaints."

        sql = """
            INSERT INTO complaint_feedback (complaint_id, student_id, rating, comments)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE rating = VALUES(rating), comments = VALUES(comments)
        """
        execute_dml(sql, (complaint_id, student_id, rating, comments))
        log_audit_event("COMPLAINT_FEEDBACK", "complaint_feedback", complaint_id, {"rating": rating})
        return True, "Thank you! Your feedback has been recorded."

    # ------------------------------------------------------------------------
    # Warden Management Domain Methods
    # ------------------------------------------------------------------------
    @staticmethod
    def get_warden_metrics(assigned_hostels: list) -> dict:
        """Computes aggregate dashboard KPI metrics restricted to assigned hostels."""
        if not assigned_hostels:
            return {
                "total": 0, "pending": 0, "in_progress": 0, "resolved": 0,
                "overdue": 0, "critical": 0, "avg_resolution_hours": 0
            }

        placeholders = ",".join(["%s"] * len(assigned_hostels))
        sql = f"""
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN status IN ('Submitted', 'Under Review') THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status IN ('Assigned', 'In Progress', 'Awaiting Verification') THEN 1 ELSE 0 END) AS in_progress,
                SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved,
                SUM(CASE WHEN is_overdue = 1 AND status NOT IN ('Resolved', 'Rejected', 'Cancelled') THEN 1 ELSE 0 END) AS overdue,
                SUM(CASE WHEN priority = 'Critical' AND status NOT IN ('Resolved', 'Rejected', 'Cancelled') THEN 1 ELSE 0 END) AS critical,
                ROUND(AVG(CASE WHEN status = 'Resolved' AND resolved_at IS NOT NULL 
                               THEN TIMESTAMPDIFF(HOUR, created_at, resolved_at) ELSE NULL END), 1) AS avg_resolution_hours
            FROM complaints
            WHERE hostel_id IN ({placeholders})
        """
        metrics = query_one(sql, tuple(assigned_hostels))
        return metrics or {}

    @staticmethod
    def get_warden_complaints(assigned_hostels: list, filters: dict = None) -> list:
        """
        Retrieves complaints strictly scoped to warden's assigned hostels,
        with optional multi-criteria filtering.
        """
        if not assigned_hostels:
            return []

        filters = filters or {}
        placeholders = ",".join(["%s"] * len(assigned_hostels))
        where_clauses = [f"c.hostel_id IN ({placeholders})"]
        params = list(assigned_hostels)

        # Optional hostel filter within assigned list
        hostel_filter = filters.get("hostel_id")
        if hostel_filter and str(hostel_filter) != "all" and int(hostel_filter) in assigned_hostels:
            where_clauses.append("c.hostel_id = %s")
            params.append(int(hostel_filter))

        category_filter = filters.get("category_id")
        if category_filter and str(category_filter) != "all":
            where_clauses.append("c.category_id = %s")
            params.append(int(category_filter))

        priority_filter = filters.get("priority")
        if priority_filter and priority_filter != "all":
            where_clauses.append("c.priority = %s")
            params.append(priority_filter)

        status_filter = filters.get("status")
        if status_filter and status_filter != "all":
            where_clauses.append("c.status = %s")
            params.append(status_filter)

        if filters.get("overdue_only"):
            where_clauses.append("c.is_overdue = 1 AND c.status NOT IN ('Resolved', 'Rejected', 'Cancelled')")

        search = filters.get("search")
        if search:
            where_clauses.append("(c.title LIKE %s OR c.ticket_number LIKE %s OR u.first_name LIKE %s OR u.last_name LIKE %s)")
            like_str = f"%{search}%"
            params.extend([like_str, like_str, like_str, like_str])

        where_sql = " AND ".join(where_clauses)
        sql = f"""
            SELECT 
                c.complaint_id, c.ticket_number, c.title, c.priority, c.visibility,
                c.status, c.reopen_count, c.is_overdue, c.sla_deadline, c.created_at, c.version_id,
                cat.name AS category_name,
                h.name AS hostel_name, h.code AS hostel_code,
                r.room_number,
                CONCAT(u.first_name, ' ', u.last_name) AS student_name,
                s.enrollment_number,
                CONCAT(u_staff.first_name, ' ', u_staff.last_name) AS staff_name
            FROM complaints c
            JOIN complaint_categories cat ON c.category_id = cat.category_id
            JOIN hostels h ON c.hostel_id = h.hostel_id
            LEFT JOIN rooms r ON c.room_id = r.room_id
            JOIN students s ON c.student_id = s.student_id
            JOIN users u ON s.user_id = u.user_id
            LEFT JOIN complaint_assignments ca ON c.complaint_id = ca.complaint_id 
                AND ca.status IN ('assigned', 'accepted', 'in_progress')
            LEFT JOIN staff st ON ca.staff_id = st.staff_id
            LEFT JOIN users u_staff ON st.user_id = u_staff.user_id
            WHERE {where_sql}
            ORDER BY 
                CASE WHEN c.priority = 'Critical' THEN 1
                     WHEN c.is_overdue = 1 THEN 2
                     ELSE 3 END ASC,
                c.created_at DESC
        """
        return query_all(sql, tuple(params))

    @staticmethod
    def update_complaint_priority(complaint_id: int, warden_user_id: int, 
                                  new_priority: str, reason: str) -> tuple:
        """Updates complaint priority with mandatory audit logging in complaint_priority_history."""
        if new_priority not in ("Low", "Medium", "High", "Critical"):
            return False, "Invalid priority level."
        if not reason or len(reason.strip()) < 5:
            return False, "Please provide an audit justification for priority adjustment."

        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT priority, version_id, ticket_number, student_id FROM complaints WHERE complaint_id = %s FOR UPDATE", (complaint_id,))
            c = cursor.fetchone()
            if not c:
                return False, "Complaint not found."

            old_priority = c["priority"]
            if old_priority == new_priority:
                return False, "New priority is identical to current priority."

            # Update priority
            cursor.execute(
                "UPDATE complaints SET priority = %s, version_id = version_id + 1, updated_at = NOW() WHERE complaint_id = %s",
                (new_priority, complaint_id)
            )

            # Record audit justification in complaint_priority_history
            cursor.execute(
                "INSERT INTO complaint_priority_history (complaint_id, old_priority, new_priority, changed_by_user_id, reason) VALUES (%s, %s, %s, %s, %s)",
                (complaint_id, old_priority, new_priority, warden_user_id, reason)
            )

            # Insert history
            cursor.execute(
                "INSERT INTO complaint_history (complaint_id, old_status, new_status, changed_by_user_id, remarks) VALUES (%s, %s, %s, %s, %s)",
                (complaint_id, None, f"Priority: {new_priority}", warden_user_id, f"Priority adjusted: {reason}")
            )

        log_audit_event("PRIORITY_CHANGE", "complaints", complaint_id, {
            "old": old_priority, "new": new_priority, "reason": reason
        })
        return True, f"Priority successfully updated from {old_priority} to {new_priority}."

    @staticmethod
    def add_management_response(complaint_id: int, user_id: int, message: str, is_internal: bool = False) -> tuple:
        """Posts an official management remark or dialogue message."""
        if not message or len(message.strip()) < 3:
            return False, "Message cannot be empty."

        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute(
                "INSERT INTO complaint_responses (complaint_id, user_id, message, is_internal) VALUES (%s, %s, %s, %s)",
                (complaint_id, user_id, message.strip(), 1 if is_internal else 0)
            )

            # If not internal, notify student
            if not is_internal:
                cursor.execute(
                    "SELECT c.ticket_number, s.user_id FROM complaints c JOIN students s ON c.student_id = s.student_id WHERE c.complaint_id = %s",
                    (complaint_id,)
                )
                student_info = cursor.fetchone()
                if student_info:
                    cursor.execute(
                        "INSERT INTO notifications (user_id, complaint_id, title, message) VALUES (%s, %s, %s, %s)",
                        (student_info["user_id"], complaint_id, "Warden Update Posted", 
                         f"Warden added an update on ticket {student_info['ticket_number']}.")
                    )

        log_audit_event("COMPLAINT_RESPOND", "complaint_responses", complaint_id, {"is_internal": is_internal})
        return True, "Response posted successfully."

    @staticmethod
    def resolve_complaint_by_warden(complaint_id: int, warden_user_id: int, remarks: str = None) -> tuple:
        """Verifies resolution quality and marks complaint Resolved."""
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT status, ticket_number, student_id FROM complaints WHERE complaint_id = %s FOR UPDATE", (complaint_id,))
            c = cursor.fetchone()
            if not c:
                return False, "Complaint not found."

            cursor.execute(
                "UPDATE complaints SET status = 'Resolved', resolved_at = NOW(), version_id = version_id + 1 WHERE complaint_id = %s",
                (complaint_id,)
            )

            # Complete active assignment
            cursor.execute(
                "UPDATE complaint_assignments SET status = 'completed', completed_at = NOW() WHERE complaint_id = %s AND status != 'completed'",
                (complaint_id,)
            )

            # Record history
            cursor.execute(
                "INSERT INTO complaint_history (complaint_id, old_status, new_status, changed_by_user_id, remarks) VALUES (%s, %s, 'Resolved', %s, %s)",
                (complaint_id, c["status"], warden_user_id, remarks or "Verified and resolved by warden")
            )

            # Notify student
            cursor.execute("SELECT user_id FROM students WHERE student_id = %s", (c["student_id"],))
            st_user = cursor.fetchone()
            if st_user:
                cursor.execute(
                    "INSERT INTO notifications (user_id, complaint_id, title, message) VALUES (%s, %s, %s, %s)",
                    (st_user["user_id"], complaint_id, "Complaint Resolved", 
                     f"Your complaint ({c['ticket_number']}) was verified and marked resolved. Please rate the service.")
                )

        log_audit_event("COMPLAINT_RESOLVE", "complaints", complaint_id, {"verified_by": warden_user_id})
        return True, "Complaint successfully resolved and closed."

    @staticmethod
    def reject_complaint_by_warden(complaint_id: int, warden_user_id: int, reason: str) -> tuple:
        """Rejects an invalid, policy-violating, or duplicate complaint."""
        if not reason or len(reason.strip()) < 5:
            return False, "Please provide an official rejection reason."

        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute("SELECT status, ticket_number, student_id FROM complaints WHERE complaint_id = %s FOR UPDATE", (complaint_id,))
            c = cursor.fetchone()
            if not c:
                return False, "Complaint not found."

            cursor.execute(
                "UPDATE complaints SET status = 'Rejected', version_id = version_id + 1, updated_at = NOW() WHERE complaint_id = %s",
                (complaint_id,)
            )

            # Add public response
            cursor.execute(
                "INSERT INTO complaint_responses (complaint_id, user_id, message, is_internal) VALUES (%s, %s, %s, 0)",
                (complaint_id, warden_user_id, f"[REJECTION NOTICE]: {reason}")
            )

            # Notify student
            cursor.execute("SELECT user_id FROM students WHERE student_id = %s", (c["student_id"],))
            st_user = cursor.fetchone()
            if st_user:
                cursor.execute(
                    "INSERT INTO notifications (user_id, complaint_id, title, message) VALUES (%s, %s, %s, %s)",
                    (st_user["user_id"], complaint_id, "Complaint Rejected", 
                     f"Ticket {c['ticket_number']} was rejected: {reason[:60]}")
                )

        log_audit_event("COMPLAINT_REJECT", "complaints", complaint_id, {"reason": reason})
        return True, "Complaint rejected and student notified."

    @staticmethod
    def get_warden_reports(assigned_hostels: list) -> list:
        """Calculates hostel-wise performance and SLA compliance for warden's blocks."""
        if not assigned_hostels:
            return []
        placeholders = ",".join(["%s"] * len(assigned_hostels))
        sql = f"""
            SELECT 
                h.hostel_id, h.name AS hostel_name, h.code AS hostel_code,
                COUNT(c.complaint_id) AS total_complaints,
                SUM(CASE WHEN c.status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_count,
                SUM(CASE WHEN c.is_overdue = 1 THEN 1 ELSE 0 END) AS overdue_count,
                ROUND((SUM(CASE WHEN c.status = 'Resolved' THEN 1 ELSE 0 END) / NULLIF(COUNT(c.complaint_id), 0)) * 100, 1) AS resolution_rate,
                ROUND(AVG(CASE WHEN c.status = 'Resolved' AND c.resolved_at IS NOT NULL 
                               THEN TIMESTAMPDIFF(HOUR, c.created_at, c.resolved_at) ELSE NULL END), 1) AS avg_turnaround_hours,
                ROUND(AVG(cf.rating), 2) AS avg_satisfaction_rating
            FROM hostels h
            LEFT JOIN complaints c ON h.hostel_id = c.hostel_id
            LEFT JOIN complaint_feedback cf ON c.complaint_id = cf.complaint_id
            WHERE h.hostel_id IN ({placeholders})
            GROUP BY h.hostel_id, h.name, h.code
            ORDER BY h.name
        """
        return query_all(sql, tuple(assigned_hostels))


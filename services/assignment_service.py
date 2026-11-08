"""
Hostel Complaint Management System (HCMS)
Assignment Domain Service (services/assignment_service.py)

Manages work orders delegated to maintenance technicians, availability checks,
and atomic assignment transactions with optimistic locking.
"""

from db import query_one, query_all, execute_dml, get_db_cursor
from utils.decorators import log_audit_event

class AssignmentService:

    @staticmethod
    def get_staff_with_workload(specialization=None) -> list:
        """
        Retrieves all active maintenance technicians alongside their current open workload count
        (tasks currently in 'assigned', 'accepted', or 'in_progress').
        Helps wardens make balanced dispatch decisions.
        """
        params = []
        where_spec = ""
        if specialization and specialization != "all":
            where_spec = "AND st.specialization = %s"
            params.append(specialization)

        sql = f"""
            SELECT 
                st.staff_id,
                st.employee_code,
                st.specialization,
                st.is_available,
                CONCAT(u.first_name, ' ', u.last_name) AS staff_name,
                u.phone,
                u.email,
                COUNT(CASE WHEN ca.status IN ('assigned', 'accepted', 'in_progress') THEN 1 END) AS active_tasks_count,
                COUNT(CASE WHEN ca.status = 'completed' THEN 1 END) AS completed_tasks_count
            FROM staff st
            JOIN users u ON st.user_id = u.user_id
            LEFT JOIN complaint_assignments ca ON st.staff_id = ca.staff_id
            WHERE u.is_active = 1 {where_spec}
            GROUP BY st.staff_id, st.employee_code, st.specialization, st.is_available, staff_name, u.phone, u.email
            ORDER BY active_tasks_count ASC, st.specialization ASC
        """
        return query_all(sql, tuple(params))

    @staticmethod
    def assign_staff_to_complaint(complaint_id: int, staff_id: int, warden_id: int, 
                                  warden_user_id: int, work_notes: str = None) -> tuple:
        """
        Atomically assigns a staff technician to a complaint:
        - Verifies that complaint exists and checks current version_id
        - Calls stored procedure sp_assign_staff_to_complaint OR atomic transaction
        - Increments version_id
        - Logs audit trail
        """
        with get_db_cursor(commit=True) as (conn, cursor):
            # 1. Fetch current complaint version and details
            cursor.execute(
                "SELECT ticket_number, status, version_id, student_id FROM complaints WHERE complaint_id = %s FOR UPDATE",
                (complaint_id,)
            )
            complaint = cursor.fetchone()
            if not complaint:
                return False, "Complaint record not found."

            expected_version = complaint["version_id"]
            ticket_number = complaint["ticket_number"]

            # 2. Invoke stored procedure sp_assign_staff_to_complaint
            try:
                cursor.callproc(
                    "sp_assign_staff_to_complaint", 
                    [complaint_id, staff_id, warden_id, expected_version, work_notes or "", 0, ""]
                )
                cursor.execute("SELECT @_sp_assign_staff_to_complaint_5, @_sp_assign_staff_to_complaint_6")
                out_res = cursor.fetchone()
                success = out_res["@_sp_assign_staff_to_complaint_5"] if out_res else 0
                message = out_res["@_sp_assign_staff_to_complaint_6"] if out_res else "Assignment completed."
            except Exception as e:
                # Fallback to direct atomic transaction if stored procedure execution encounters environment differences
                cursor.execute(
                    "INSERT INTO complaint_assignments (complaint_id, staff_id, assigned_by_warden_id, status, work_notes) VALUES (%s, %s, %s, 'assigned', %s)",
                    (complaint_id, staff_id, warden_id, work_notes)
                )
                cursor.execute(
                    "UPDATE complaints SET status = 'Assigned', version_id = version_id + 1, updated_at = NOW() WHERE complaint_id = %s AND version_id = %s",
                    (complaint_id, expected_version)
                )
                if cursor.rowcount == 0:
                    return False, "Concurrency Conflict: Complaint was updated by another user."
                success = 1
                message = "Staff successfully assigned to complaint."

        if success:
            log_audit_event("COMPLAINT_ASSIGN", "complaints", complaint_id, {
                "staff_id": staff_id, "warden_id": warden_id, "ticket": ticket_number
            })
        return bool(success), message

    # ------------------------------------------------------------------------
    # Staff Technician Execution Methods
    # ------------------------------------------------------------------------
    @staticmethod
    def get_staff_metrics(staff_id: int) -> dict:
        """Retrieves aggregated KPI metrics for a specific maintenance technician."""
        sql = """
            SELECT 
                COUNT(*) AS total_assigned,
                SUM(CASE WHEN ca.status IN ('assigned', 'accepted') THEN 1 ELSE 0 END) AS pending_start,
                SUM(CASE WHEN ca.status = 'in_progress' THEN 1 ELSE 0 END) AS in_progress,
                SUM(CASE WHEN ca.status = 'completed' THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN c.is_overdue = 1 AND ca.status != 'completed' THEN 1 ELSE 0 END) AS overdue
            FROM complaint_assignments ca
            JOIN complaints c ON ca.complaint_id = c.complaint_id
            WHERE ca.staff_id = %s
        """
        metrics = query_one(sql, (staff_id,))
        return metrics or {"total_assigned": 0, "pending_start": 0, "in_progress": 0, "completed": 0, "overdue": 0}

    @staticmethod
    def get_staff_tasks(staff_id: int, status_filter: str = None) -> list:
        """
        Retrieves active or filtered work orders delegated strictly to the technician.
        Sorted with Critical priority and SLA-breached tasks at the top.
        """
        where_status = "AND ca.status IN ('assigned', 'accepted', 'in_progress')"
        params = [staff_id]

        if status_filter == "completed":
            where_status = "AND ca.status = 'completed'"
        elif status_filter == "all":
            where_status = ""
        elif status_filter in ("assigned", "accepted", "in_progress"):
            where_status = "AND ca.status = %s"
            params.append(status_filter)

        sql = f"""
            SELECT 
                ca.assignment_id, ca.status AS task_status, ca.assigned_at, ca.accepted_at, ca.work_notes,
                c.complaint_id, c.ticket_number, c.title, c.description, c.priority, c.status AS complaint_status,
                c.sla_deadline, c.is_overdue,
                cat.name AS category_name,
                h.name AS hostel_name, h.code AS hostel_code,
                r.room_number, r.floor_number,
                CONCAT(u_warden.first_name, ' ', u_warden.last_name) AS assigned_by_warden_name
            FROM complaint_assignments ca
            JOIN complaints c ON ca.complaint_id = c.complaint_id
            JOIN complaint_categories cat ON c.category_id = cat.category_id
            JOIN hostels h ON c.hostel_id = h.hostel_id
            LEFT JOIN rooms r ON c.room_id = r.room_id
            JOIN wardens w ON ca.assigned_by_warden_id = w.warden_id
            JOIN users u_warden ON w.user_id = u_warden.user_id
            WHERE ca.staff_id = %s {where_status}
            ORDER BY 
                CASE WHEN c.priority = 'Critical' THEN 1
                     WHEN c.is_overdue = 1 THEN 2
                     ELSE 3 END ASC,
                c.sla_deadline ASC
        """
        return query_all(sql, tuple(params))

    @staticmethod
    def get_staff_task_detail(assignment_id: int, staff_id: int) -> dict:
        """
        Retrieves full entity details for a specific work order.
        Strictly enforces that the assignment belongs to this staff technician.
        """
        sql = """
            SELECT 
                ca.assignment_id, ca.status AS task_status, ca.assigned_at, ca.accepted_at, ca.completed_at, ca.work_notes,
                c.complaint_id, c.ticket_number, c.title, c.description, c.priority, c.status AS complaint_status,
                c.sla_deadline, c.is_overdue, c.version_id, c.student_id,
                cat.name AS category_name, cat.default_sla_hours,
                h.name AS hostel_name, h.code AS hostel_code,
                r.room_number, r.floor_number,
                CONCAT(u_warden.first_name, ' ', u_warden.last_name) AS assigned_by_warden_name,
                CONCAT(u_stud.first_name, ' ', u_stud.last_name) AS student_name,
                u_stud.phone AS student_phone
            FROM complaint_assignments ca
            JOIN complaints c ON ca.complaint_id = c.complaint_id
            JOIN complaint_categories cat ON c.category_id = cat.category_id
            JOIN hostels h ON c.hostel_id = h.hostel_id
            LEFT JOIN rooms r ON c.room_id = r.room_id
            JOIN wardens w ON ca.assigned_by_warden_id = w.warden_id
            JOIN users u_warden ON w.user_id = u_warden.user_id
            JOIN students s ON c.student_id = s.student_id
            JOIN users u_stud ON s.user_id = u_stud.user_id
            WHERE ca.assignment_id = %s AND ca.staff_id = %s
        """
        task = query_one(sql, (assignment_id, staff_id))
        if not task:
            return None

        # Fetch attachments (both submission evidence and completion proof)
        sql_attach = """
            SELECT ca.*, CONCAT(u.first_name, ' ', u.last_name) AS uploader_name
            FROM complaint_attachments ca
            JOIN users u ON ca.uploaded_by_user_id = u.user_id
            WHERE ca.complaint_id = %s
            ORDER BY ca.created_at ASC
        """
        task["attachments"] = query_all(sql_attach, (task["complaint_id"],))

        # Fetch dialogue thread
        sql_resp = """
            SELECT cr.*, CONCAT(u.first_name, ' ', u.last_name) AS author_name, u.role AS author_role
            FROM complaint_responses cr
            JOIN users u ON cr.user_id = u.user_id
            WHERE cr.complaint_id = %s
            ORDER BY cr.created_at ASC
        """
        task["responses"] = query_all(sql_resp, (task["complaint_id"],))

        return task

    @staticmethod
    def accept_task(assignment_id: int, staff_id: int, user_id: int) -> tuple:
        """Staff technician confirms task commencement, transitioning status to 'In Progress'."""
        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute(
                "SELECT ca.status, ca.complaint_id, c.ticket_number, c.student_id, c.status AS complaint_status FROM complaint_assignments ca JOIN complaints c ON ca.complaint_id = c.complaint_id WHERE ca.assignment_id = %s AND ca.staff_id = %s FOR UPDATE",
                (assignment_id, staff_id)
            )
            row = cursor.fetchone()
            if not row:
                return False, "Task assignment not found or access denied."

            complaint_id = row["complaint_id"]
            ticket_number = row["ticket_number"]

            # Update assignment to accepted / in_progress
            cursor.execute(
                "UPDATE complaint_assignments SET status = 'in_progress', accepted_at = NOW() WHERE assignment_id = %s",
                (assignment_id,)
            )

            # Update complaint status to In Progress
            cursor.execute(
                "UPDATE complaints SET status = 'In Progress', version_id = version_id + 1, updated_at = NOW() WHERE complaint_id = %s",
                (complaint_id,)
            )

            # Record history
            cursor.execute(
                "INSERT INTO complaint_history (complaint_id, old_status, new_status, changed_by_user_id, remarks) VALUES (%s, %s, 'In Progress', %s, 'Technician accepted work order and commenced inspection')",
                (complaint_id, row["complaint_status"], user_id)
            )

            # Notify student
            cursor.execute("SELECT user_id FROM students WHERE student_id = %s", (row["student_id"],))
            st_user = cursor.fetchone()
            if st_user:
                cursor.execute(
                    "INSERT INTO notifications (user_id, complaint_id, title, message) VALUES (%s, %s, %s, %s)",
                    (st_user["user_id"], complaint_id, "Technician Commenced Work", 
                     f"A maintenance technician has accepted your complaint ({ticket_number}) and started work.")
                )

        log_audit_event("TASK_ACCEPT", "complaint_assignments", assignment_id, {"ticket": ticket_number})
        return True, "Task accepted! Work is now officially marked In Progress."

    @staticmethod
    def add_task_notes(assignment_id: int, staff_id: int, user_id: int, notes: str) -> tuple:
        """Appends progress remarks to the work order and official dialogue."""
        if not notes or len(notes.strip()) < 3:
            return False, "Work notes cannot be empty."

        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute(
                "SELECT complaint_id, work_notes FROM complaint_assignments WHERE assignment_id = %s AND staff_id = %s FOR UPDATE",
                (assignment_id, staff_id)
            )
            row = cursor.fetchone()
            if not row:
                return False, "Task assignment not found."

            complaint_id = row["complaint_id"]
            existing_notes = row["work_notes"] or ""
            updated_notes = f"{existing_notes}\n[{notes.strip()}]" if existing_notes else notes.strip()

            cursor.execute(
                "UPDATE complaint_assignments SET work_notes = %s WHERE assignment_id = %s",
                (updated_notes, assignment_id)
            )

            # Add to complaint responses dialogue
            cursor.execute(
                "INSERT INTO complaint_responses (complaint_id, user_id, message, is_internal) VALUES (%s, %s, %s, 0)",
                (complaint_id, user_id, f"[TECHNICIAN UPDATE]: {notes.strip()}")
            )

        log_audit_event("TASK_NOTES_UPDATE", "complaint_assignments", assignment_id)
        return True, "Work notes successfully appended to task log."

    @staticmethod
    def complete_task(assignment_id: int, staff_id: int, user_id: int, 
                      work_notes: str, completion_photo = None) -> tuple:
        """
        Marks technician work completed and uploads evidentiary photo proof.
        Transitions complaint status to 'Awaiting Verification' for warden review.
        """
        from utils.security import save_uploaded_file

        with get_db_cursor(commit=True) as (conn, cursor):
            cursor.execute(
                "SELECT ca.complaint_id, c.ticket_number, c.hostel_id, c.status AS complaint_status FROM complaint_assignments ca JOIN complaints c ON ca.complaint_id = c.complaint_id WHERE ca.assignment_id = %s AND ca.staff_id = %s FOR UPDATE",
                (assignment_id, staff_id)
            )
            row = cursor.fetchone()
            if not row:
                return False, "Task assignment not found or access denied."

            complaint_id = row["complaint_id"]
            ticket_number = row["ticket_number"]
            hostel_id = row["hostel_id"]

            # 1. Update assignment to completed
            cursor.execute(
                "UPDATE complaint_assignments SET status = 'completed', completed_at = NOW(), work_notes = CONCAT(IFNULL(work_notes, ''), '\n[COMPLETION SUMMARY]: ', %s) WHERE assignment_id = %s",
                (work_notes.strip() if work_notes else "Work finished", assignment_id)
            )

            # 2. Update complaint status to Awaiting Verification
            cursor.execute(
                "UPDATE complaints SET status = 'Awaiting Verification', version_id = version_id + 1, updated_at = NOW() WHERE complaint_id = %s",
                (complaint_id,)
            )

            # 3. Handle Completion Photo Evidence Upload
            if completion_photo and completion_photo.filename:
                rel_path, orig_name, size_kb, mime_type = save_uploaded_file(completion_photo, "completion")
                if rel_path:
                    cursor.execute(
                        "INSERT INTO complaint_attachments (complaint_id, uploaded_by_user_id, file_type, file_path, original_filename, file_size_kb, mime_type) VALUES (%s, %s, 'completion_proof', %s, %s, %s, %s)",
                        (complaint_id, user_id, rel_path, orig_name, size_kb, mime_type)
                    )

            # 4. Record history
            cursor.execute(
                "INSERT INTO complaint_history (complaint_id, old_status, new_status, changed_by_user_id, remarks) VALUES (%s, %s, 'Awaiting Verification', %s, %s)",
                (complaint_id, row["complaint_status"], user_id, f"Technician completed repairs: {work_notes[:60] if work_notes else 'Done'}")
            )

            # 5. Notify assigned wardens to inspect and close ticket
            cursor.execute(
                "SELECT w.user_id FROM hostel_wardens hw JOIN wardens w ON hw.warden_id = w.warden_id WHERE hw.hostel_id = %s",
                (hostel_id,)
            )
            wardens = cursor.fetchall()
            for w in wardens:
                cursor.execute(
                    "INSERT INTO notifications (user_id, complaint_id, title, message) VALUES (%s, %s, %s, %s)",
                    (w["user_id"], complaint_id, "Work Ready for Verification", 
                     f"Technician completed repairs on ticket {ticket_number}. Please inspect and verify.")
                )

        log_audit_event("TASK_COMPLETE", "complaint_assignments", assignment_id, {"ticket": ticket_number})
        return True, "Repairs completed! Work order submitted to warden for resolution verification."

    @staticmethod
    def get_staff_history(staff_id: int) -> list:
        """Retrieves history of all completed tasks alongside student feedback ratings."""
        sql = """
            SELECT 
                ca.assignment_id, ca.assigned_at, ca.completed_at, ca.work_notes,
                TIMESTAMPDIFF(HOUR, ca.assigned_at, ca.completed_at) AS turnaround_hours,
                c.complaint_id, c.ticket_number, c.title, c.priority,
                cat.name AS category_name,
                h.code AS hostel_code,
                r.room_number,
                cf.rating AS student_rating,
                cf.comments AS student_feedback
            FROM complaint_assignments ca
            JOIN complaints c ON ca.complaint_id = c.complaint_id
            JOIN complaint_categories cat ON c.category_id = cat.category_id
            JOIN hostels h ON c.hostel_id = h.hostel_id
            LEFT JOIN rooms r ON c.room_id = r.room_id
            LEFT JOIN complaint_feedback cf ON c.complaint_id = cf.complaint_id
            WHERE ca.staff_id = %s AND ca.status = 'completed'
            ORDER BY ca.completed_at DESC
        """
        return query_all(sql, (staff_id,))


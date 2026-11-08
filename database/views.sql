-- ============================================================================
-- HOSTEL COMPLAINT MANAGEMENT SYSTEM (HCMS)
-- Database Views Definition (views.sql)
-- Optimizes reporting, simplifies multi-table joins, and speeds up dashboards
-- ============================================================================

USE `hostel_complaint_db`;

DROP VIEW IF EXISTS `vw_complaint_full_details`;
DROP VIEW IF EXISTS `vw_warden_dashboard_summary`;
DROP VIEW IF EXISTS `vw_staff_task_queue`;
DROP VIEW IF EXISTS `vw_hostel_resolution_analytics`;
DROP VIEW IF EXISTS `vw_category_complaint_stats`;

-- ----------------------------------------------------------------------------
-- View 1: vw_complaint_full_details
-- Denormalized view joining student, hostel, room, category, and assigned staff
-- ----------------------------------------------------------------------------
CREATE VIEW `vw_complaint_full_details` AS
SELECT 
    c.complaint_id,
    c.ticket_number,
    c.title,
    c.description,
    c.priority,
    c.visibility,
    c.status,
    c.reopen_count,
    c.is_overdue,
    c.sla_deadline,
    c.version_id,
    c.created_at,
    c.updated_at,
    c.resolved_at,
    TIMESTAMPDIFF(HOUR, c.created_at, IFNULL(c.resolved_at, NOW())) AS duration_hours,
    -- Category info
    cat.category_id,
    cat.name AS category_name,
    cat.default_sla_hours,
    -- Student info
    s.student_id,
    s.enrollment_number,
    u_stud.user_id AS student_user_id,
    CONCAT(u_stud.first_name, ' ', u_stud.last_name) AS student_name,
    u_stud.email AS student_email,
    u_stud.phone AS student_phone,
    -- Hostel & Room info
    h.hostel_id,
    h.name AS hostel_name,
    h.code AS hostel_code,
    r.room_id,
    r.room_number,
    r.floor_number,
    -- Assigned staff info
    ca.assignment_id,
    ca.staff_id,
    ca.status AS assignment_status,
    CONCAT(u_staff.first_name, ' ', u_staff.last_name) AS staff_name,
    st.specialization AS staff_specialization,
    -- Feedback info
    cf.rating AS feedback_rating,
    cf.comments AS feedback_comments
FROM complaints c
JOIN complaint_categories cat ON c.category_id = cat.category_id
JOIN students s ON c.student_id = s.student_id
JOIN users u_stud ON s.user_id = u_stud.user_id
JOIN hostels h ON c.hostel_id = h.hostel_id
LEFT JOIN rooms r ON c.room_id = r.room_id
LEFT JOIN complaint_assignments ca ON c.complaint_id = ca.complaint_id 
    AND ca.status IN ('assigned', 'accepted', 'in_progress')
LEFT JOIN staff st ON ca.staff_id = st.staff_id
LEFT JOIN users u_staff ON st.user_id = u_staff.user_id
LEFT JOIN complaint_feedback cf ON c.complaint_id = cf.complaint_id;

-- ----------------------------------------------------------------------------
-- View 2: vw_warden_dashboard_summary
-- Aggregated metrics per hostel block for wardens
-- ----------------------------------------------------------------------------
CREATE VIEW `vw_warden_dashboard_summary` AS
SELECT 
    h.hostel_id,
    h.name AS hostel_name,
    h.code AS hostel_code,
    COUNT(c.complaint_id) AS total_complaints,
    SUM(CASE WHEN c.status = 'Submitted' THEN 1 ELSE 0 END) AS submitted_count,
    SUM(CASE WHEN c.status = 'Under Review' THEN 1 ELSE 0 END) AS under_review_count,
    SUM(CASE WHEN c.status = 'Assigned' THEN 1 ELSE 0 END) AS assigned_count,
    SUM(CASE WHEN c.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_count,
    SUM(CASE WHEN c.status = 'Awaiting Verification' THEN 1 ELSE 0 END) AS awaiting_verification_count,
    SUM(CASE WHEN c.status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_count,
    SUM(CASE WHEN c.status = 'Reopened' THEN 1 ELSE 0 END) AS reopened_count,
    SUM(CASE WHEN c.priority = 'Critical' AND c.status NOT IN ('Resolved', 'Rejected', 'Cancelled') THEN 1 ELSE 0 END) AS active_critical_count,
    SUM(CASE WHEN c.is_overdue = 1 AND c.status NOT IN ('Resolved', 'Rejected', 'Cancelled') THEN 1 ELSE 0 END) AS overdue_count
FROM hostels h
LEFT JOIN complaints c ON h.hostel_id = c.hostel_id
GROUP BY h.hostel_id, h.name, h.code;

-- ----------------------------------------------------------------------------
-- View 3: vw_staff_task_queue
-- Current active work order queue for maintenance staff
-- ----------------------------------------------------------------------------
CREATE VIEW `vw_staff_task_queue` AS
SELECT 
    ca.assignment_id,
    ca.staff_id,
    ca.status AS task_status,
    ca.assigned_at,
    ca.accepted_at,
    ca.work_notes,
    c.complaint_id,
    c.ticket_number,
    c.title,
    c.description,
    c.priority,
    c.status AS complaint_status,
    c.sla_deadline,
    c.is_overdue,
    cat.name AS category_name,
    h.name AS hostel_name,
    h.code AS hostel_code,
    r.room_number,
    CONCAT(u_warden.first_name, ' ', u_warden.last_name) AS assigned_by_warden_name
FROM complaint_assignments ca
JOIN complaints c ON ca.complaint_id = c.complaint_id
JOIN complaint_categories cat ON c.category_id = cat.category_id
JOIN hostels h ON c.hostel_id = h.hostel_id
LEFT JOIN rooms r ON c.room_id = r.room_id
JOIN wardens w ON ca.assigned_by_warden_id = w.warden_id
JOIN users u_warden ON w.user_id = u_warden.user_id
WHERE ca.status IN ('assigned', 'accepted', 'in_progress');

-- ----------------------------------------------------------------------------
-- View 4: vw_hostel_resolution_analytics
-- Resolution efficiency, SLA compliance percentage, and turnaround hours
-- ----------------------------------------------------------------------------
CREATE VIEW `vw_hostel_resolution_analytics` AS
SELECT 
    h.hostel_id,
    h.name AS hostel_name,
    COUNT(c.complaint_id) AS total_logged,
    SUM(CASE WHEN c.status = 'Resolved' THEN 1 ELSE 0 END) AS total_resolved,
    ROUND(
        (SUM(CASE WHEN c.status = 'Resolved' THEN 1 ELSE 0 END) / NULLIF(COUNT(c.complaint_id), 0)) * 100, 
        1
    ) AS resolution_percentage,
    ROUND(
        AVG(CASE WHEN c.status = 'Resolved' THEN TIMESTAMPDIFF(HOUR, c.created_at, c.resolved_at) ELSE NULL END), 
        1
    ) AS avg_resolution_hours,
    ROUND(
        AVG(cf.rating), 
        2
    ) AS avg_student_satisfaction
FROM hostels h
LEFT JOIN complaints c ON h.hostel_id = c.hostel_id
LEFT JOIN complaint_feedback cf ON c.complaint_id = cf.complaint_id
GROUP BY h.hostel_id, h.name;

-- ----------------------------------------------------------------------------
-- View 5: vw_category_complaint_stats
-- Distribution of issues across categories
-- ----------------------------------------------------------------------------
CREATE VIEW `vw_category_complaint_stats` AS
SELECT 
    cat.category_id,
    cat.name AS category_name,
    cat.default_sla_hours,
    COUNT(c.complaint_id) AS complaint_count,
    SUM(CASE WHEN c.status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_count,
    SUM(CASE WHEN c.status NOT IN ('Resolved', 'Rejected', 'Cancelled') THEN 1 ELSE 0 END) AS active_count,
    ROUND(
        AVG(CASE WHEN c.status = 'Resolved' THEN TIMESTAMPDIFF(HOUR, c.created_at, c.resolved_at) ELSE NULL END), 
        1
    ) AS avg_resolution_hours
FROM complaint_categories cat
LEFT JOIN complaints c ON cat.category_id = c.category_id
GROUP BY cat.category_id, cat.name, cat.default_sla_hours;

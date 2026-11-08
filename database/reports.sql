-- ============================================================================
-- HOSTEL COMPLAINT MANAGEMENT SYSTEM (HCMS)
-- Advanced Analytical SQL Showcase (reports.sql)
-- Demonstrates CTEs, Window Functions, Correlated Subqueries, EXISTS, and Self Joins
-- ============================================================================

USE `hostel_complaint_db`;

-- ----------------------------------------------------------------------------
-- Report 1: CTE & Window Function - Staff Efficiency & Performance Ranking
-- Ranks technicians using DENSE_RANK() based on average resolution turnaround
-- ----------------------------------------------------------------------------
WITH StaffMetrics AS (
    SELECT 
        st.staff_id,
        CONCAT(u.first_name, ' ', u.last_name) AS technician_name,
        st.specialization,
        COUNT(ca.assignment_id) AS total_tasks_assigned,
        SUM(CASE WHEN ca.status = 'completed' THEN 1 ELSE 0 END) AS tasks_completed,
        ROUND(AVG(TIMESTAMPDIFF(HOUR, ca.assigned_at, ca.completed_at)), 2) AS avg_turnaround_hours,
        ROUND(AVG(cf.rating), 2) AS avg_student_rating
    FROM staff st
    JOIN users u ON st.user_id = u.user_id
    LEFT JOIN complaint_assignments ca ON st.staff_id = ca.staff_id
    LEFT JOIN complaints c ON ca.complaint_id = c.complaint_id
    LEFT JOIN complaint_feedback cf ON c.complaint_id = cf.complaint_id
    GROUP BY st.staff_id, technician_name, st.specialization
)
SELECT 
    staff_id,
    technician_name,
    specialization,
    total_tasks_assigned,
    tasks_completed,
    avg_turnaround_hours,
    avg_student_rating,
    DENSE_RANK() OVER (
        ORDER BY tasks_completed DESC, avg_turnaround_hours ASC
    ) AS efficiency_rank
FROM StaffMetrics;

-- ----------------------------------------------------------------------------
-- Report 2: Window Function - Top 3 Most Recent Complaints Per Hostel Block
-- Uses ROW_NUMBER() PARTITION BY to extract top-N per group without subquery scans
-- ----------------------------------------------------------------------------
WITH RankedComplaints AS (
    SELECT 
        c.complaint_id,
        c.ticket_number,
        h.name AS hostel_name,
        cat.name AS category,
        c.title,
        c.priority,
        c.status,
        c.created_at,
        ROW_NUMBER() OVER (
            PARTITION BY c.hostel_id 
            ORDER BY c.created_at DESC
        ) AS recency_rank
    FROM complaints c
    JOIN hostels h ON c.hostel_id = h.hostel_id
    JOIN complaint_categories cat ON c.category_id = cat.category_id
)
SELECT * 
FROM RankedComplaints
WHERE recency_rank <= 3;

-- ----------------------------------------------------------------------------
-- Report 3: NOT EXISTS - Identify Idle Maintenance Staff Available for Dispatch
-- Finds technicians with zero active ('assigned', 'in_progress') assignments
-- ----------------------------------------------------------------------------
SELECT 
    st.staff_id,
    st.employee_code,
    st.specialization,
    CONCAT(u.first_name, ' ', u.last_name) AS staff_name,
    u.phone
FROM staff st
JOIN users u ON st.user_id = u.user_id
WHERE st.is_available = 1
  AND NOT EXISTS (
      SELECT 1 
      FROM complaint_assignments ca 
      WHERE ca.staff_id = st.staff_id 
        AND ca.status IN ('assigned', 'accepted', 'in_progress')
  );

-- ----------------------------------------------------------------------------
-- Report 4: Correlated Subquery - Students Submitting Above-Average Complaints
-- Identifies students filing significantly more tickets than their hostel peers
-- ----------------------------------------------------------------------------
SELECT 
    s.student_id,
    s.enrollment_number,
    CONCAT(u.first_name, ' ', u.last_name) AS student_name,
    h.name AS hostel_name,
    COUNT(c.complaint_id) AS student_complaint_count
FROM students s
JOIN users u ON s.user_id = u.user_id
JOIN hostels h ON s.hostel_id = h.hostel_id
JOIN complaints c ON s.student_id = c.student_id
GROUP BY s.student_id, s.enrollment_number, student_name, h.name, s.hostel_id
HAVING student_complaint_count > (
    -- Subquery calculating hostel-wide average complaints per student
    SELECT AVG(complaint_tally)
    FROM (
        SELECT COUNT(c_inner.complaint_id) AS complaint_tally
        FROM students s_inner
        LEFT JOIN complaints c_inner ON s_inner.student_id = c_inner.student_id
        WHERE s_inner.hostel_id = s.hostel_id
        GROUP BY s_inner.student_id
    ) AS hostel_averages
);

-- ----------------------------------------------------------------------------
-- Report 5: Self-Join - Detecting Recurring Issues in the Same Room within 7 Days
-- Identifies persistent hardware defects where a new complaint was lodged
-- shortly after another in the exact same room
-- ----------------------------------------------------------------------------
USE hostel_complaint_db;


-- 1. FIND REPEATED COMPLAINTS WITHIN 7 DAYS

SELECT
    c1.room_id,
    c1.ticket_number AS first_complaint,
    c2.ticket_number AS repeated_complaint,
    c1.created_at AS first_date,
    c2.created_at AS repeated_date
FROM complaints c1
JOIN complaints c2
    ON c1.room_id = c2.room_id
    AND c1.category_id = c2.category_id
    AND c1.complaint_id < c2.complaint_id
    AND c2.created_at BETWEEN c1.created_at
    AND DATE_ADD(c1.created_at, INTERVAL 7 DAY)
ORDER BY c1.room_id;


-- 2. ADD SLA DEADLINE COLUMN

ALTER TABLE complaints
ADD COLUMN sla_deadline DATETIME;


-- 3. CHECK COMPLAINT SLA STATUS

SELECT
    ticket_number,
    title,
    priority,
    status,
    sla_deadline,
    CASE
        WHEN sla_deadline IS NULL THEN 'Not Set'
        WHEN NOW() > sla_deadline THEN 'Overdue'
        WHEN TIMESTAMPDIFF(HOUR, NOW(), sla_deadline) <= 6
            THEN 'Urgent'
        WHEN TIMESTAMPDIFF(HOUR, NOW(), sla_deadline) <= 24
            THEN 'Deadline Near'
        ELSE 'On Time'
    END AS sla_status
FROM complaints
WHERE status NOT IN ('Resolved', 'Rejected', 'Cancelled')
ORDER BY sla_deadline;
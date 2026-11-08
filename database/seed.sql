-- ============================================================================
-- HOSTEL COMPLAINT MANAGEMENT SYSTEM (HCMS)
-- Comprehensive Seed Data Script (seed.sql)
-- Pre-populates all 18 tables with realistic campus scenario data
-- Default Password for ALL demo accounts: password123
-- ============================================================================

USE `hostel_complaint_db`;

-- Disable FK checks for clean deterministic bulk insert
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE `audit_logs`;
TRUNCATE TABLE `complaint_feedback`;
TRUNCATE TABLE `notifications`;
TRUNCATE TABLE `complaint_attachments`;
TRUNCATE TABLE `complaint_priority_history`;
TRUNCATE TABLE `complaint_history`;
TRUNCATE TABLE `complaint_responses`;
TRUNCATE TABLE `complaint_assignments`;
TRUNCATE TABLE `complaint_affected_hostels`;
TRUNCATE TABLE `complaints`;
TRUNCATE TABLE `complaint_categories`;
TRUNCATE TABLE `hostel_wardens`;
TRUNCATE TABLE `staff`;
TRUNCATE TABLE `wardens`;
TRUNCATE TABLE `students`;
TRUNCATE TABLE `rooms`;
TRUNCATE TABLE `hostels`;
TRUNCATE TABLE `users`;
SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------------------------------------------------------
-- 1. Insert Users (Password: password123 -> Werkzeug scrypt hash)
-- ----------------------------------------------------------------------------
INSERT INTO `users` (`user_id`, `email`, `password_hash`, `role`, `first_name`, `last_name`, `phone`, `is_active`) VALUES
-- 1: Admin
(1, 'admin@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'admin', 'System', 'Administrator', '9876543210', 1),
-- 2-4: Wardens
(2, 'warden.sharma@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'warden', 'Rajesh', 'Sharma', '9876543211', 1),
(3, 'warden.patel@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'warden', 'Meena', 'Patel', '9876543212', 1),
(4, 'warden.singh@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'warden', 'Harpal', 'Singh', '9876543213', 1),
-- 5-8: Maintenance Staff
(5, 'staff.ramesh@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'staff', 'Ramesh', 'Kumar', '9876543220', 1),
(6, 'staff.suresh@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'staff', 'Suresh', 'Verma', '9876543221', 1),
(7, 'staff.anita@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'staff', 'Anita', 'Devi', '9876543222', 1),
(8, 'staff.vikram@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'staff', 'Vikram', 'Joshi', '9876543223', 1),
-- 9-14: Students
-- (9, 'student.rahul@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'student', 'Rahul', 'Verma', '9876543230', 1),
-- (10, 'student.amit@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'student', 'Amit', 'Sharma', '9876543231', 1),
-- (11, 'student.priya@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'student', 'Priya', 'Nair', '9876543232', 1),
-- (12, 'student.sneha@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'student', 'Sneha', 'Kulkarni', '9876543233', 1),
-- (13, 'student.rohit@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'student', 'Rohit', 'Gupta', '9876543234', 1),
-- (14, 'student.pooja@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'student', 'Pooja', 'Iyer', '9876543235', 1);

-- ----------------------------------------------------------------------------
-- 2. Insert Hostels
-- ----------------------------------------------------------------------------
INSERT INTO `hostels` (`hostel_id`, `name`, `code`, `type`, `total_floors`, `is_active`) VALUES
(1, 'Aryabhata Boys Hostel', 'BH-1', 'boys', 7, 1),
(2, 'Bhaskara Boys Hostel', 'BH-2', 'boys', 7, 1),
(3, 'Kadambini Girls Hostel', 'GH-1', 'girls', 7, 1),
(4, 'Sarojini Girls Hostel', 'GH-2', 'girls', 7, 1);

-- ----------------------------------------------------------------------------
-- 3. Insert Rooms
-- ----------------------------------------------------------------------------
-- INSERT INTO `rooms` (`room_id`, `hostel_id`, `room_number`, `floor_number`, `capacity`, `current_occupancy`) VALUES
-- -- BH-1
-- (1, 1, '101', 1, 2, 1),
-- (2, 1, '102', 1, 2, 1),
-- (3, 1, '201', 2, 2, 0),
-- (4, 1, '202', 2, 2, 0),
-- -- BH-2
-- (5, 2, '301', 3, 2, 1),
-- (6, 2, '302', 3, 2, 0),
-- -- GH-1
-- (7, 3, '201', 2, 2, 1),
-- (8, 3, '202', 2, 2, 1),
-- (9, 3, '301', 3, 2, 0),
-- -- GH-2
-- (10, 4, '101', 1, 2, 1),
-- (11, 4, '102', 1, 2, 0);

-- ----------------------------------------------------------------------------
-- 4. Insert Wardens
-- ----------------------------------------------------------------------------
INSERT INTO `wardens` (`warden_id`, `user_id`, `employee_code`, `office_location`) VALUES
(1, 2, 'WRD-2024-001', 'BH-1 Ground Floor Office Room 4'),
(2, 3, 'WRD-2024-002', 'GH-1 Main Office Gate A'),
(3, 4, 'WRD-2024-003', 'GH-2 Administration Block Room 2');

-- ----------------------------------------------------------------------------
-- 5. Insert Hostel Wardens (M:N Assignment)
-- ----------------------------------------------------------------------------
INSERT INTO `hostel_wardens` (`hostel_id`, `warden_id`, `assigned_date`) VALUES
(1, 1, '2024-01-15'),  -- Warden Sharma manages BH-1
(2, 1, '2024-06-01'),  -- Warden Sharma also manages BH-2
(3, 2, '2024-01-15'),  -- Warden Patel manages GH-1
(4, 3, '2024-02-01');  -- Warden Singh manages GH-2

-- ----------------------------------------------------------------------------
-- 6. Insert Staff
-- ----------------------------------------------------------------------------
INSERT INTO `staff` (`staff_id`, `user_id`, `employee_code`, `specialization`, `is_available`) VALUES
(1, 5, 'STF-PLUMB-01', 'plumbing', 1),
(2, 6, 'STF-ELEC-02', 'electrical', 1),
(3, 7, 'STF-CLEAN-03', 'cleanliness', 1),
(4, 8, 'STF-CARP-04', 'carpentry', 1);

-- ----------------------------------------------------------------------------
-- 7. Insert Students
-- ----------------------------------------------------------------------------
-- INSERT INTO `students` (`student_id`, `user_id`, `enrollment_number`, `hostel_id`, `room_id`, `branch`, `academic_year`) VALUES
-- (1, 9, '2023CSB101', 1, 1, 'Computer Science & Engineering', 3),
-- (2, 10, '2023ECB102', 1, 2, 'Electronics & Communication', 3),
-- (3, 11, '2024CSB201', 3, 7, 'Computer Science & Engineering', 2),
-- (4, 12, '2024MEB202', 3, 8, 'Mechanical Engineering', 2),
-- (5, 13, '2022EEB301', 2, 5, 'Electrical Engineering', 4),
-- (6, 14, '2025CEB101', 4, 10, 'Civil Engineering', 1);

-- ----------------------------------------------------------------------------
-- 8. Insert Complaint Categories
-- ----------------------------------------------------------------------------
INSERT INTO `complaint_categories` (`category_id`, `name`, `description`, `default_sla_hours`, `default_priority`) VALUES
(1, 'Plumbing', 'Water leaks, pipe bursts, tap issues, flush failures', 24, 'High'),
(2, 'Electricity', 'Power outage, switchboard spark, tube light, fan issues', 12, 'Critical'),
(3, 'Water Supply', 'No drinking water supply, overhead tank shortages', 8, 'Critical'),
(4, 'Cleanliness', 'Corridor sweep, washroom cleaning, waste bin disposal', 24, 'Medium'),
(5, 'Food Quality', 'Mess hygienic complaints, foreign objects, food temperature', 12, 'High'),
(6, 'Internet', 'LAN port broken, Wi-Fi router reboot, high latency', 48, 'Low'),
(7, 'Room Maintenance', 'Wall dampness, door locks, window mesh tearing', 72, 'Low'),
(8, 'Furniture', 'Cot repair, study chair broken, cupboard hinge defective', 72, 'Low'),
(9, 'Security', 'Unauthorized visitors, main gate CCTV, security guard alert', 6, 'Critical'),
(10, 'Pest Control', 'Termites, bedbugs, mosquito fogging requirements', 48, 'Medium'),
(11, 'Bathroom Maintenance', 'Geyser defect, shower head missing, mirror damaged', 36, 'Medium'),
(12, 'Other', 'General complaints not fitting existing classifications', 48, 'Medium');

-- ----------------------------------------------------------------------------
-- 9. Insert Realistic Complaints Spanning ALL Lifecycles
-- ----------------------------------------------------------------------------
-- INSERT INTO `complaints` (
--     `complaint_id`, `ticket_number`, `student_id`, `hostel_id`, `room_id`, `category_id`, 
--     `title`, `description`, `priority`, `visibility`, `status`, `reopen_count`, 
--     `is_overdue`, `sla_deadline`, `version_id`, `resolved_at`, `created_at`
-- ) VALUES
-- -- 1: Submitted
-- (1, 'CMP-2026-0001', 1, 1, 1, 1, 
--  'Washbasin tap continuously dripping water', 
--  'The bathroom washbasin cold water tap handle is loose and water drips incessantly wasting clean water.', 
--  'Low', 'private', 'Submitted', 0, 0, 
--  DATE_ADD(NOW(), INTERVAL 24 HOUR), 1, NULL, 
--  DATE_SUB(NOW(), INTERVAL 2 HOUR)),

-- -- 2: Under Review
-- (2, 'CMP-2026-0002', 2, 1, 2, 2, 
--  'Study table socket sparking upon laptop charger insertion', 
--  'When plugging in a standard three-pin adapter into socket 2, visible electrical spark occurs. Potential fire hazard.', 
--  'Critical', 'private', 'Under Review', 0, 0, 
--  DATE_ADD(NOW(), INTERVAL 10 HOUR), 1, NULL, 
--  DATE_SUB(NOW(), INTERVAL 3 HOUR)),

-- -- 3: Assigned
-- (3, 'CMP-2026-0003', 3, 3, 7, 4, 
--  'Floor corridor dustbin overflowing with food waste', 
--  '2nd floor east wing garbage bin has not been cleared for 2 days, producing unbearable foul odor and attracting flies.', 
--  'Medium', 'private', 'Assigned', 0, 0, 
--  DATE_ADD(NOW(), INTERVAL 18 HOUR), 2, NULL, 
--  DATE_SUB(NOW(), INTERVAL 6 HOUR)),

-- -- 4: In Progress
-- (4, 'CMP-2026-0004', 1, 1, 1, 2, 
--  'Ceiling fan making loud grinding noise and vibrating vigorously', 
--  'The ceiling fan regulator at speed 3 and above produces rhythmic grinding sound and shakes. Risk of bearing seizure.', 
--  'High', 'private', 'In Progress', 0, 0, 
--  DATE_ADD(NOW(), INTERVAL 8 HOUR), 3, NULL, 
--  DATE_SUB(NOW(), INTERVAL 8 HOUR)),

-- -- 5: Awaiting Verification
-- (5, 'CMP-2026-0005', 5, 2, 5, 8, 
--  'Wooden study chair rear leg joint cracked and unsteady', 
--  'The wooden joinery under the study chair seat gave way, chair tilts backwards dangerously.', 
--  'Medium', 'private', 'Awaiting Verification', 0, 0, 
--  DATE_ADD(NOW(), INTERVAL 24 HOUR), 3, NULL, 
--  DATE_SUB(NOW(), INTERVAL 18 HOUR)),

-- -- 6: Resolved
-- (6, 'CMP-2026-0006', 4, 3, 8, 6, 
--  'Wi-Fi Access Point on 2nd floor continuously dropping connection', 
--  'Hostel SSID drops every 5 minutes during peak evening hours between 8 PM and 11 PM.', 
--  'Medium', 'private', 'Resolved', 0, 0, 
--  DATE_SUB(NOW(), INTERVAL 10 HOUR), 4, DATE_SUB(NOW(), INTERVAL 4 HOUR), 
--  DATE_SUB(NOW(), INTERVAL 30 HOUR)),

-- -- 7: Reopened
-- (7, 'CMP-2026-0007', 3, 3, 7, 1, 
--  'Shower mixer valve stuck - Scalding hot water only', 
--  'Technician previously visited but only changed washer. The mixer cartridge is defective - only scalding water flows.', 
--  'High', 'private', 'Reopened', 1, 0, 
--  DATE_ADD(NOW(), INTERVAL 12 HOUR), 5, NULL, 
--  DATE_SUB(NOW(), INTERVAL 28 HOUR)),

-- -- 8: Rejected
-- (8, 'CMP-2026-0008', 1, 1, 1, 12, 
--  'Request personal air conditioner installation in room 101', 
--  'Weather is getting warm, requesting permission to bring personal 1.5 ton split AC and install in room.', 
--  'Low', 'private', 'Rejected', 0, 0, 
--  DATE_SUB(NOW(), INTERVAL 12 HOUR), 2, NULL, 
--  DATE_SUB(NOW(), INTERVAL 24 HOUR)),

-- -- 9: Cancelled
-- (9, 'CMP-2026-0009', 2, 1, 2, 8, 
--  'Cupboard key lost - Need spare lock drill', 
--  'Misplaced room cupboard key. Requesting carpenter to cut open padlock.', 
--  'Low', 'private', 'Cancelled', 0, 0, 
--  DATE_SUB(NOW(), INTERVAL 20 HOUR), 2, NULL, 
--  DATE_SUB(NOW(), INTERVAL 36 HOUR)),

-- -- 10: General Complaint (Multi-Hostel Impact)
-- (10, 'CMP-2026-0010', 1, 1, NULL, 3, 
--  'Central RO drinking water cooler on ground floor dispensing warm cloudy water', 
--  'The commercial water filter serving Aryabhata and Bhaskara hostel common foyer is dispensing brownish cloudy water.', 
--  'Critical', 'general', 'In Progress', 0, 0, 
--  DATE_ADD(NOW(), INTERVAL 4 HOUR), 2, NULL, 
--  DATE_SUB(NOW(), INTERVAL 5 HOUR)),

-- -- 11: Overdue Complaint (Breached SLA)
-- (11, 'CMP-2026-0011', 5, 2, 5, 11, 
--  'Geyser thermostat malfunctioning - water not heating up in winter', 
--  'Bathroom geyser power lamp glows but heating coil fails to raise water temperature.', 
--  'High', 'private', 'Assigned', 0, 1, 
--  DATE_SUB(NOW(), INTERVAL 12 HOUR), 2, NULL, 
--  DATE_SUB(NOW(), INTERVAL 48 HOUR));

-- -- ----------------------------------------------------------------------------
-- -- 10. Insert Affected Hostels for General Complaints
-- -- ----------------------------------------------------------------------------
-- INSERT INTO `complaint_affected_hostels` (`complaint_id`, `hostel_id`) VALUES
-- (10, 1), -- BH-1
-- (10, 2); -- BH-2

-- -- ----------------------------------------------------------------------------
-- -- 11. Insert Complaint Assignments
-- -- ----------------------------------------------------------------------------
-- INSERT INTO `complaint_assignments` (
--     `assignment_id`, `complaint_id`, `staff_id`, `assigned_by_warden_id`, 
--     `status`, `assigned_at`, `accepted_at`, `completed_at`, `work_notes`
-- ) VALUES
-- -- CMP-3 assigned to Anita (Cleanliness)
-- (1, 3, 3, 2, 'assigned', DATE_SUB(NOW(), INTERVAL 5 HOUR), NULL, NULL, 
--  'Dispatched housekeeping team with industrial bags and disinfectant spray.'),

-- -- CMP-4 assigned to Suresh (Electrical) - In Progress
-- (2, 4, 2, 1, 'in_progress', DATE_SUB(NOW(), INTERVAL 7 HOUR), DATE_SUB(NOW(), INTERVAL 6 HOUR), NULL, 
--  'Inspected bearing assembly. Procuring 6202 replacement bearing from campus central store.'),

-- -- CMP-5 assigned to Vikram (Carpentry) - Completed
-- (3, 5, 4, 1, 'completed', DATE_SUB(NOW(), INTERVAL 16 HOUR), DATE_SUB(NOW(), INTERVAL 14 HOUR), DATE_SUB(NOW(), INTERVAL 3 HOUR), 
--  'Replaced rear cross-dowel brace with hardwood timber and tightened stainless steel bolts.'),

-- -- CMP-6 assigned to Vikram (General) - Completed
-- (4, 6, 4, 2, 'completed', DATE_SUB(NOW(), INTERVAL 28 HOUR), DATE_SUB(NOW(), INTERVAL 26 HOUR), DATE_SUB(NOW(), INTERVAL 4 HOUR), 
--  'Re-crimped RJ45 patch connector and power-cycled Cisco PoE switch on rack 2B.'),

-- -- CMP-10 assigned to Ramesh (Plumbing) - In Progress
-- (5, 10, 1, 1, 'in_progress', DATE_SUB(NOW(), INTERVAL 4 HOUR), DATE_SUB(NOW(), INTERVAL 3 HOUR), NULL, 
--  'Backflushed sediment filter cartridge, replacement carbon block scheduled for 4 PM delivery.'),

-- -- CMP-11 assigned to Suresh (Electrical) - Overdue
-- (6, 11, 2, 1, 'assigned', DATE_SUB(NOW(), INTERVAL 46 HOUR), NULL, NULL, 
--  'Work order forwarded. Pending heating coil stock availability.');

-- -- ----------------------------------------------------------------------------
-- -- 12. Insert Responses & Management Dialogue
-- -- ----------------------------------------------------------------------------
-- INSERT INTO `complaint_responses` (`complaint_id`, `user_id`, `message`, `is_internal`, `created_at`) VALUES
-- (2, 2, 'Electrician has been alerted to inspect wiring before 2 PM today. Please refrain from using that socket.', 0, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
-- (5, 8, 'Work completed. Chair leg reinforced with solid teak strut. Tested with 90kg load test.', 0, DATE_SUB(NOW(), INTERVAL 3 HOUR)),
-- (6, 3, 'Network team confirmed faulty uplink switch port reconfigured. Service restored.', 0, DATE_SUB(NOW(), INTERVAL 4 HOUR)),
-- (7, 11, 'Water is dangerously hot and knob cannot be turned to cold. Please send senior plumber urgently.', 0, DATE_SUB(NOW(), INTERVAL 27 HOUR)),
-- (8, 2, 'Request rejected as per University Hostel Policy Rule 14.b: High-load personal appliances (ACs, induction stoves, room heaters) are strictly prohibited.', 0, DATE_SUB(NOW(), INTERVAL 12 HOUR)),
-- (9, 10, 'Found key in backpack pocket. Cancelling request.', 0, DATE_SUB(NOW(), INTERVAL 20 HOUR));

-- -- ----------------------------------------------------------------------------
-- -- 13. Insert Complaint Status History
-- -- ----------------------------------------------------------------------------
-- INSERT INTO `complaint_history` (`complaint_id`, `old_status`, `new_status`, `changed_by_user_id`, `remarks`, `created_at`) VALUES
-- (1, NULL, 'Submitted', 9, 'Initial complaint lodged by student', DATE_SUB(NOW(), INTERVAL 2 HOUR)),
-- (2, NULL, 'Submitted', 10, 'Initial complaint lodged by student', DATE_SUB(NOW(), INTERVAL 3 HOUR)),
-- (2, 'Submitted', 'Under Review', 2, 'Warden Sharma reviewed urgency', DATE_SUB(NOW(), INTERVAL 2 HOUR)),
-- (3, NULL, 'Submitted', 11, 'Initial complaint lodged by student', DATE_SUB(NOW(), INTERVAL 6 HOUR)),
-- (3, 'Submitted', 'Assigned', 3, 'Assigned to Anita Devi', DATE_SUB(NOW(), INTERVAL 5 HOUR)),
-- (4, NULL, 'Submitted', 9, 'Initial complaint lodged by student', DATE_SUB(NOW(), INTERVAL 8 HOUR)),
-- (4, 'Submitted', 'Assigned', 2, 'Assigned to electrician Suresh', DATE_SUB(NOW(), INTERVAL 7 HOUR)),
-- (4, 'Assigned', 'In Progress', 6, 'Technician Suresh commenced work', DATE_SUB(NOW(), INTERVAL 6 HOUR)),
-- (5, 'In Progress', 'Awaiting Verification', 8, 'Carpenter Vikram completed repairs', DATE_SUB(NOW(), INTERVAL 3 HOUR)),
-- (6, 'Awaiting Verification', 'Resolved', 3, 'Warden Patel verified Wi-Fi uptime', DATE_SUB(NOW(), INTERVAL 4 HOUR)),
-- (7, 'Resolved', 'Reopened', 11, 'Student reopened due to persistent mixer issue', DATE_SUB(NOW(), INTERVAL 27 HOUR)),
-- (8, 'Submitted', 'Rejected', 2, 'Violates campus appliance regulations', DATE_SUB(NOW(), INTERVAL 12 HOUR)),
-- (9, 'Submitted', 'Cancelled', 10, 'Student cancelled - found key', DATE_SUB(NOW(), INTERVAL 20 HOUR));

-- -- ----------------------------------------------------------------------------
-- -- 14. Insert Feedback on Resolved Complaints
-- -- ----------------------------------------------------------------------------
-- INSERT INTO `complaint_feedback` (`complaint_id`, `student_id`, `rating`, `comments`, `created_at`) VALUES
-- (6, 4, 5, 'Wi-Fi connection is rock solid now. Thank you for the quick resolution within 24 hours!', DATE_SUB(NOW(), INTERVAL 3 HOUR));

-- -- ----------------------------------------------------------------------------
-- -- 15. Insert Notifications
-- -- ----------------------------------------------------------------------------
-- INSERT INTO `notifications` (`user_id`, `complaint_id`, `title`, `message`, `is_read`, `created_at`) VALUES
-- (9, 4, 'Technician Started Work', 'Electrician Suresh Verma has begun work on ticket CMP-2026-0004.', 1, DATE_SUB(NOW(), INTERVAL 6 HOUR)),
-- (11, 3, 'Complaint Assigned', 'Your complaint (CMP-2026-0003) has been assigned to Anita Devi.', 0, DATE_SUB(NOW(), INTERVAL 5 HOUR)),
-- (12, 6, 'Complaint Resolved', 'Your Wi-Fi complaint (CMP-2026-0006) has been resolved. Please rate the service.', 1, DATE_SUB(NOW(), INTERVAL 4 HOUR)),
-- (13, 11, 'Escalation Notice', 'Ticket CMP-2026-0011 has exceeded SLA target and has been escalated to Chief Warden.', 0, DATE_SUB(NOW(), INTERVAL 12 HOUR)),
-- (6, 4, 'New Assignment', 'You were assigned complaint CMP-2026-0004 for fan grinding noise.', 1, DATE_SUB(NOW(), INTERVAL 7 HOUR));

-- ----------------------------------------------------------------------------
-- 16. Insert Security Audit Logs
-- ----------------------------------------------------------------------------
INSERT INTO `audit_logs` (`user_id`, `action`, `target_entity`, `target_id`, `ip_address`, `user_agent`, `details_json`) VALUES
(1, 'SYSTEM_INIT', 'database', NULL, '127.0.0.1', 'DatabaseSeeder/1.0', JSON_OBJECT('status', 'Initialized with demo campus data')),
(2, 'COMPLAINT_REJECT', 'complaints', 8, '192.168.1.15', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', JSON_OBJECT('reason', 'Policy violation: AC not allowed')),
(3, 'COMPLAINT_RESOLVE', 'complaints', 6, '192.168.1.20', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', JSON_OBJECT('ticket', 'CMP-2026-0006', 'verified_by', 'Meena Patel')),
(9, 'LOGIN_SUCCESS', 'users', 9, '10.0.4.52', 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5)', JSON_OBJECT('role', 'student', 'method', 'password_auth'));

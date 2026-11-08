-- ============================================================================
-- HOSTEL COMPLAINT MANAGEMENT SYSTEM (HCMS)
-- Comprehensive Seed Data Script (seed.sql)
-- Pre-populates all 18 tables with realistic campus scenario data
-- Default Password for ALL demo accounts: password123
-- ============================================================================


USE `hostel_complaint_db`;

INSERT INTO `hostels`
(`hostel_id`, `name`, `code`, `type`, `total_floors`, `is_active`)
VALUES
(1, 'Aryabhata Boys Hostel', 'BH-1', 'boys', 7, 1),
(2, 'Bhaskara Boys Hostel', 'BH-2', 'boys', 7, 1),
(3, 'Kadambini Girls Hostel', 'GH-1', 'girls', 7, 1),
(4, 'Sarojini Girls Hostel', 'GH-2', 'girls', 7, 1);

INSERT INTO `complaint_categories`
(`category_id`, `name`, `description`, `default_sla_hours`, `default_priority`)
VALUES
(1, 'Plumbing', 'Water leaks, pipe bursts, tap issues, flush failures', 24, 'High'),
(2, 'Electricity', 'Power outage, switchboard spark, light and fan issues', 12, 'Critical'),
(3, 'Water Supply', 'Drinking water supply and tank shortages', 8, 'Critical'),
(4, 'Cleanliness', 'Corridor and washroom cleaning', 24, 'Medium'),
(5, 'Food Quality', 'Mess hygiene and food quality complaints', 12, 'High'),
(6, 'Internet', 'Wi-Fi and LAN connection issues', 48, 'Low'),
(7, 'Room Maintenance', 'Wall, door and window repairs', 72, 'Low'),
(8, 'Furniture', 'Bed, chair and cupboard repairs', 72, 'Low'),
(9, 'Security', 'Unauthorized visitors and security concerns', 6, 'Critical'),
(10, 'Pest Control', 'Termites, bedbugs and mosquito issues', 48, 'Medium'),
(11, 'Bathroom Maintenance', 'Geyser, shower and mirror issues', 36, 'Medium'),
(12, 'Other', 'Other general complaints', 48, 'Medium');

INSERT IGNORE INTO `users`
(`user_id`, `email`, `password_hash`, `role`, `first_name`, `last_name`, `phone`, `is_active`)
VALUES
(1, 'admin@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'admin', 'System', 'Administrator', '9876543210', 1),
(2, 'warden.sharma@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'warden', 'Rajesh', 'Sharma', '9876543211', 1),
(3, 'warden.patel@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'warden', 'Meena', 'Patel', '9876543212', 1),
(4, 'warden.singh@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'warden', 'Harpal', 'Singh', '9876543213', 1),
(5, 'staff.ramesh@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'staff', 'Ramesh', 'Kumar', '9876543220', 1),
(6, 'staff.suresh@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'staff', 'Suresh', 'Verma', '9876543221', 1),
(7, 'staff.anita@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'staff', 'Anita', 'Devi', '9876543222', 1),
(8, 'staff.vikram@hostel.edu', 'scrypt:32768:8:1$tcnxbRbbeTL62Gwa$8161a050ccf5e12e9867a7e08624d142da9c955346c0aab73878cedfefa30c12bcd0c056fd59ba24dc9dc6670ae28cdbf8832330786a6cc976a1a70200f4332b', 'staff', 'Vikram', 'Joshi', '9876543223', 1);


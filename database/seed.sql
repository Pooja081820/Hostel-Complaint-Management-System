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

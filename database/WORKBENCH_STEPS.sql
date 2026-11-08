-- FULL ADVANCED DATABASE: use this with Option B
-- IMPORTANT: schema.sql drops/recreates the project's tables.
-- Back up existing data first. Prefer a fresh test database.
--
-- Recommended: from the project root, configure .env and run:
--     python init_db.py
--
-- Manual Workbench order:
-- 1. schema.sql
-- 2. triggers.sql
-- 3. procedures.sql
-- 4. views.sql
-- 5. seed.sql
--
-- Then check:
USE hostel_complaint_db;
SHOW TABLES;
SELECT COUNT(*) AS users_total FROM users;
SELECT COUNT(*) AS complaints_total FROM complaints;
SELECT status, COUNT(*) AS total
FROM complaints
GROUP BY status;
SELECT * FROM vw_complaint_full_details;

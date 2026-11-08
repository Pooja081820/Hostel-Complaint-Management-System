-- SIMPLE HOSTEL COMPLAINT DATABASE
-- For learning MySQL Workbench. This is NOT the full app schema.
-- Run this whole file in MySQL Workbench on a NEW learning database.

CREATE DATABASE IF NOT EXISTS hostel_complaint_simple;
USE hostel_complaint_simple;

-- 1. All people use one users table.
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'warden', 'staff', 'admin') NOT NULL,
    hostel_name VARCHAR(100),
    room_number VARCHAR(20)
);

-- 2. Complaint types, for example plumbing or electricity.
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE
);

-- 3. Every complaint belongs to one student and one category.
CREATE TABLE complaints (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    category_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    priority ENUM('Low', 'Medium', 'High') DEFAULT 'Medium',
    status ENUM('Submitted', 'In Progress', 'Resolved', 'Rejected')
        DEFAULT 'Submitted',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(user_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- 4. A warden can assign a complaint to a staff member.
CREATE TABLE assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    staff_id INT NOT NULL,
    assigned_by INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id),
    FOREIGN KEY (staff_id) REFERENCES users(user_id),
    FOREIGN KEY (assigned_by) REFERENCES users(user_id)
);

-- 5. Feedback given by a student after resolution.
CREATE TABLE feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL UNIQUE,
    student_id INT NOT NULL,
    rating INT NOT NULL,
    comment VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id),
    FOREIGN KEY (student_id) REFERENCES users(user_id)
);

-- DEMO DATA
-- The password_hash values below are placeholders for SQL learning only.
-- Real login passwords must be hashed by Python (never store plain passwords).

INSERT INTO users (name, email, password_hash, role, hostel_name, room_number)
VALUES
('Rahul Kumar', 'rahul@example.com', 'demo_hash', 'student', 'Boys Hostel A', '101'),
('Anita Sharma', 'warden@example.com', 'demo_hash', 'warden', 'Boys Hostel A', NULL),
('Ramesh Kumar', 'staff@example.com', 'demo_hash', 'staff', 'Boys Hostel A', NULL),
('System Admin', 'admin@example.com', 'demo_hash', 'admin', NULL, NULL);

INSERT INTO categories (category_name)
VALUES ('Water'), ('Electricity'), ('Cleaning'), ('Furniture');

-- Rahul is user_id 1; Water is category_id 1.
INSERT INTO complaints
(student_id, category_id, title, description, priority)
VALUES
(1, 1, 'Water leakage', 'Water is leaking in room 101.', 'High');

-- Assign complaint 1 to staff user 3 by warden user 2.
INSERT INTO assignments (complaint_id, staff_id, assigned_by)
VALUES (1, 3, 2);

-- USEFUL QUERIES TO PRACTICE
SELECT * FROM users;
SELECT * FROM categories;
SELECT * FROM complaints;
SELECT * FROM assignments;
SELECT * FROM feedback;

-- Show each complaint with student and category names.
SELECT
    c.complaint_id,
    u.name AS student_name,
    cat.category_name,
    c.title,
    c.priority,
    c.status,
    c.created_at
FROM complaints c
JOIN users u ON c.student_id = u.user_id
JOIN categories cat ON c.category_id = cat.category_id;

-- Change complaint status to In Progress.
UPDATE complaints
SET status = 'In Progress'
WHERE complaint_id = 1;

-- Add feedback after resolving the complaint.
-- First set it to Resolved, then add feedback.
UPDATE complaints
SET status = 'Resolved'
WHERE complaint_id = 1;

INSERT INTO feedback (complaint_id, student_id, rating, comment)
VALUES (1, 1, 5, 'The issue was fixed quickly.');

-- Count complaints by status.
SELECT status, COUNT(*) AS total
FROM complaints
GROUP BY status;

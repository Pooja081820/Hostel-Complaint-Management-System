-- ============================================================================
-- HOSTEL COMPLAINT MANAGEMENT SYSTEM (HCMS)
-- Database DDL Schema Definition (schema.sql)
-- Target RDBMS: MySQL 8.0+ | Engine: InnoDB | Character Set: utf8mb4
-- Normalized up to Boyce-Codd Normal Form (BCNF)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS `hostel_complaint_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `hostel_complaint_db`;

-- Drop existing tables in reverse dependency order to avoid foreign key errors


-- ----------------------------------------------------------------------------
-- Table 1: users (Master Authentication & User Profile Table)
-- ----------------------------------------------------------------------------
CREATE TABLE `users` (
    `user_id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
     password_hash VARCHAR(255) NOT NULL,
    `email` VARCHAR(100) NOT NULL,
    `role` ENUM('student', 'warden', 'staff', 'admin') NOT NULL,
    `first_name` VARCHAR(50) NOT NULL,
    `last_name` VARCHAR(50) NOT NULL,
    `phone` VARCHAR(15) NOT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `uq_users_email` UNIQUE (`email`),
    CONSTRAINT `chk_users_phone` CHECK (CHAR_LENGTH(`phone`) >= 10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 2: hostels (Campus Residential Hostel Blocks)
-- ----------------------------------------------------------------------------
CREATE TABLE `hostels` (
    `hostel_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(80) NOT NULL,
    `code` VARCHAR(15) NOT NULL,
    `type` ENUM('boys', 'girls') NOT NULL,
    `total_floors` TINYINT UNSIGNED NOT NULL DEFAULT 3,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `uq_hostels_name` UNIQUE (`name`),
    CONSTRAINT `uq_hostels_code` UNIQUE (`code`),
    CONSTRAINT `chk_hostels_floors` CHECK (`total_floors` > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 3: rooms (Rooms within Hostels)
-- ----------------------------------------------------------------------------
CREATE TABLE `rooms` (
    `room_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `hostel_id` INT UNSIGNED NOT NULL,
    `room_number` VARCHAR(10) NOT NULL,
    `floor_number` TINYINT NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_rooms_hostel` FOREIGN KEY (`hostel_id`)
        REFERENCES `hostels` (`hostel_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- ----------------------------------------------------------------------------
-- Table 4: students (Student Profile Extension of Users)
-- ----------------------------------------------------------------------------
CREATE TABLE `students` (
    `student_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `enrollment_number` VARCHAR(30) NOT NULL,
    `hostel_id` INT UNSIGNED NOT NULL,
    `room_id` INT UNSIGNED NOT NULL,
    `branch` VARCHAR(60) NOT NULL,
    `academic_year` TINYINT UNSIGNED NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_students_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_students_hostel` FOREIGN KEY (`hostel_id`) 
        REFERENCES `hostels` (`hostel_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_students_room` FOREIGN KEY (`room_id`) 
        REFERENCES `rooms` (`room_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `uq_students_user_id` UNIQUE (`user_id`),
    CONSTRAINT `uq_students_enrollment` UNIQUE (`enrollment_number`),
    CONSTRAINT `chk_students_year` CHECK (`academic_year` BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 5: wardens (Hostel Warden Profile Extension of Users)
-- ----------------------------------------------------------------------------
CREATE TABLE `wardens` (
    `warden_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `employee_code` VARCHAR(30) NOT NULL,
    `office_location` VARCHAR(100) DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_wardens_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `uq_wardens_user_id` UNIQUE (`user_id`),
    CONSTRAINT `uq_wardens_emp_code` UNIQUE (`employee_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 6: staff (Maintenance Staff Profile Extension of Users)
-- ----------------------------------------------------------------------------
CREATE TABLE `staff` (
    `staff_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `employee_code` VARCHAR(30) NOT NULL,
    `specialization` ENUM('plumbing', 'electrical', 'carpentry', 'cleanliness', 'network', 'general', 'pest_control') NOT NULL,
    `is_available` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_staff_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `uq_staff_user_id` UNIQUE (`user_id`),
    CONSTRAINT `uq_staff_emp_code` UNIQUE (`employee_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 7: hostel_wardens (M:N Mapping of Wardens to Assigned Hostels)
-- ----------------------------------------------------------------------------
CREATE TABLE `hostel_wardens` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `hostel_id` INT UNSIGNED NOT NULL,
    `warden_id` INT UNSIGNED NOT NULL,
    `assigned_date` DATE NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_hw_hostel` FOREIGN KEY (`hostel_id`) 
        REFERENCES `hostels` (`hostel_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_hw_warden` FOREIGN KEY (`warden_id`) 
        REFERENCES `wardens` (`warden_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `uq_hostel_warden_pair` UNIQUE (`hostel_id`, `warden_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 8: complaint_categories (Classifications & Service Level Agreements)
-- ----------------------------------------------------------------------------
CREATE TABLE `complaint_categories` (
    `category_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(50) NOT NULL,
    `description` VARCHAR(255) DEFAULT NULL,
    `default_sla_hours` SMALLINT UNSIGNED NOT NULL DEFAULT 48,
    `default_priority` ENUM('Low', 'Medium', 'High', 'Critical') NOT NULL DEFAULT 'Medium',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `uq_categories_name` UNIQUE (`name`),
    CONSTRAINT `chk_categories_sla` CHECK (`default_sla_hours` > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 9: complaints (Core Transactional Table with Optimistic Locking)
-- ----------------------------------------------------------------------------
CREATE TABLE `complaints` (
    `complaint_id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `ticket_number` VARCHAR(25) NOT NULL,
    `student_id` INT UNSIGNED NOT NULL,
    `hostel_id` INT UNSIGNED NOT NULL,
    `room_id` INT UNSIGNED DEFAULT NULL,
    `category_id` INT UNSIGNED NOT NULL,
    `title` VARCHAR(150) NOT NULL,
    `description` TEXT NOT NULL,
    `priority` ENUM('Low', 'Medium', 'High', 'Critical') NOT NULL DEFAULT 'Medium',
    `visibility` ENUM('private', 'general') NOT NULL DEFAULT 'private',
    `status` ENUM('Submitted', 'Under Review', 'Assigned', 'In Progress', 'Awaiting Verification', 'Resolved', 'Reopened', 'Rejected', 'Cancelled') NOT NULL DEFAULT 'Submitted',
    `reopen_count` TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `is_overdue` TINYINT(1) NOT NULL DEFAULT 0,
    `sla_deadline` DATETIME NOT NULL,
    `version_id` INT UNSIGNED NOT NULL DEFAULT 1,
    `resolved_at` DATETIME DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_complaints_student` FOREIGN KEY (`student_id`) 
        REFERENCES `students` (`student_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_complaints_hostel` FOREIGN KEY (`hostel_id`) 
        REFERENCES `hostels` (`hostel_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_complaints_room` FOREIGN KEY (`room_id`) 
        REFERENCES `rooms` (`room_id`) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT `fk_complaints_category` FOREIGN KEY (`category_id`) 
        REFERENCES `complaint_categories` (`category_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `uq_complaints_ticket` UNIQUE (`ticket_number`),
    CONSTRAINT `chk_complaints_reopen` CHECK (`reopen_count` <= 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Composite indexes for optimal query execution plans
CREATE INDEX `idx_complaints_hostel_status_priority` ON `complaints` (`hostel_id`, `status`, `priority`);
CREATE INDEX `idx_complaints_student_status` ON `complaints` (`student_id`, `status`);
CREATE INDEX `idx_complaints_sla_overdue` ON `complaints` (`is_overdue`, `status`, `sla_deadline`);
CREATE INDEX `idx_complaints_created_at` ON `complaints` (`created_at`);

-- ----------------------------------------------------------------------------
-- Table 10: complaint_affected_hostels (M:N for General Multi-Hostel Issues)
-- ----------------------------------------------------------------------------
CREATE TABLE `complaint_affected_hostels` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `complaint_id` BIGINT UNSIGNED NOT NULL,
    `hostel_id` INT UNSIGNED NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_cah_complaint` FOREIGN KEY (`complaint_id`) 
        REFERENCES `complaints` (`complaint_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_cah_hostel` FOREIGN KEY (`hostel_id`) 
        REFERENCES `hostels` (`hostel_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `uq_cah_pair` UNIQUE (`complaint_id`, `hostel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 11: complaint_assignments (Work Orders Delegated to Staff)
-- ----------------------------------------------------------------------------
CREATE TABLE `complaint_assignments` (
    `assignment_id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `complaint_id` BIGINT UNSIGNED NOT NULL,
    `staff_id` INT UNSIGNED NOT NULL,
    `assigned_by_warden_id` INT UNSIGNED NOT NULL,
    `status` ENUM('assigned', 'accepted', 'in_progress', 'completed', 'reassigned') NOT NULL DEFAULT 'assigned',
    `assigned_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `accepted_at` TIMESTAMP NULL DEFAULT NULL,
    `completed_at` TIMESTAMP NULL DEFAULT NULL,
    `work_notes` TEXT DEFAULT NULL,
    CONSTRAINT `fk_ca_complaint` FOREIGN KEY (`complaint_id`) 
        REFERENCES `complaints` (`complaint_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_ca_staff` FOREIGN KEY (`staff_id`) 
        REFERENCES `staff` (`staff_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_ca_warden` FOREIGN KEY (`assigned_by_warden_id`) 
        REFERENCES `wardens` (`warden_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX `idx_assignments_staff_status` ON `complaint_assignments` (`staff_id`, `status`);

-- ----------------------------------------------------------------------------
-- Table 12: complaint_responses (Official Dialogue & Management Notes)
-- ----------------------------------------------------------------------------
CREATE TABLE `complaint_responses` (
    `response_id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `complaint_id` BIGINT UNSIGNED NOT NULL,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `message` TEXT NOT NULL,
    `is_internal` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_cr_complaint` FOREIGN KEY (`complaint_id`) 
        REFERENCES `complaints` (`complaint_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_cr_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX `idx_responses_complaint_created` ON `complaint_responses` (`complaint_id`, `created_at`);

-- ----------------------------------------------------------------------------
-- Table 13: complaint_history (Immutable Status Audit Trail)
-- ----------------------------------------------------------------------------
CREATE TABLE `complaint_history` (
    `history_id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `complaint_id` BIGINT UNSIGNED NOT NULL,
    `old_status` VARCHAR(30) DEFAULT NULL,
    `new_status` VARCHAR(30) NOT NULL,
    `changed_by_user_id` BIGINT UNSIGNED NOT NULL,
    `remarks` VARCHAR(255) DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_ch_complaint` FOREIGN KEY (`complaint_id`) 
        REFERENCES `complaints` (`complaint_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_ch_user` FOREIGN KEY (`changed_by_user_id`) 
        REFERENCES `users` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX `idx_history_complaint_created` ON `complaint_history` (`complaint_id`, `created_at`);

-- ----------------------------------------------------------------------------
-- Table 14: complaint_priority_history (Warden Justification for Priority Edits)
-- ----------------------------------------------------------------------------
CREATE TABLE `complaint_priority_history` (
    `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `complaint_id` BIGINT UNSIGNED NOT NULL,
    `old_priority` VARCHAR(20) NOT NULL,
    `new_priority` VARCHAR(20) NOT NULL,
    `changed_by_user_id` BIGINT UNSIGNED NOT NULL,
    `reason` TEXT NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_cph_complaint` FOREIGN KEY (`complaint_id`) 
        REFERENCES `complaints` (`complaint_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_cph_user` FOREIGN KEY (`changed_by_user_id`) 
        REFERENCES `users` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 15: complaint_attachments (Student Evidence & Staff Completion Proof)
-- ----------------------------------------------------------------------------
CREATE TABLE `complaint_attachments` (
    `attachment_id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `complaint_id` BIGINT UNSIGNED NOT NULL,
    `uploaded_by_user_id` BIGINT UNSIGNED NOT NULL,
    `file_type` ENUM('submission_evidence', 'completion_proof') NOT NULL,
    `file_path` VARCHAR(255) NOT NULL,
    `original_filename` VARCHAR(255) NOT NULL,
    `file_size_kb` INT UNSIGNED NOT NULL,
    `mime_type` VARCHAR(50) NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_ca_attach_complaint` FOREIGN KEY (`complaint_id`) 
        REFERENCES `complaints` (`complaint_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_ca_attach_user` FOREIGN KEY (`uploaded_by_user_id`) 
        REFERENCES `users` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 16: notifications (User Alert Inbox)
-- ----------------------------------------------------------------------------
CREATE TABLE `notifications` (
    `notification_id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `complaint_id` BIGINT UNSIGNED DEFAULT NULL,
    `title` VARCHAR(100) NOT NULL,
    `message` TEXT NOT NULL,
    `is_read` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_notif_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_notif_complaint` FOREIGN KEY (`complaint_id`) 
        REFERENCES `complaints` (`complaint_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX `idx_notif_user_read_created` ON `notifications` (`user_id`, `is_read`, `created_at`);

-- ----------------------------------------------------------------------------
-- Table 17: complaint_feedback (Student Satisfaction Survey Post-Resolution)
-- ----------------------------------------------------------------------------
CREATE TABLE `complaint_feedback` (
    `feedback_id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `complaint_id` BIGINT UNSIGNED NOT NULL,
    `student_id` INT UNSIGNED NOT NULL,
    `rating` TINYINT UNSIGNED NOT NULL,
    `comments` TEXT DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_cf_complaint` FOREIGN KEY (`complaint_id`) 
        REFERENCES `complaints` (`complaint_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_cf_student` FOREIGN KEY (`student_id`) 
        REFERENCES `students` (`student_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `uq_cf_complaint` UNIQUE (`complaint_id`),
    CONSTRAINT `chk_cf_rating` CHECK (`rating` BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 18: audit_logs (System-Wide Security & Compliance Trail)
-- ----------------------------------------------------------------------------
CREATE TABLE `audit_logs` (
    `log_id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT UNSIGNED DEFAULT NULL,
    `action` VARCHAR(60) NOT NULL,
    `target_entity` VARCHAR(40) NOT NULL,
    `target_id` BIGINT UNSIGNED DEFAULT NULL,
    `ip_address` VARCHAR(45) NOT NULL,
    `user_agent` VARCHAR(255) DEFAULT NULL,
    `details_json` JSON DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_al_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users` (`user_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX `idx_audit_action_created` ON `audit_logs` (`action`, `created_at`);

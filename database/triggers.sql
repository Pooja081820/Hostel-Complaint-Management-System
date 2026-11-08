-- ============================================================================
-- HOSTEL COMPLAINT MANAGEMENT SYSTEM (HCMS)
-- Database Triggers Definition (triggers.sql)
-- Automates audit logging, data integrity, and business rule enforcement
-- ============================================================================

USE `hostel_complaint_db`;

DROP TRIGGER IF EXISTS `trg_complaint_status_audit`;
DROP TRIGGER IF EXISTS `trg_prevent_invalid_cancellation`;
DROP TRIGGER IF EXISTS `trg_student_occupancy_increment`;
DROP TRIGGER IF EXISTS `trg_student_occupancy_decrement`;

DELIMITER $$

-- ----------------------------------------------------------------------------
-- Trigger 1: trg_complaint_status_audit
-- Ensures every status progression is permanently logged in complaint_history
-- ----------------------------------------------------------------------------
CREATE TRIGGER `trg_complaint_status_audit`
AFTER UPDATE ON `complaints`
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        -- Fallback: Use the student user_id if session context is not available
        INSERT INTO `complaint_history` (
            `complaint_id`,
            `old_status`,
            `new_status`,
            `changed_by_user_id`,
            `remarks`,
            `created_at`
        ) VALUES (
            NEW.complaint_id,
            OLD.status,
            NEW.status,
            (SELECT `user_id` FROM `students` WHERE `student_id` = NEW.student_id LIMIT 1),
            CONCAT('Status automatically transitioned from ', OLD.status, ' to ', NEW.status),
            NOW()
        );
    END IF;
END$$

-- ----------------------------------------------------------------------------
-- Trigger 2: trg_prevent_invalid_cancellation
-- Enforces business rule: Students cannot cancel complaints once work is assigned or started
-- ----------------------------------------------------------------------------
CREATE TRIGGER `trg_prevent_invalid_cancellation`
BEFORE UPDATE ON `complaints`
FOR EACH ROW
BEGIN
    IF NEW.status = 'Cancelled' AND OLD.status IN ('Assigned', 'In Progress', 'Awaiting Verification', 'Resolved') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Business Rule Violation: Complaint cannot be cancelled once work has been assigned or started.';
    END IF;
END$$

-- ----------------------------------------------------------------------------
-- Trigger 3: trg_student_occupancy_increment
-- Automatically increments room occupancy when a student profile is created
-- ----------------------------------------------------------------------------
CREATE TRIGGER `trg_student_occupancy_increment`
AFTER INSERT ON `students`
FOR EACH ROW
BEGIN
    UPDATE `rooms`
    SET `current_occupancy` = `current_occupancy` + 1
    WHERE `room_id` = NEW.room_id;
END$$

-- ----------------------------------------------------------------------------
-- Trigger 4: trg_student_occupancy_decrement
-- Automatically decrements room occupancy when a student profile is removed
-- ----------------------------------------------------------------------------
CREATE TRIGGER `trg_student_occupancy_decrement`
AFTER DELETE ON `students`
FOR EACH ROW
BEGIN
    UPDATE `rooms`
    SET `current_occupancy` = GREATEST(0, CAST(`current_occupancy` AS SIGNED) - 1)
    WHERE `room_id` = OLD.room_id;
END$$

DELIMITER ;

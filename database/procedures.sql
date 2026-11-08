-- ============================================================================
-- HOSTEL COMPLAINT MANAGEMENT SYSTEM (HCMS)
-- Database Stored Procedures Definition (procedures.sql)
-- Encapsulates atomic multi-step business transactions with ACID guarantees
-- ============================================================================

USE `hostel_complaint_db`;

DROP PROCEDURE IF EXISTS `sp_assign_staff_to_complaint`;
DROP PROCEDURE IF EXISTS `sp_resolve_complaint`;
DROP PROCEDURE IF EXISTS `sp_reopen_complaint`;
DROP PROCEDURE IF EXISTS `sp_scan_and_escalate_overdue`;

DELIMITER $$

-- ----------------------------------------------------------------------------
-- Procedure 1: sp_assign_staff_to_complaint
-- Atomically assigns a staff technician, updates status, and logs assignment
-- Uses optimistic concurrency control via version checking
-- ----------------------------------------------------------------------------
CREATE PROCEDURE `sp_assign_staff_to_complaint`(
    IN  p_complaint_id         BIGINT UNSIGNED,
    IN  p_staff_id             INT UNSIGNED,
    IN  p_warden_id            INT UNSIGNED,
    IN  p_expected_version     INT UNSIGNED,
    IN  p_work_notes           TEXT,
    OUT p_success              TINYINT(1),
    OUT p_message              VARCHAR(255)
)
proc_label: BEGIN
    DECLARE v_current_status VARCHAR(30);
    DECLARE v_current_version INT UNSIGNED;
    DECLARE v_student_user_id BIGINT UNSIGNED;
    DECLARE v_staff_user_id BIGINT UNSIGNED;
    DECLARE v_ticket_no VARCHAR(25);
    DECLARE v_staff_avail TINYINT(1);
    DECLARE v_rows_affected INT;

    -- Default exit handler for SQLEXCEPTION
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = 'Database transaction failed during assignment. Rolled back.';
    END;

    START TRANSACTION;

    -- 1. Lock and verify complaint record
    SELECT `status`, `version_id`, `ticket_number`,
           (SELECT `user_id` FROM `students` WHERE `student_id` = `complaints`.`student_id`)
    INTO v_current_status, v_current_version, v_ticket_no, v_student_user_id
    FROM `complaints`
    WHERE `complaint_id` = p_complaint_id
    FOR UPDATE;

    IF v_current_status IS NULL THEN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = 'Complaint record not found.';
        LEAVE proc_label;
    END IF;

    -- 2. Validate optimistic locking version
    IF v_current_version != p_expected_version THEN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = 'Concurrency Conflict: This complaint was modified by another user. Please refresh.';
        LEAVE proc_label;
    END IF;

    -- 3. Verify target staff member exists and is available
    SELECT `user_id`, `is_available`
    INTO v_staff_user_id, v_staff_avail
    FROM `staff`
    WHERE `staff_id` = p_staff_id;

    IF v_staff_user_id IS NULL THEN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = 'Designated maintenance staff member does not exist.';
        LEAVE proc_label;
    END IF;

    -- 4. Create assignment record
    INSERT INTO `complaint_assignments` (
        `complaint_id`, `staff_id`, `assigned_by_warden_id`, `status`, `work_notes`, `assigned_at`
    ) VALUES (
        p_complaint_id, p_staff_id, p_warden_id, 'assigned', p_work_notes, NOW()
    );

    -- 5. Update complaint status and increment version
    UPDATE `complaints`
    SET `status` = 'Assigned',
        `version_id` = `version_id` + 1,
        `updated_at` = NOW()
    WHERE `complaint_id` = p_complaint_id AND `version_id` = p_expected_version;

    SET v_rows_affected = ROW_COUNT();
    IF v_rows_affected = 0 THEN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = 'Concurrent update conflict during complaint status modification.';
        LEAVE proc_label;
    END IF;

    -- 6. Generate alerts for student and assigned staff member
    INSERT INTO `notifications` (`user_id`, `complaint_id`, `title`, `message`, `created_at`)
    VALUES 
    (v_student_user_id, p_complaint_id, 'Complaint Assigned', 
     CONCAT('Your complaint (', v_ticket_no, ') has been assigned to a maintenance technician.'), NOW()),
    (v_staff_user_id, p_complaint_id, 'New Task Assigned', 
     CONCAT('You have been assigned to work on ticket ', v_ticket_no, '. Check your dashboard.'), NOW());

    COMMIT;
    SET p_success = 1;
    SET p_message = 'Staff successfully assigned and work order dispatched.';
END proc_label$$

-- ----------------------------------------------------------------------------
-- Procedure 2: sp_resolve_complaint
-- Warden verifies completion and marks ticket Resolved
-- ----------------------------------------------------------------------------
CREATE PROCEDURE `sp_resolve_complaint`(
    IN  p_complaint_id         BIGINT UNSIGNED,
    IN  p_warden_user_id       BIGINT UNSIGNED,
    IN  p_remarks              TEXT,
    OUT p_success              TINYINT(1),
    OUT p_message              VARCHAR(255)
)
proc_label: BEGIN
    DECLARE v_student_user_id BIGINT UNSIGNED;
    DECLARE v_ticket_no VARCHAR(25);
    DECLARE v_status VARCHAR(30);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = 'Failed to mark complaint resolved. Transaction rolled back.';
    END;

    START TRANSACTION;

    SELECT `status`, `ticket_number`,
           (SELECT `user_id` FROM `students` WHERE `student_id` = `complaints`.`student_id`)
    INTO v_status, v_ticket_no, v_student_user_id
    FROM `complaints`
    WHERE `complaint_id` = p_complaint_id
    FOR UPDATE;

    IF v_status NOT IN ('Awaiting Verification', 'In Progress', 'Assigned', 'Under Review') THEN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = CONCAT('Cannot resolve complaint with current status: ', IFNULL(v_status, 'UNKNOWN'));
        LEAVE proc_label;
    END IF;

    UPDATE `complaints`
    SET `status` = 'Resolved',
        `resolved_at` = NOW(),
        `version_id` = `version_id` + 1
    WHERE `complaint_id` = p_complaint_id;

    -- Mark active assignment as completed
    UPDATE `complaint_assignments`
    SET `status` = 'completed', `completed_at` = NOW()
    WHERE `complaint_id` = p_complaint_id AND `status` != 'completed';

    -- Add official management response
    IF p_remarks IS NOT NULL AND CHAR_LENGTH(TRIM(p_remarks)) > 0 THEN
        INSERT INTO `complaint_responses` (`complaint_id`, `user_id`, `message`, `is_internal`, `created_at`)
        VALUES (p_complaint_id, p_warden_user_id, p_remarks, 0, NOW());
    END IF;

    -- Notify student to inspect and leave feedback
    INSERT INTO `notifications` (`user_id`, `complaint_id`, `title`, `message`, `created_at`)
    VALUES (v_student_user_id, p_complaint_id, 'Complaint Resolved', 
            CONCAT('Your complaint (', v_ticket_no, ') was marked resolved by the warden. Please rate the service.'), NOW());

    COMMIT;
    SET p_success = 1;
    SET p_message = 'Complaint successfully verified and marked Resolved.';
END proc_label$$

-- ----------------------------------------------------------------------------
-- Procedure 3: sp_reopen_complaint
-- Validates student reopen criteria (within 48 hours, maximum 2 reopens)
-- ----------------------------------------------------------------------------
CREATE PROCEDURE `sp_reopen_complaint`(
    IN  p_complaint_id         BIGINT UNSIGNED,
    IN  p_student_user_id      BIGINT UNSIGNED,
    IN  p_reason               TEXT,
    OUT p_success              TINYINT(1),
    OUT p_message              VARCHAR(255)
)
proc_label: BEGIN
    DECLARE v_status VARCHAR(30);
    DECLARE v_resolved_at DATETIME;
    DECLARE v_reopen_count TINYINT UNSIGNED;
    DECLARE v_student_id INT UNSIGNED;
    DECLARE v_ticket_no VARCHAR(25);
    DECLARE v_hostel_id INT UNSIGNED;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = 'Reopen transaction failed. Rolled back.';
    END;

    START TRANSACTION;

    SELECT c.`status`, c.`resolved_at`, c.`reopen_count`, c.`ticket_number`, c.`hostel_id`, s.`student_id`
    INTO v_status, v_resolved_at, v_reopen_count, v_ticket_no, v_hostel_id, v_student_id
    FROM `complaints` c
    JOIN `students` s ON c.`student_id` = s.`student_id`
    WHERE c.`complaint_id` = p_complaint_id AND s.`user_id` = p_student_user_id
    FOR UPDATE;

    IF v_status IS NULL THEN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = 'Complaint not found or access denied.';
        LEAVE proc_label;
    END IF;

    IF v_status != 'Resolved' THEN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = 'Only resolved complaints can be reopened.';
        LEAVE proc_label;
    END IF;

    IF v_reopen_count >= 2 THEN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = 'Maximum reopen limit reached (2 times). Please contact the Chief Warden directly.';
        LEAVE proc_label;
    END IF;

    IF v_resolved_at IS NOT NULL AND TIMESTAMPDIFF(HOUR, v_resolved_at, NOW()) > 48 THEN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = 'Reopen window expired (must be within 48 hours of resolution).';
        LEAVE proc_label;
    END IF;

    -- Update status to Reopened and increment reopen_count
    UPDATE `complaints`
    SET `status` = 'Reopened',
        `reopen_count` = `reopen_count` + 1,
        `priority` = IF(`reopen_count` + 1 >= 2, 'Critical', `priority`),
        `version_id` = `version_id` + 1,
        `updated_at` = NOW()
    WHERE `complaint_id` = p_complaint_id;

    -- Record student response explanation
    INSERT INTO `complaint_responses` (`complaint_id`, `user_id`, `message`, `is_internal`, `created_at`)
    VALUES (p_complaint_id, p_student_user_id, CONCAT('[REOPEN REASON]: ', p_reason), 0, NOW());

    -- Notify wardens of this hostel
    INSERT INTO `notifications` (`user_id`, `complaint_id`, `title`, `message`, `created_at`)
    SELECT w.`user_id`, p_complaint_id, 'Complaint Reopened',
           CONCAT('Student reopened ticket ', v_ticket_no, '. Reason: ', SUBSTRING(p_reason, 1, 60)), NOW()
    FROM `hostel_wardens` hw
    JOIN `wardens` w ON hw.`warden_id` = w.`warden_id`
    WHERE hw.`hostel_id` = v_hostel_id;

    COMMIT;
    SET p_success = 1;
    SET p_message = 'Complaint successfully reopened and escalated to warden review.';
END proc_label$$

-- ----------------------------------------------------------------------------
-- Procedure 4: sp_scan_and_escalate_overdue
-- Scans active complaints past SLA deadline and marks is_overdue = 1
-- ----------------------------------------------------------------------------
CREATE PROCEDURE `sp_scan_and_escalate_overdue`(
    OUT p_escalated_count INT
)
BEGIN
    UPDATE `complaints`
    SET `is_overdue` = 1
    WHERE `status` NOT IN ('Resolved', 'Rejected', 'Cancelled')
      AND `sla_deadline` < NOW()
      AND `is_overdue` = 0;

    SET p_escalated_count = ROW_COUNT();
END$$

DELIMITER ;

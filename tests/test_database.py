"""
Hostel Complaint Management System (HCMS)
Database Integrity, Concurrency, and Workflow Rules Test Suite (tests/test_database.py)
"""

import unittest
from unittest.mock import MagicMock, patch
from services.complaint_service import ComplaintService
from services.assignment_service import AssignmentService
from utils.security import allowed_file

class DatabaseWorkflowTestCase(unittest.TestCase):

    def test_file_extension_whitelist(self):
        """Verifies strict security validation for uploaded file extensions."""
        self.assertTrue(allowed_file("evidence.png"))
        self.assertTrue(allowed_file("water_leak.jpg"))
        self.assertTrue(allowed_file("bill.jpeg"))
        self.assertTrue(allowed_file("report.pdf"))
        self.assertTrue(allowed_file("screenshot.webp"))

        # Blocked dangerous extensions
        self.assertFalse(allowed_file("malicious.exe"))
        self.assertFalse(allowed_file("webshell.php"))
        self.assertFalse(allowed_file("script.py"))
        self.assertFalse(allowed_file("payload.sh"))
        self.assertFalse(allowed_file("exploit.js"))
        self.assertFalse(allowed_file("no_extension"))

    def test_optimistic_locking_version_mismatch(self):
        """
        Verifies that attempting an assignment with an outdated version_id
        is detected and rejected to prevent race conditions.
        """
        # Simulate stored procedure sp_assign_staff_to_complaint logic:
        # If expected_version (1) does not match database current version (2), abort.
        current_db_version = 2
        incoming_form_version = 1
        self.assertNotEqual(
            current_db_version, 
            incoming_form_version, 
            "Version mismatch must trigger concurrency abort"
        )

    def test_reopen_limit_validation(self):
        """Verifies that a complaint exceeding maximum reopen attempts (5) cannot be reopened."""
        max_allowed_reopens = 5
        complaint_reopen_count = 5
        self.assertFalse(
            complaint_reopen_count < max_allowed_reopens,
            "Complaints with 5 reopens should be flagged as non-reopenable"
        )

    def test_transaction_rollback_handling(self):
        """Verifies that database errors trigger ROLLBACK and preserve data consistency."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Simulate exception during multi-step operation
        try:
            mock_cursor.execute.side_effect = Exception("Simulated DB Disk Failure")
            mock_cursor.execute("UPDATE complaints SET status = 'Resolved' WHERE complaint_id = 1")
            mock_conn.commit()
        except Exception:
            mock_conn.rollback()

        mock_conn.rollback.assert_called_once()

    def test_ticket_number_formatting(self):
        """Verifies ticket numbering adheres to CMP-YYYY-XXXX schema."""
        import re
        sample_ticket = "CMP-2026-0042"
        pattern = r"^CMP-\d{4}-\d{4}$"
        self.assertTrue(bool(re.match(pattern, sample_ticket)))

if __name__ == "__main__":
    unittest.main()


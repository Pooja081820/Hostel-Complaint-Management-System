"""
Hostel Complaint Management System (HCMS)
Maintenance Staff Workflow Test Suite (tests/test_staff.py)
"""

import unittest
from app import create_app

class StaffWorkflowTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_unauthenticated_staff_redirects(self):
        """Verifies that accessing staff dashboard without login redirects to /auth/login."""
        response = self.client.get("/staff/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login", response.headers["Location"])

    def test_student_cannot_access_staff_dashboard(self):
        """Verifies that a student user is blocked with HTTP 403 Forbidden."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 9
            sess["role"] = "student"
            sess["name"] = "Rahul Verma"

        response = self.client.get("/staff/dashboard")
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"Access Forbidden", response.data)

    def test_staff_history_page_renders_cleanly(self):
        """Verifies that staff history page renders successfully for staff role."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 6
            sess["staff_id"] = 2
            sess["role"] = "staff"
            sess["name"] = "Suresh Verma"
            sess["specialization"] = "electrical"

        response = self.client.get("/staff/history")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Completed Work Orders History", response.data)

if __name__ == "__main__":
    unittest.main()

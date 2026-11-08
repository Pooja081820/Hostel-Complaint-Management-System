"""
Hostel Complaint Management System (HCMS)
Strict Role-Based Authorization & Tenant Isolation Test Suite (tests/test_permissions.py)
"""

import unittest
from unittest.mock import patch
from app import create_app

class PermissionsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_guest_redirected_from_all_dashboards(self):
        """Verifies that unauthenticated visitors are redirected to login from every protected module."""
        protected_urls = [
            "/student/dashboard",
            "/student/submit",
            "/student/complaints",
            "/warden/dashboard",
            "/warden/complaints",
            "/warden/reports",
            "/staff/dashboard",
            "/staff/history",
            "/admin/dashboard",
            "/admin/users",
            "/admin/hostels",
            "/admin/audit-logs",
            "/notifications"
        ]
        for url in protected_urls:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 302, f"Expected 302 for unauthenticated access to {url}")
            self.assertIn("/auth/login", res.headers["Location"])

    def test_student_forbidden_from_privileged_endpoints(self):
        """Verifies that student accounts receive HTTP 403 Forbidden on warden, staff, and admin routes."""
        privileged_urls = [
            "/warden/dashboard",
            "/warden/complaints",
            "/warden/reports",
            "/staff/dashboard",
            "/staff/history",
            "/admin/dashboard",
            "/admin/users",
            "/admin/hostels",
            "/admin/categories",
            "/admin/audit-logs"
        ]
        with self.client.session_transaction() as sess:
            sess["user_id"] = 101
            sess["role"] = "student"
            sess["student_id"] = 1
            sess["name"] = "Alice Student"

        for url in privileged_urls:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 403, f"Expected 403 Forbidden for student on {url}")

    def test_staff_forbidden_from_admin_and_warden(self):
        """Verifies that maintenance staff cannot tamper with warden or admin panels."""
        forbidden_urls = [
            "/warden/dashboard",
            "/warden/complaints",
            "/warden/reports",
            "/admin/dashboard",
            "/admin/users",
            "/admin/hostels"
        ]
        with self.client.session_transaction() as sess:
            sess["user_id"] = 202
            sess["role"] = "staff"
            sess["staff_id"] = 3
            sess["name"] = "Bob Electrician"

        for url in forbidden_urls:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 403, f"Expected 403 Forbidden for staff on {url}")

    def test_warden_forbidden_from_admin_endpoints(self):
        """Verifies that wardens cannot access administrative system governance views."""
        admin_urls = [
            "/admin/dashboard",
            "/admin/users",
            "/admin/hostels",
            "/admin/categories",
            "/admin/audit-logs"
        ]
        with self.client.session_transaction() as sess:
            sess["user_id"] = 303
            sess["role"] = "warden"
            sess["warden_id"] = 4
            sess["name"] = "Charlie Warden"
            sess["assigned_hostels"] = [1, 2]

        for url in admin_urls:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 403, f"Expected 403 Forbidden for warden on {url}")

    @patch("routes.student.ComplaintService.get_complaint_details")
    def test_cross_student_complaint_isolation(self, mock_get_details):
        """Verifies that a student cannot view another student's private complaint (blocks with redirect)."""
        mock_get_details.side_effect = PermissionError("Unauthorized access to complaint")

        with self.client.session_transaction() as sess:
            sess["user_id"] = 101
            sess["role"] = "student"
            sess["student_id"] = 1  # Alice has student_id 1
            sess["name"] = "Alice Student"

        res = self.client.get("/student/complaints/50", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/student/complaints", res.headers["Location"])

if __name__ == "__main__":
    unittest.main()

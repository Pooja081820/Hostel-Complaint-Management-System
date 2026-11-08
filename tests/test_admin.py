"""
Hostel Complaint Management System (HCMS)
Administrator Governance Test Suite (tests/test_admin.py)
"""

import unittest
from app import create_app

class AdminGovernanceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_unauthenticated_admin_redirects(self):
        """Verifies unauthenticated access to admin endpoints redirects to login."""
        endpoints = [
            "/admin/dashboard",
            "/admin/users",
            "/admin/hostels",
            "/admin/categories",
            "/admin/complaints",
            "/admin/audit-logs"
        ]
        for ep in endpoints:
            response = self.client.get(ep)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/auth/login", response.headers["Location"])

    def test_student_and_warden_cannot_access_admin(self):
        """Verifies RBAC prevents students and wardens from accessing admin endpoints (HTTP 403)."""
        roles_to_test = [
            {"user_id": 9, "role": "student", "name": "Student User"},
            {"user_id": 2, "role": "warden", "name": "Warden User"},
            {"user_id": 5, "role": "staff", "name": "Staff User"}
        ]
        for user_meta in roles_to_test:
            with self.client.session_transaction() as sess:
                sess["user_id"] = user_meta["user_id"]
                sess["role"] = user_meta["role"]
                sess["name"] = user_meta["name"]

            response = self.client.get("/admin/dashboard")
            self.assertEqual(response.status_code, 403)
            self.assertIn(b"Access Forbidden", response.data)

    def test_admin_dashboard_renders_cleanly(self):
        """Verifies that an authorized administrator can view the governance dashboard."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["role"] = "admin"
            sess["name"] = "Chief Administrator"

        response = self.client.get("/admin/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Campus System Governance", response.data)

    def test_admin_subpages_render_cleanly(self):
        """Verifies admin sub-views (users, hostels, categories, audit logs) render cleanly."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["role"] = "admin"
            sess["name"] = "Chief Administrator"

        endpoints = [
            ("/admin/users", b"User Governance"),
            ("/admin/hostels", b"Campus Residential Hostel"),
            ("/admin/categories", b"Complaint Categories"),
            ("/admin/complaints", b"University-Wide Complaints"),
            ("/admin/audit-logs", b"Immutable Security")
        ]
        for ep, expected_text in endpoints:
            response = self.client.get(ep)
            self.assertEqual(response.status_code, 200)
            self.assertIn(expected_text, response.data)

    def test_admin_cannot_deactivate_self(self):
        """Verifies that the system prevents an administrator from deactivating their own active account."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["role"] = "admin"
            sess["name"] = "Chief Administrator"
            sess["_csrf_token"] = "valid_csrf_token"

        response = self.client.post("/admin/users/1/toggle-status", data={
            "csrf_token": "valid_csrf_token"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"You cannot deactivate your own administrative account", response.data)

if __name__ == "__main__":
    unittest.main()

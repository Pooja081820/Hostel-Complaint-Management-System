"""
Hostel Complaint Management System (HCMS)
Authentication & RBAC Test Suite (tests/test_auth.py)
"""

import unittest
from app import create_app
from utils.security import hash_password, verify_password, validate_csrf_token

class AuthenticationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_password_hashing_and_verification(self):
        """Validates cryptographic password hashing and verification using Werkzeug."""
        plain = "SecureStudentPass2026!"
        hashed = hash_password(plain)
        self.assertNotEqual(plain, hashed)
        self.assertTrue(verify_password(hashed, plain))
        self.assertFalse(verify_password(hashed, "WrongPassword123"))

    def test_login_page_renders_cleanly(self):
        """Verifies that the login page loads with CSRF token and demo account buttons."""
        response = self.client.get("/auth/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"HostelCare", response.data)
        self.assertIn(b"csrf_token", response.data)
        self.assertIn(b"student.rahul@hostel.edu", response.data)

    def test_register_page_renders_cleanly(self):
        """Verifies that the registration page loads with form inputs."""
        response = self.client.get("/auth/register")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Student Registration", response.data)
        self.assertIn(b"Allocated Hostel Block", response.data)

    def test_unauthenticated_protected_route_redirects(self):
        """Verifies that unauthenticated requests to protected dashboards redirect to /auth/login."""
        response = self.client.get("/student/dashboard", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login", response.headers["Location"])

    def test_role_based_access_denied(self):
        """Verifies that accessing an endpoint with an improper role returns HTTP 403."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 99
            sess["role"] = "student"  # A student trying to access admin dashboard
            sess["name"] = "Test Student"

        response = self.client.get("/admin/dashboard")
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"Access Forbidden", response.data)

if __name__ == "__main__":
    unittest.main()

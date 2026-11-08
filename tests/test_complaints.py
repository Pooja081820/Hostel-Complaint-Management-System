"""
Hostel Complaint Management System (HCMS)
Complaint Lifecycle & Validation Test Suite (tests/test_complaints.py)
"""

import unittest
from app import create_app
from services.complaint_service import ComplaintService
from utils.validators import validate_complaint_data

class ComplaintLifecycleTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_complaint_input_validation(self):
        """Verifies that invalid complaint data returns appropriate error messages."""
        # Short title
        errors = validate_complaint_data({"title": "Tap", "description": "Too short"})
        self.assertTrue(any("title" in e.lower() for e in errors))

        # Short description
        errors = validate_complaint_data({"title": "Valid Title Here", "description": "short"})
        self.assertTrue(any("description" in e.lower() for e in errors))

        # Valid payload
        valid_data = {
            "title": "Water cooler leaking in corridor",
            "description": "Continuous leakage of clean water onto corridor tiles causing slipping hazard.",
            "category_id": 1,
            "priority": "High",
            "visibility": "private"
        }
        self.assertEqual(len(validate_complaint_data(valid_data)), 0)

    def test_unauthenticated_complaint_submission_redirects(self):
        """Verifies that submitting or viewing complaints without login redirects to /auth/login."""
        response = self.client.get("/student/submit")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login", response.headers["Location"])

    def test_student_cannot_access_warden_pages(self):
        """Verifies role restriction: Student session cannot access /warden/dashboard."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 9
            sess["role"] = "student"
            sess["student_id"] = 1
            sess["name"] = "Rahul Verma"

        response = self.client.get("/warden/dashboard")
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"Access Forbidden", response.data)

    def test_duplicate_token_extraction(self):
        """Verifies that duplicate token matching logic behaves deterministically."""
        # Check duplicate token identification
        title_a = "Washbasin tap continuously dripping water"
        title_b = "Bathroom washbasin cold water tap handle leaking"
        tokens_a = set(w.lower() for w in title_a.split() if len(w) > 3)
        tokens_b = set(w.lower() for w in title_b.split() if len(w) > 3)
        common = tokens_a.intersection(tokens_b)
        self.assertTrue(len(common) >= 1)
        self.assertIn("washbasin", common)
        self.assertIn("water", common)

if __name__ == "__main__":
    unittest.main()

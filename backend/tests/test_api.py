import unittest
import os
import sys

# Ensure backend directory is in path
BACKEND_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import create_app
from app.extensions import db
from app.models.user import User


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_api_login_invalid(self):
        """Test API login with invalid credentials."""
        res = self.client.post("/api/v1/auth/login", json={
            "username": "nonexistent_user",
            "password": "wrong_password"
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data["success"])

    def test_api_login_success(self):
        """Test API login with valid admin credentials."""
        res = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("token", data)
        self.assertEqual(data["user"]["role"], "admin")

    def test_protected_endpoint_without_token(self):
        """Test accessing protected /api/v1/employees without Bearer token."""
        res = self.client.get("/api/v1/employees")
        self.assertEqual(res.status_code, 401)

    def test_protected_endpoint_with_jwt(self):
        """Test accessing protected /api/v1/employees with valid JWT."""
        login_res = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@123"
        })
        token = login_res.get_json()["token"]

        res = self.client.get("/api/v1/employees", headers={
            "Authorization": f"Bearer {token}"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("employees", data)

    def test_analytics_dashboard_endpoint(self):
        """Test analytics dashboard summary endpoint."""
        login_res = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@123"
        })
        token = login_res.get_json()["token"]

        res = self.client.get("/api/v1/analytics/dashboard", headers={
            "Authorization": f"Bearer {token}"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("summary", data)


if __name__ == "__main__":
    unittest.main()

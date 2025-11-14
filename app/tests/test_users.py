"""Tests for user management endpoints."""

import pytest
from fastapi import status


class TestGetCurrentUser:
    """Test getting current user profile."""

    def test_get_me_success(self, client, auth_headers, test_user):
        """Test successfully getting own profile."""
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert data["id"] == test_user.id
        assert "password" not in data

    def test_get_me_unauthorized(self, client):
        """Test getting profile without authentication."""
        response = client.get("/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateCurrentUser:
    """Test updating current user profile."""

    def test_update_me_success(self, client, auth_headers, test_user):
        """Test successfully updating own profile."""
        response = client.put(
            "/users/me",
            headers=auth_headers,
            json={"name": "Updated Name"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["email"] == test_user.email

    def test_update_me_email(self, client, auth_headers, test_user):
        """Test updating email address."""
        response = client.put(
            "/users/me",
            headers=auth_headers,
            json={"email": "newemail@example.com"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "newemail@example.com"

    def test_update_me_unauthorized(self, client):
        """Test updating profile without authentication."""
        response = client.put(
            "/users/me",
            json={"name": "New Name"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAdminGetUser:
    """Test admin getting any user."""

    def test_admin_get_user_success(self, client, admin_headers, test_user):
        """Test admin successfully getting user by ID."""
        response = client.get(
            f"/users/{test_user.id}",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    def test_admin_get_nonexistent_user(self, client, admin_headers):
        """Test admin getting nonexistent user."""
        response = client.get("/users/99999", headers=admin_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_non_admin_get_user_forbidden(self, client, auth_headers, test_user):
        """Test non-admin cannot get user by ID."""
        response = client.get(
            f"/users/{test_user.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAdminListUsers:
    """Test admin listing all users."""

    def test_admin_list_users_success(self, client, admin_headers, test_user, admin_user):
        """Test admin successfully listing all users."""
        response = client.get("/users/", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least test_user and admin_user
        emails = [user["email"] for user in data]
        assert test_user.email in emails
        assert admin_user.email in emails

    def test_admin_list_users_pagination(self, client, admin_headers, db):
        """Test pagination in user listing."""
        # Create additional users
        from app.models.user import User
        from app.core.security import get_password_hash
        
        for i in range(5):
            user = User(
                email=f"user{i}@example.com",
                name=f"User {i}",
                password_hash=get_password_hash("password"),
                is_active=True
            )
            db.add(user)
        db.commit()
        
        response = client.get(
            "/users/?skip=0&limit=3",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 3

    def test_non_admin_list_users_forbidden(self, client, auth_headers):
        """Test non-admin cannot list users."""
        response = client.get("/users/", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUserRoles:
    """Test user role functionality."""

    def test_user_has_user_role(self, client, auth_headers, test_user):
        """Test regular user has USER role."""
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "user"

    def test_admin_has_admin_role(self, client, admin_headers, admin_user):
        """Test admin user has ADMIN role."""
        response = client.get("/users/me", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "admin"


class TestUserStatus:
    """Test user active/inactive status."""

    def test_active_user_can_login(self, client, test_user):
        """Test active user can login."""
        response = client.post(
            "/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        assert response.status_code == status.HTTP_200_OK

    def test_inactive_user_cannot_access(self, client, db, test_user):
        """Test inactive user cannot access endpoints."""
        # Deactivate user
        test_user.is_active = False
        db.commit()
        
        # Try to login
        response = client.post(
            "/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

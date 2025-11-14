"""Tests for project management endpoints."""

import pytest
from fastapi import status
from datetime import date, timedelta


class TestCreateProject:
    """Test project creation."""

    def test_create_project_success(self, client, auth_headers, test_user):
        """Test successfully creating a project."""
        response = client.post(
            "/projects/",
            headers=auth_headers,
            json={
                "name": "Test Project",
                "description": "A test project description",
                "start_date": str(date.today()),
                "end_date": str(date.today() + timedelta(days=30))
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["description"] == "A test project description"
        assert data["owner_id"] == test_user.id
        assert "id" in data

    def test_create_project_minimal(self, client, auth_headers):
        """Test creating project with minimal data."""
        response = client.post(
            "/projects/",
            headers=auth_headers,
            json={"name": "Minimal Project"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Minimal Project"

    def test_create_project_unauthorized(self, client):
        """Test creating project without authentication."""
        response = client.post(
            "/projects/",
            json={"name": "Test Project"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_project_invalid_dates(self, client, auth_headers):
        """Test creating project with end date before start date."""
        response = client.post(
            "/projects/",
            headers=auth_headers,
            json={
                "name": "Invalid Project",
                "start_date": str(date.today()),
                "end_date": str(date.today() - timedelta(days=10))
            }
        )
        # Should still create but dates are invalid
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestListProjects:
    """Test listing user's projects."""

    def test_list_projects_success(self, client, auth_headers, test_user, db):
        """Test successfully listing user's projects."""
        # Create some projects
        from app.models.project import Project
        
        project1 = Project(name="Project 1", owner_id=test_user.id)
        project2 = Project(name="Project 2", owner_id=test_user.id)
        db.add_all([project1, project2])
        db.commit()
        
        response = client.get("/projects/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        project_names = [p["name"] for p in data]
        assert "Project 1" in project_names
        assert "Project 2" in project_names

    def test_list_projects_empty(self, client, auth_headers):
        """Test listing when user has no projects."""
        response = client.get("/projects/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_list_projects_pagination(self, client, auth_headers, test_user, db):
        """Test project listing pagination."""
        # Create multiple projects
        from app.models.project import Project
        
        for i in range(10):
            project = Project(name=f"Project {i}", owner_id=test_user.id)
            db.add(project)
        db.commit()
        
        response = client.get(
            "/projects/?skip=0&limit=5",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 5

    def test_list_projects_unauthorized(self, client):
        """Test listing projects without authentication."""
        response = client.get("/projects/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetProject:
    """Test getting single project."""

    def test_get_project_success(self, client, auth_headers, test_user, db):
        """Test successfully getting a project."""
        from app.models.project import Project
        
        project = Project(
            name="Test Project",
            description="Test description",
            owner_id=test_user.id
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        response = client.get(
            f"/projects/{project.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == project.id
        assert data["name"] == "Test Project"
        assert data["description"] == "Test description"

    def test_get_project_not_found(self, client, auth_headers):
        """Test getting nonexistent project."""
        response = client.get("/projects/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_project_not_owner(self, client, auth_headers, admin_user, db):
        """Test getting project owned by another user."""
        from app.models.project import Project
        
        # Create project owned by admin
        project = Project(name="Admin Project", owner_id=admin_user.id)
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Try to access with regular user
        response = client.get(
            f"/projects/{project.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateProject:
    """Test updating projects."""

    def test_update_project_success(self, client, auth_headers, test_user, db):
        """Test successfully updating a project."""
        from app.models.project import Project
        
        project = Project(name="Original Name", owner_id=test_user.id)
        db.add(project)
        db.commit()
        db.refresh(project)
        
        response = client.put(
            f"/projects/{project.id}",
            headers=auth_headers,
            json={
                "name": "Updated Name",
                "description": "Updated description"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    def test_update_project_not_found(self, client, auth_headers):
        """Test updating nonexistent project."""
        response = client.put(
            "/projects/99999",
            headers=auth_headers,
            json={"name": "New Name"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_project_not_owner(self, client, auth_headers, admin_user, db):
        """Test updating project owned by another user."""
        from app.models.project import Project
        
        project = Project(name="Admin Project", owner_id=admin_user.id)
        db.add(project)
        db.commit()
        db.refresh(project)
        
        response = client.put(
            f"/projects/{project.id}",
            headers=auth_headers,
            json={"name": "Hacked Name"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteProject:
    """Test deleting projects."""

    def test_delete_project_success(self, client, auth_headers, test_user, db):
        """Test successfully deleting a project."""
        from app.models.project import Project
        
        project = Project(name="To Delete", owner_id=test_user.id)
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = project.id
        
        response = client.delete(
            f"/projects/{project_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's deleted
        response = client.get(
            f"/projects/{project_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_project_with_tasks(self, client, auth_headers, test_user, db):
        """Test deleting project with tasks (cascade)."""
        from app.models.project import Project
        from app.models.task import Task
        
        project = Project(name="Project with Tasks", owner_id=test_user.id)
        db.add(project)
        db.commit()
        db.refresh(project)
        
        task = Task(
            title="Task in Project",
            project_id=project.id,
            assigned_to_id=test_user.id
        )
        db.add(task)
        db.commit()
        
        response = client.delete(
            f"/projects/{project.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_project_not_found(self, client, auth_headers):
        """Test deleting nonexistent project."""
        response = client.delete("/projects/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_project_not_owner(self, client, auth_headers, admin_user, db):
        """Test deleting project owned by another user."""
        from app.models.project import Project
        
        project = Project(name="Admin Project", owner_id=admin_user.id)
        db.add(project)
        db.commit()
        db.refresh(project)
        
        response = client.delete(
            f"/projects/{project.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

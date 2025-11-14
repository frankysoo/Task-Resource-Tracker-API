"""Tests for reporting endpoints."""

import pytest
from fastapi import status
from datetime import date, timedelta


class TestCompletionStats:
    """Test task completion statistics."""

    def test_get_completion_stats_success(self, client, admin_headers, test_user, db):
        """Test successfully getting completion statistics."""
        from app.models.task import Task, TaskStatus
        
        # Create tasks with different statuses
        tasks = [
            Task(title="Pending Task", assigned_to_id=test_user.id, status=TaskStatus.PENDING),
            Task(title="In Progress Task", assigned_to_id=test_user.id, status=TaskStatus.IN_PROGRESS),
            Task(title="Done Task 1", assigned_to_id=test_user.id, status=TaskStatus.DONE),
            Task(title="Done Task 2", assigned_to_id=test_user.id, status=TaskStatus.DONE),
        ]
        db.add_all(tasks)
        db.commit()
        
        response = client.get("/reports/completion", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check that stats are returned
        assert isinstance(data, dict)
        assert "total_tasks" in data
        assert "pending" in data
        assert "in_progress" in data
        assert "done" in data
        assert data["total_tasks"] >= 4
        assert data["pending"] >= 1
        assert data["in_progress"] >= 1
        assert data["done"] >= 2

    def test_get_completion_stats_no_tasks(self, client, admin_headers):
        """Test completion stats when no tasks exist."""
        response = client.get("/reports/completion", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, dict)
        assert data["total_tasks"] == 0

    def test_get_completion_stats_unauthorized(self, client, auth_headers):
        """Test non-admin cannot access completion stats."""
        response = client.get("/reports/completion", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestOverdueTasks:
    """Test overdue tasks report."""

    def test_get_overdue_tasks_success(self, client, admin_headers, test_user, db):
        """Test successfully getting overdue tasks."""
        from app.models.task import Task, TaskStatus
        
        # Create overdue and non-overdue tasks
        overdue_task = Task(
            title="Overdue Task",
            assigned_to_id=test_user.id,
            status=TaskStatus.PENDING,
            due_date=date.today() - timedelta(days=1)  # Yesterday
        )
        future_task = Task(
            title="Future Task",
            assigned_to_id=test_user.id,
            status=TaskStatus.PENDING,
            due_date=date.today() + timedelta(days=7)  # Next week
        )
        done_overdue_task = Task(
            title="Done Overdue Task",
            assigned_to_id=test_user.id,
            status=TaskStatus.DONE,
            due_date=date.today() - timedelta(days=5)  # 5 days ago
        )
        db.add_all([overdue_task, future_task, done_overdue_task])
        db.commit()
        
        response = client.get("/reports/overdue", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert isinstance(data, list)
        # Should only return the pending overdue task
        assert len(data) >= 1
        overdue_titles = [task["title"] for task in data]
        assert "Overdue Task" in overdue_titles
        assert "Future Task" not in overdue_titles
        assert "Done Overdue Task" not in overdue_titles

    def test_get_overdue_tasks_no_overdue(self, client, admin_headers, test_user, db):
        """Test overdue tasks when none are overdue."""
        from app.models.task import Task
        
        # Create only future tasks
        future_task = Task(
            title="Future Task",
            assigned_to_id=test_user.id,
            due_date=date.today() + timedelta(days=7)
        )
        db.add(future_task)
        db.commit()
        
        response = client.get("/reports/overdue", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_overdue_tasks_unauthorized(self, client, auth_headers):
        """Test non-admin cannot access overdue tasks."""
        response = client.get("/reports/overdue", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestProjectStats:
    """Test project statistics."""

    def test_get_project_stats_success(self, client, admin_headers, test_user, admin_user, db):
        """Test successfully getting project statistics."""
        from app.models.project import Project
        from app.models.task import Task, TaskStatus
        
        # Create projects with different states
        empty_project = Project(name="Empty Project", owner_id=test_user.id)
        
        active_project = Project(name="Active Project", owner_id=test_user.id)
        db.add(active_project)
        db.commit()
        db.refresh(active_project)
        
        # Add incomplete tasks to active project
        active_task = Task(
            title="Active Task",
            project_id=active_project.id,
            assigned_to_id=test_user.id,
            status=TaskStatus.IN_PROGRESS
        )
        
        completed_project = Project(name="Completed Project", owner_id=admin_user.id)
        db.add(completed_project)
        db.commit()
        db.refresh(completed_project)
        
        # Add completed tasks to completed project
        completed_task = Task(
            title="Completed Task",
            project_id=completed_project.id,
            assigned_to_id=admin_user.id,
            status=TaskStatus.DONE
        )
        
        db.add_all([empty_project, active_task, completed_task])
        db.commit()
        
        response = client.get("/reports/projects", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert isinstance(data, dict)
        assert "total_projects" in data
        assert "active_projects" in data
        assert "completed_projects" in data
        assert "projects_with_tasks" in data
        
        assert data["total_projects"] >= 3
        assert data["active_projects"] >= 1  # Active project with incomplete tasks
        assert data["completed_projects"] >= 1  # Completed project with all tasks done
        assert data["projects_with_tasks"] >= 2  # Active and completed projects

    def test_get_project_stats_no_projects(self, client, admin_headers):
        """Test project stats when no projects exist."""
        response = client.get("/reports/projects", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, dict)
        assert data["total_projects"] == 0
        assert data["active_projects"] == 0
        assert data["completed_projects"] == 0
        assert data["projects_with_tasks"] == 0

    def test_get_project_stats_unauthorized(self, client, auth_headers):
        """Test non-admin cannot access project stats."""
        response = client.get("/reports/projects", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestReportDataIntegrity:
    """Test that reports return correct data."""

    def test_completion_stats_accuracy(self, client, admin_headers, test_user, db):
        """Test completion stats are accurate."""
        from app.models.task import Task, TaskStatus
        
        # Create exactly 3 pending, 2 in_progress, 4 done
        tasks = []
        for i in range(3):
            tasks.append(Task(
                title=f"Pending {i}",
                assigned_to_id=test_user.id,
                status=TaskStatus.PENDING
            ))
        for i in range(2):
            tasks.append(Task(
                title=f"In Progress {i}",
                assigned_to_id=test_user.id,
                status=TaskStatus.IN_PROGRESS
            ))
        for i in range(4):
            tasks.append(Task(
                title=f"Done {i}",
                assigned_to_id=test_user.id,
                status=TaskStatus.DONE
            ))
        
        db.add_all(tasks)
        db.commit()
        
        response = client.get("/reports/completion", headers=admin_headers)
        data = response.json()
        
        assert data["total_tasks"] >= 9
        assert data["pending"] >= 3
        assert data["in_progress"] >= 2
        assert data["done"] >= 4

    def test_overdue_tasks_only_pending(self, client, admin_headers, test_user, db):
        """Test that only pending overdue tasks are reported."""
        from app.models.task import Task, TaskStatus
        
        # Create overdue tasks with different statuses
        overdue_pending = Task(
            title="Overdue Pending",
            assigned_to_id=test_user.id,
            status=TaskStatus.PENDING,
            due_date=date.today() - timedelta(days=1)
        )
        overdue_in_progress = Task(
            title="Overdue In Progress",
            assigned_to_id=test_user.id,
            status=TaskStatus.IN_PROGRESS,
            due_date=date.today() - timedelta(days=2)
        )
        overdue_done = Task(
            title="Overdue Done",
            assigned_to_id=test_user.id,
            status=TaskStatus.DONE,
            due_date=date.today() - timedelta(days=3)
        )
        
        db.add_all([overdue_pending, overdue_in_progress, overdue_done])
        db.commit()
        
        response = client.get("/reports/overdue", headers=admin_headers)
        data = response.json()
        
        # Should only return the pending overdue task
        assert len(data) >= 1
        titles = [task["title"] for task in data]
        assert "Overdue Pending" in titles
        assert "Overdue In Progress" not in titles
        assert "Overdue Done" not in titles

    def test_project_stats_calculation(self, client, admin_headers, test_user, db):
        """Test project statistics calculation."""
        from app.models.project import Project
        from app.models.task import Task, TaskStatus
        
        # Create projects
        project1 = Project(name="Project 1", owner_id=test_user.id)  # Empty
        project2 = Project(name="Project 2", owner_id=test_user.id)  # Active
        project3 = Project(name="Project 3", owner_id=test_user.id)  # Completed
        
        db.add_all([project1, project2, project3])
        db.commit()
        
        # Refresh to get IDs
        db.refresh(project2)
        db.refresh(project3)
        
        # Add tasks
        active_task = Task(
            title="Active Task",
            project_id=project2.id,
            assigned_to_id=test_user.id,
            status=TaskStatus.IN_PROGRESS
        )
        completed_task = Task(
            title="Completed Task",
            project_id=project3.id,
            assigned_to_id=test_user.id,
            status=TaskStatus.DONE
        )
        
        db.add_all([active_task, completed_task])
        db.commit()
        
        response = client.get("/reports/projects", headers=admin_headers)
        data = response.json()
        
        assert data["total_projects"] >= 3
        assert data["active_projects"] >= 1  # Project 2
        assert data["completed_projects"] >= 1  # Project 3
        assert data["projects_with_tasks"] >= 2  # Projects 2 and 3


class TestReportEdgeCases:
    """Test edge cases in reporting."""

    def test_reports_with_multiple_users(self, client, admin_headers, test_user, admin_user, db):
        """Test reports work correctly with multiple users."""
        from app.models.task import Task, TaskStatus
        
        # Create tasks for different users
        user_task = Task(
            title="User Task",
            assigned_to_id=test_user.id,
            status=TaskStatus.DONE
        )
        admin_task = Task(
            title="Admin Task",
            assigned_to_id=admin_user.id,
            status=TaskStatus.PENDING
        )
        
        db.add_all([user_task, admin_task])
        db.commit()
        
        # Completion stats should include all tasks
        response = client.get("/reports/completion", headers=admin_headers)
        data = response.json()
        assert data["total_tasks"] >= 2
        assert data["done"] >= 1
        assert data["pending"] >= 1

    def test_overdue_tasks_different_users(self, client, admin_headers, test_user, admin_user, db):
        """Test overdue tasks from different users."""
        from app.models.task import Task, TaskStatus
        
        # Create overdue tasks for different users
        user_overdue = Task(
            title="User Overdue",
            assigned_to_id=test_user.id,
            status=TaskStatus.PENDING,
            due_date=date.today() - timedelta(days=1)
        )
        admin_overdue = Task(
            title="Admin Overdue",
            assigned_to_id=admin_user.id,
            status=TaskStatus.PENDING,
            due_date=date.today() - timedelta(days=2)
        )
        
        db.add_all([user_overdue, admin_overdue])
        db.commit()
        
        response = client.get("/reports/overdue", headers=admin_headers)
        data = response.json()
        
        # Should return both overdue tasks
        assert len(data) >= 2
        titles = [task["title"] for task in data]
        assert "User Overdue" in titles
        assert "Admin Overdue" in titles

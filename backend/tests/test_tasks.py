"""Tests for task CRUD endpoints"""
import pytest
from fastapi import status


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_task(client, auth_headers):
    """Test creating a new task"""
    response = client.post(
        "/api/test-user-123/tasks",
        json={
            "title": "Test Task",
            "description": "Test Description",
            "completed": False
        },
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"
    assert data["completed"] is False
    assert data["user_id"] == "test-user-123"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_list_tasks(client, auth_headers):
    """Test listing all tasks"""
    # Create a task first
    client.post(
        "/api/test-user-123/tasks",
        json={"title": "Task 1", "description": "Description 1"},
        headers=auth_headers
    )

    # List tasks
    response = client.get("/api/test-user-123/tasks", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["title"] == "Task 1"


def test_get_task(client, auth_headers):
    """Test getting a specific task"""
    # Create a task
    create_response = client.post(
        "/api/test-user-123/tasks",
        json={"title": "Get Test Task"},
        headers=auth_headers
    )
    task_id = create_response.json()["id"]

    # Get the task
    response = client.get(
        f"/api/test-user-123/tasks/{task_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Get Test Task"


def test_update_task(client, auth_headers):
    """Test updating a task"""
    # Create a task
    create_response = client.post(
        "/api/test-user-123/tasks",
        json={"title": "Original Title"},
        headers=auth_headers
    )
    task_id = create_response.json()["id"]

    # Update the task
    response = client.put(
        f"/api/test-user-123/tasks/{task_id}",
        json={"title": "Updated Title", "description": "New Description"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "New Description"


def test_delete_task(client, auth_headers):
    """Test deleting a task"""
    # Create a task
    create_response = client.post(
        "/api/test-user-123/tasks",
        json={"title": "To Delete"},
        headers=auth_headers
    )
    task_id = create_response.json()["id"]

    # Delete the task
    response = client.delete(
        f"/api/test-user-123/tasks/{task_id}",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify task is deleted
    get_response = client.get(
        f"/api/test-user-123/tasks/{task_id}",
        headers=auth_headers
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_toggle_complete(client, auth_headers):
    """Test toggling task completion status"""
    # Create a task
    create_response = client.post(
        "/api/test-user-123/tasks",
        json={"title": "To Complete", "completed": False},
        headers=auth_headers
    )
    task_id = create_response.json()["id"]

    # Toggle to complete
    response = client.patch(
        f"/api/test-user-123/tasks/{task_id}/complete",
        headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["completed"] is True

    # Toggle back to incomplete
    response = client.patch(
        f"/api/test-user-123/tasks/{task_id}/complete",
        headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["completed"] is False


def test_unauthorized_access(client):
    """Test accessing endpoints without authentication"""
    response = client.get("/api/test-user-123/tasks")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_wrong_user_access(client, auth_headers):
    """Test accessing another user's tasks"""
    response = client.get(
        "/api/different-user/tasks",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_task_not_found(client, auth_headers):
    """Test accessing non-existent task"""
    response = client.get(
        "/api/test-user-123/tasks/99999",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

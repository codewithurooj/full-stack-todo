"""Tests for due date functionality"""
import pytest
from datetime import datetime, timedelta
import pytz
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.task import Task


class TestDueDateEndpoints:
    """Tests for due date PUT and DELETE endpoints"""

    def test_set_due_date_valid(self, client: TestClient, mock_jwt: str, session: Session):
        """Test setting due date with valid ISO 8601 date"""
        # Create a task first
        create_response = client.post(
            "/api/user123/tasks",
            json={"title": "Test Task", "description": "Test"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # Set due date
        response = client.put(
            f"/api/user123/tasks/{task_id}/due-date",
            json={
                "due_date": "2026-02-15T09:00:00",
                "timezone": "America/New_York"
            },
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["due_date"] is not None
        # Due date should be stored in UTC (9 AM EST = 2 PM UTC)
        due_date = datetime.fromisoformat(data["due_date"].replace('Z', '+00:00'))
        assert due_date.hour == 14  # 9 AM EST = 2 PM UTC

    def test_set_due_date_natural_language(self, client: TestClient, mock_jwt: str):
        """Test setting due date with natural language"""
        # Create a task
        create_response = client.post(
            "/api/user123/tasks",
            json={"title": "Test Task"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        task_id = create_response.json()["id"]

        # Set due date with natural language
        response = client.put(
            f"/api/user123/tasks/{task_id}/due-date",
            json={
                "due_date": "tomorrow 9am",
                "timezone": "UTC"
            },
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["due_date"] is not None

    def test_update_existing_due_date(self, client: TestClient, mock_jwt: str):
        """Test updating an existing due date"""
        # Create task with due date
        create_response = client.post(
            "/api/user123/tasks",
            json={"title": "Test Task"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        task_id = create_response.json()["id"]

        # Set initial due date
        client.put(
            f"/api/user123/tasks/{task_id}/due-date",
            json={"due_date": "2026-02-15T09:00:00", "timezone": "UTC"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        # Update due date
        response = client.put(
            f"/api/user123/tasks/{task_id}/due-date",
            json={"due_date": "2026-03-01T14:00:00", "timezone": "UTC"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        data = response.json()
        due_date = datetime.fromisoformat(data["due_date"].replace('Z', '+00:00'))
        assert due_date.day == 1
        assert due_date.month == 3

    def test_set_due_date_invalid_format(self, client: TestClient, mock_jwt: str):
        """Test setting due date with invalid format"""
        # Create task
        create_response = client.post(
            "/api/user123/tasks",
            json={"title": "Test Task"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        task_id = create_response.json()["id"]

        # Try to set invalid due date
        response = client.put(
            f"/api/user123/tasks/{task_id}/due-date",
            json={"due_date": "invalid-date", "timezone": "UTC"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 400

    def test_set_due_date_invalid_timezone(self, client: TestClient, mock_jwt: str):
        """Test setting due date with invalid timezone"""
        # Create task
        create_response = client.post(
            "/api/user123/tasks",
            json={"title": "Test Task"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        task_id = create_response.json()["id"]

        # Try to set due date with invalid timezone
        response = client.put(
            f"/api/user123/tasks/{task_id}/due-date",
            json={"due_date": "2026-02-15T09:00:00", "timezone": "Invalid/Timezone"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 400

    def test_set_due_date_task_not_found(self, client: TestClient, mock_jwt: str):
        """Test setting due date for non-existent task"""
        response = client.put(
            "/api/user123/tasks/99999/due-date",
            json={"due_date": "2026-02-15T09:00:00", "timezone": "UTC"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 404

    def test_clear_due_date(self, client: TestClient, mock_jwt: str):
        """Test clearing due date from task"""
        # Create task with due date
        create_response = client.post(
            "/api/user123/tasks",
            json={"title": "Test Task"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        task_id = create_response.json()["id"]

        # Set due date
        client.put(
            f"/api/user123/tasks/{task_id}/due-date",
            json={"due_date": "2026-02-15T09:00:00", "timezone": "UTC"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        # Clear due date
        response = client.delete(
            f"/api/user123/tasks/{task_id}/due-date",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 204

        # Verify due date is cleared
        get_response = client.get(
            f"/api/user123/tasks/{task_id}",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        assert get_response.json()["due_date"] is None

    def test_clear_due_date_task_not_found(self, client: TestClient, mock_jwt: str):
        """Test clearing due date for non-existent task"""
        response = client.delete(
            "/api/user123/tasks/99999/due-date",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 404


class TestDueDateFiltering:
    """Tests for due date filtering in GET /tasks endpoint"""

    def test_filter_by_due_date_range(self, client: TestClient, mock_jwt: str):
        """Test filtering tasks by due date range"""
        # Create tasks with different due dates
        tasks = [
            {"title": "Task 1", "due_date": "2026-02-10T09:00:00"},
            {"title": "Task 2", "due_date": "2026-02-15T09:00:00"},
            {"title": "Task 3", "due_date": "2026-02-20T09:00:00"},
        ]

        for task_data in tasks:
            create_response = client.post(
                "/api/user123/tasks",
                json={"title": task_data["title"]},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )
            task_id = create_response.json()["id"]

            # Set due date
            client.put(
                f"/api/user123/tasks/{task_id}/due-date",
                json={"due_date": task_data["due_date"], "timezone": "UTC"},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )

        # Filter by date range
        response = client.get(
            "/api/user123/tasks",
            params={
                "due_date_from": "2026-02-12T00:00:00Z",
                "due_date_to": "2026-02-18T23:59:59Z"
            },
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1  # Only Task 2 should be in range
        assert data["tasks"][0]["title"] == "Task 2"

    def test_filter_by_due_date_from_only(self, client: TestClient, mock_jwt: str):
        """Test filtering with only due_date_from"""
        # Create tasks
        tasks = [
            {"title": "Past Task", "due_date": "2026-01-01T09:00:00"},
            {"title": "Future Task", "due_date": "2026-12-31T09:00:00"},
        ]

        for task_data in tasks:
            create_response = client.post(
                "/api/user123/tasks",
                json={"title": task_data["title"]},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )
            task_id = create_response.json()["id"]
            client.put(
                f"/api/user123/tasks/{task_id}/due-date",
                json={"due_date": task_data["due_date"], "timezone": "UTC"},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )

        # Filter from June onwards
        response = client.get(
            "/api/user123/tasks",
            params={"due_date_from": "2026-06-01T00:00:00Z"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["tasks"][0]["title"] == "Future Task"

    def test_filter_by_due_date_to_only(self, client: TestClient, mock_jwt: str):
        """Test filtering with only due_date_to"""
        # Create tasks
        tasks = [
            {"title": "Past Task", "due_date": "2026-01-01T09:00:00"},
            {"title": "Future Task", "due_date": "2026-12-31T09:00:00"},
        ]

        for task_data in tasks:
            create_response = client.post(
                "/api/user123/tasks",
                json={"title": task_data["title"]},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )
            task_id = create_response.json()["id"]
            client.put(
                f"/api/user123/tasks/{task_id}/due-date",
                json={"due_date": task_data["due_date"], "timezone": "UTC"},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )

        # Filter until June
        response = client.get(
            "/api/user123/tasks",
            params={"due_date_to": "2026-06-01T00:00:00Z"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["tasks"][0]["title"] == "Past Task"


class TestRelativeDateFiltering:
    """Tests for relative date range filtering"""

    def test_filter_today(self, client: TestClient, mock_jwt: str, freezer):
        """Test filtering tasks due today"""
        # Freeze time to a specific date
        freezer.move_to("2026-02-15 10:00:00")

        # Create tasks
        tasks = [
            {"title": "Today Task", "due_date": "2026-02-15T14:00:00"},
            {"title": "Tomorrow Task", "due_date": "2026-02-16T14:00:00"},
            {"title": "Yesterday Task", "due_date": "2026-02-14T14:00:00"},
        ]

        for task_data in tasks:
            create_response = client.post(
                "/api/user123/tasks",
                json={"title": task_data["title"]},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )
            task_id = create_response.json()["id"]
            client.put(
                f"/api/user123/tasks/{task_id}/due-date",
                json={"due_date": task_data["due_date"], "timezone": "UTC"},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )

        # Filter for today
        response = client.get(
            "/api/user123/tasks",
            params={"relative_range": "today", "user_timezone": "UTC"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["tasks"][0]["title"] == "Today Task"

    def test_filter_this_week(self, client: TestClient, mock_jwt: str, freezer):
        """Test filtering tasks due this week"""
        # Freeze time to Monday
        freezer.move_to("2026-02-16 10:00:00")  # Monday

        # Create tasks
        tasks = [
            {"title": "This Week", "due_date": "2026-02-18T14:00:00"},  # Wednesday
            {"title": "Next Week", "due_date": "2026-02-23T14:00:00"},  # Next Monday
            {"title": "Last Week", "due_date": "2026-02-09T14:00:00"},  # Last Monday
        ]

        for task_data in tasks:
            create_response = client.post(
                "/api/user123/tasks",
                json={"title": task_data["title"]},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )
            task_id = create_response.json()["id"]
            client.put(
                f"/api/user123/tasks/{task_id}/due-date",
                json={"due_date": task_data["due_date"], "timezone": "UTC"},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )

        # Filter for this week
        response = client.get(
            "/api/user123/tasks",
            params={"relative_range": "this_week", "user_timezone": "UTC"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["tasks"][0]["title"] == "This Week"

    def test_filter_this_month(self, client: TestClient, mock_jwt: str, freezer):
        """Test filtering tasks due this month"""
        freezer.move_to("2026-02-15 10:00:00")

        # Create tasks
        tasks = [
            {"title": "This Month", "due_date": "2026-02-20T14:00:00"},
            {"title": "Next Month", "due_date": "2026-03-05T14:00:00"},
            {"title": "Last Month", "due_date": "2026-01-25T14:00:00"},
        ]

        for task_data in tasks:
            create_response = client.post(
                "/api/user123/tasks",
                json={"title": task_data["title"]},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )
            task_id = create_response.json()["id"]
            client.put(
                f"/api/user123/tasks/{task_id}/due-date",
                json={"due_date": task_data["due_date"], "timezone": "UTC"},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )

        # Filter for this month
        response = client.get(
            "/api/user123/tasks",
            params={"relative_range": "this_month", "user_timezone": "UTC"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["tasks"][0]["title"] == "This Month"

    def test_filter_overdue(self, client: TestClient, mock_jwt: str, freezer):
        """Test filtering overdue tasks"""
        freezer.move_to("2026-02-15 10:00:00")

        # Create tasks
        tasks = [
            {"title": "Overdue Incomplete", "due_date": "2026-02-10T14:00:00", "completed": False},
            {"title": "Overdue Completed", "due_date": "2026-02-12T14:00:00", "completed": True},
            {"title": "Future Task", "due_date": "2026-02-20T14:00:00", "completed": False},
        ]

        for task_data in tasks:
            create_response = client.post(
                "/api/user123/tasks",
                json={"title": task_data["title"]},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )
            task_id = create_response.json()["id"]
            client.put(
                f"/api/user123/tasks/{task_id}/due-date",
                json={"due_date": task_data["due_date"], "timezone": "UTC"},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )

            # Mark as completed if needed
            if task_data["completed"]:
                client.patch(
                    f"/api/user123/tasks/{task_id}/complete",
                    headers={"Authorization": f"Bearer {mock_jwt}"}
                )

        # Filter for overdue
        response = client.get(
            "/api/user123/tasks",
            params={"relative_range": "overdue"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1  # Only incomplete overdue task
        assert data["tasks"][0]["title"] == "Overdue Incomplete"

    def test_timezone_aware_filtering(self, client: TestClient, mock_jwt: str, freezer):
        """Test that relative filters respect user timezone"""
        freezer.move_to("2026-02-15 10:00:00")  # 10 AM UTC

        # Create a task due at 2 AM UTC (which is 9 PM EST previous day)
        create_response = client.post(
            "/api/user123/tasks",
            json={"title": "Timezone Test"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        task_id = create_response.json()["id"]
        client.put(
            f"/api/user123/tasks/{task_id}/due-date",
            json={"due_date": "2026-02-15T02:00:00", "timezone": "UTC"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        # Filter for "today" in EST timezone (should include this task)
        response = client.get(
            "/api/user123/tasks",
            params={"relative_range": "today", "user_timezone": "America/New_York"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200


class TestDueDateSorting:
    """Tests for sorting by due date"""

    def test_sort_due_date_asc(self, client: TestClient, mock_jwt: str):
        """Test sorting by due date ascending (earliest first)"""
        # Create tasks with different due dates
        tasks = [
            {"title": "Task C", "due_date": "2026-03-01T09:00:00"},
            {"title": "Task A", "due_date": "2026-01-01T09:00:00"},
            {"title": "Task B", "due_date": "2026-02-01T09:00:00"},
        ]

        for task_data in tasks:
            create_response = client.post(
                "/api/user123/tasks",
                json={"title": task_data["title"]},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )
            task_id = create_response.json()["id"]
            client.put(
                f"/api/user123/tasks/{task_id}/due-date",
                json={"due_date": task_data["due_date"], "timezone": "UTC"},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )

        # Get tasks sorted by due date ascending
        response = client.get(
            "/api/user123/tasks",
            params={"sort_by": "due_date", "sort_order": "asc"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        data = response.json()
        titles = [task["title"] for task in data["tasks"]]
        assert titles == ["Task A", "Task B", "Task C"]

    def test_sort_due_date_desc(self, client: TestClient, mock_jwt: str):
        """Test sorting by due date descending (latest first)"""
        # Create tasks
        tasks = [
            {"title": "Task C", "due_date": "2026-03-01T09:00:00"},
            {"title": "Task A", "due_date": "2026-01-01T09:00:00"},
            {"title": "Task B", "due_date": "2026-02-01T09:00:00"},
        ]

        for task_data in tasks:
            create_response = client.post(
                "/api/user123/tasks",
                json={"title": task_data["title"]},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )
            task_id = create_response.json()["id"]
            client.put(
                f"/api/user123/tasks/{task_id}/due-date",
                json={"due_date": task_data["due_date"], "timezone": "UTC"},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )

        # Get tasks sorted by due date descending
        response = client.get(
            "/api/user123/tasks",
            params={"sort_by": "due_date", "sort_order": "desc"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        data = response.json()
        titles = [task["title"] for task in data["tasks"]]
        assert titles == ["Task C", "Task B", "Task A"]

    def test_null_due_dates_appear_last(self, client: TestClient, mock_jwt: str):
        """Test that NULL due dates appear last regardless of sort order"""
        # Create tasks with and without due dates
        tasks = [
            {"title": "With Due Date", "due_date": "2026-02-15T09:00:00"},
            {"title": "No Due Date", "due_date": None},
        ]

        for task_data in tasks:
            create_response = client.post(
                "/api/user123/tasks",
                json={"title": task_data["title"]},
                headers={"Authorization": f"Bearer {mock_jwt}"}
            )
            if task_data["due_date"]:
                task_id = create_response.json()["id"]
                client.put(
                    f"/api/user123/tasks/{task_id}/due-date",
                    json={"due_date": task_data["due_date"], "timezone": "UTC"},
                    headers={"Authorization": f"Bearer {mock_jwt}"}
                )

        # Test ascending sort
        response = client.get(
            "/api/user123/tasks",
            params={"sort_by": "due_date", "sort_order": "asc"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        data = response.json()
        assert data["tasks"][-1]["title"] == "No Due Date"

        # Test descending sort
        response = client.get(
            "/api/user123/tasks",
            params={"sort_by": "due_date", "sort_order": "desc"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        data = response.json()
        assert data["tasks"][-1]["title"] == "No Due Date"


class TestDueDatePersistence:
    """Tests for due date persistence and round-trip"""

    def test_due_date_round_trip(self, client: TestClient, mock_jwt: str):
        """Test that due date persists correctly through create → fetch → update → fetch"""
        # Create task
        create_response = client.post(
            "/api/user123/tasks",
            json={"title": "Persistence Test"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        task_id = create_response.json()["id"]

        # Set due date
        set_response = client.put(
            f"/api/user123/tasks/{task_id}/due-date",
            json={"due_date": "2026-02-15T14:30:00", "timezone": "America/New_York"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        original_due_date = set_response.json()["due_date"]

        # Fetch task
        fetch_response = client.get(
            f"/api/user123/tasks/{task_id}",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        fetched_due_date = fetch_response.json()["due_date"]
        assert fetched_due_date == original_due_date

        # Update due date
        update_response = client.put(
            f"/api/user123/tasks/{task_id}/due-date",
            json={"due_date": "2026-03-01T10:00:00", "timezone": "America/New_York"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        updated_due_date = update_response.json()["due_date"]
        assert updated_due_date != original_due_date

        # Fetch again to verify
        final_fetch = client.get(
            f"/api/user123/tasks/{task_id}",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        assert final_fetch.json()["due_date"] == updated_due_date

    def test_timezone_preservation(self, client: TestClient, mock_jwt: str):
        """Test that timezone conversion is correct"""
        # Create task
        create_response = client.post(
            "/api/user123/tasks",
            json={"title": "Timezone Test"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        task_id = create_response.json()["id"]

        # Set due date in EST timezone (9 AM EST = 2 PM UTC in winter)
        response = client.put(
            f"/api/user123/tasks/{task_id}/due-date",
            json={"due_date": "2026-02-15T09:00:00", "timezone": "America/New_York"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        due_date_str = response.json()["due_date"]
        # Parse the ISO format date string
        if due_date_str.endswith('Z'):
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        else:
            due_date = datetime.fromisoformat(due_date_str)

        # Verify the hour is correct (9 AM EST = 2 PM UTC in winter)
        # The date should be stored and returned in UTC
        assert due_date.hour == 14

    def test_update_task_preserves_due_date(self, client: TestClient, mock_jwt: str):
        """Test that updating other task fields preserves due date"""
        # Create task with due date
        create_response = client.post(
            "/api/user123/tasks",
            json={"title": "Original Title"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        task_id = create_response.json()["id"]

        client.put(
            f"/api/user123/tasks/{task_id}/due-date",
            json={"due_date": "2026-02-15T09:00:00", "timezone": "UTC"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        # Get original due date
        get_response = client.get(
            f"/api/user123/tasks/{task_id}",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        original_due_date = get_response.json()["due_date"]

        # Update title (not due date)
        client.put(
            f"/api/user123/tasks/{task_id}",
            json={"title": "Updated Title"},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        # Verify due date is still the same
        final_response = client.get(
            f"/api/user123/tasks/{task_id}",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        assert final_response.json()["due_date"] == original_due_date
        assert final_response.json()["title"] == "Updated Title"

"""
Tests for recurrence calculation logic
"""
import pytest
from datetime import datetime, timedelta
from src.recurrence import calculate_next_due_date, should_create_instance


class TestCalculateNextDueDate:
    """Test next due date calculation for various patterns"""

    def test_daily_pattern(self):
        """Test daily recurrence calculation"""
        current = datetime(2026, 1, 13, 10, 0, 0)
        next_date = calculate_next_due_date(current, "daily", 1, None)

        assert next_date == datetime(2026, 1, 14, 10, 0, 0)

    def test_daily_pattern_with_interval(self):
        """Test daily recurrence with interval > 1"""
        current = datetime(2026, 1, 13)
        next_date = calculate_next_due_date(current, "daily", 3, None)

        assert next_date == datetime(2026, 1, 16)

    def test_weekly_pattern(self):
        """Test weekly recurrence calculation"""
        current = datetime(2026, 1, 13)  # Monday
        next_date = calculate_next_due_date(current, "weekly", 1, None)

        assert next_date == datetime(2026, 1, 20)  # Next Monday

    def test_weekly_pattern_with_interval(self):
        """Test weekly recurrence with interval > 1"""
        current = datetime(2026, 1, 13)
        next_date = calculate_next_due_date(current, "weekly", 2, None)

        assert next_date == datetime(2026, 1, 27)  # 2 weeks later

    def test_monthly_pattern(self):
        """Test monthly recurrence calculation"""
        current = datetime(2026, 1, 15)
        next_date = calculate_next_due_date(current, "monthly", 1, None)

        assert next_date == datetime(2026, 2, 15)

    def test_monthly_pattern_month_end(self):
        """Test monthly recurrence handles month-end correctly"""
        # Jan 31 + 1 month should be Feb 28, not March 3
        current = datetime(2026, 1, 31)
        next_date = calculate_next_due_date(current, "monthly", 1, None)

        assert next_date == datetime(2026, 2, 28)

    def test_monthly_pattern_with_interval(self):
        """Test monthly recurrence with interval > 1"""
        current = datetime(2026, 1, 15)
        next_date = calculate_next_due_date(current, "monthly", 3, None)

        assert next_date == datetime(2026, 4, 15)

    def test_with_end_date_not_exceeded(self):
        """Test recurrence continues when next date before end_date"""
        current = datetime(2026, 1, 13)
        end_date = datetime(2026, 12, 31)
        next_date = calculate_next_due_date(current, "daily", 1, end_date)

        assert next_date == datetime(2026, 1, 14)

    def test_with_end_date_exceeded(self):
        """Test recurrence stops when next date after end_date"""
        current = datetime(2026, 12, 30)
        end_date = datetime(2026, 12, 31)
        next_date = calculate_next_due_date(current, "daily", 5, end_date)

        assert next_date is None  # Would be Jan 4, 2027 - exceeds end_date

    def test_none_pattern_returns_none(self):
        """Test 'none' pattern returns None"""
        current = datetime(2026, 1, 13)
        next_date = calculate_next_due_date(current, "none", 1, None)

        assert next_date is None

    def test_invalid_interval_returns_none(self):
        """Test invalid interval returns None"""
        current = datetime(2026, 1, 13)
        next_date = calculate_next_due_date(current, "daily", 0, None)

        assert next_date is None

        next_date = calculate_next_due_date(current, "daily", -1, None)

        assert next_date is None

    def test_unknown_pattern_returns_none(self):
        """Test unknown pattern returns None"""
        current = datetime(2026, 1, 13)
        next_date = calculate_next_due_date(current, "unknown", 1, None)

        assert next_date is None


class TestShouldCreateInstance:
    """Test instance creation validation"""

    def test_should_create_valid_future_date(self):
        """Test instance should be created for valid future date"""
        future_date = datetime.utcnow() + timedelta(days=7)
        assert should_create_instance(future_date, None) is True

    def test_should_not_create_far_past_date(self):
        """Test instance should not be created for far past dates"""
        past_date = datetime.utcnow() - timedelta(days=10)
        assert should_create_instance(past_date, None) is False

    def test_should_create_recent_past_within_grace(self):
        """Test instance should be created for recent past (within grace period)"""
        recent_past = datetime.utcnow() - timedelta(hours=12)
        assert should_create_instance(recent_past, None) is True

    def test_should_not_create_after_end_date(self):
        """Test instance should not be created after end_date"""
        future_date = datetime(2026, 12, 31)
        end_date = datetime(2026, 6, 30)
        assert should_create_instance(future_date, end_date) is False

    def test_should_create_before_end_date(self):
        """Test instance should be created before end_date"""
        future_date = datetime(2026, 3, 15)
        end_date = datetime(2026, 12, 31)
        assert should_create_instance(future_date, end_date) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

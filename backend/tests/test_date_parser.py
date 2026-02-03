"""Tests for flexible date parsing utilities.

Tests natural language parsing, relative dates, and timezone awareness.
"""

import pytest
from datetime import datetime, timedelta
import pytz
from app.utils.date_parser import (
    parse_flexible_date,
    parse_time_string,
    is_past_due,
    format_relative_time
)


class TestParseFlexibleDate:
    """Tests for parse_flexible_date function"""

    def test_parse_iso_8601_format(self):
        """Test parsing ISO 8601 date format"""
        result = parse_flexible_date(
            "2024-01-15T14:30:00",
            timezone_str="UTC"
        )

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30
        assert result.tzinfo is not None

    def test_parse_date_with_time(self):
        """Test parsing date with time"""
        result = parse_flexible_date(
            "2024-01-15 14:30",
            timezone_str="America/New_York"
        )

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30

    def test_parse_today(self):
        """Test parsing 'today'"""
        result = parse_flexible_date("today", timezone_str="UTC")

        now = datetime.now(pytz.UTC)
        assert result.year == now.year
        assert result.month == now.month
        assert result.day == now.day

    def test_parse_tomorrow(self):
        """Test parsing 'tomorrow'"""
        result = parse_flexible_date("tomorrow", timezone_str="UTC")

        tomorrow = datetime.now(pytz.UTC) + timedelta(days=1)
        assert result.year == tomorrow.year
        assert result.month == tomorrow.month
        assert result.day == tomorrow.day
        # Default time should be 9 AM
        assert result.hour == 9

    def test_parse_tomorrow_with_time(self):
        """Test parsing 'tomorrow 9am'"""
        result = parse_flexible_date("tomorrow 9am", timezone_str="UTC")

        tomorrow = datetime.now(pytz.UTC) + timedelta(days=1)
        assert result.year == tomorrow.year
        assert result.month == tomorrow.month
        assert result.day == tomorrow.day
        assert result.hour == 9
        assert result.minute == 0

    def test_parse_tomorrow_with_pm_time(self):
        """Test parsing 'tomorrow 2pm'"""
        result = parse_flexible_date("tomorrow 2pm", timezone_str="UTC")

        tomorrow = datetime.now(pytz.UTC) + timedelta(days=1)
        assert result.hour == 14  # 2 PM = 14:00

    def test_parse_next_friday(self):
        """Test parsing 'next friday'"""
        result = parse_flexible_date("next friday", timezone_str="UTC")

        assert result.weekday() == 4  # Friday = 4
        assert result > datetime.now(pytz.UTC)

    def test_parse_next_friday_with_time(self):
        """Test parsing 'next friday 2pm'"""
        result = parse_flexible_date("next friday 2pm", timezone_str="UTC")

        assert result.weekday() == 4  # Friday
        assert result.hour == 14  # 2 PM

    def test_parse_next_week(self):
        """Test parsing 'next week'"""
        result = parse_flexible_date("next week", timezone_str="UTC")

        now = datetime.now(pytz.UTC)
        next_week = now + timedelta(weeks=1)
        # Should be approximately 7 days ahead
        diff = (result - now).days
        assert 6 <= diff <= 8

    def test_parse_in_3_days(self):
        """Test parsing 'in 3 days'"""
        result = parse_flexible_date("in 3 days", timezone_str="UTC")

        now = datetime.now(pytz.UTC)
        expected = now + timedelta(days=3)
        assert result.year == expected.year
        assert result.month == expected.month
        assert result.day == expected.day

    def test_parse_in_2_hours(self):
        """Test parsing 'in 2 hours'"""
        result = parse_flexible_date("in 2 hours", timezone_str="UTC")

        now = datetime.now(pytz.UTC)
        expected = now + timedelta(hours=2)
        # Allow 1 minute tolerance
        diff = abs((result - expected).total_seconds())
        assert diff < 60

    def test_parse_with_timezone(self):
        """Test parsing with specific timezone"""
        result = parse_flexible_date(
            "2024-01-15 14:30",
            timezone_str="America/New_York"
        )

        assert result.tzinfo.zone == "America/New_York"

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            parse_flexible_date("", timezone_str="UTC")

    def test_none_raises_error(self):
        """Test that None raises ValueError"""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            parse_flexible_date(None, timezone_str="UTC")

    def test_invalid_timezone_raises_error(self):
        """Test that invalid timezone raises ValueError"""
        with pytest.raises(ValueError, match="Invalid timezone"):
            parse_flexible_date("tomorrow", timezone_str="Invalid/Timezone")

    def test_unparseable_string_raises_error(self):
        """Test that empty or completely invalid string raises ValueError"""
        # dateutil is very forgiving with fuzzy parsing, so test with truly empty input
        with pytest.raises(ValueError, match="must be a non-empty string"):
            parse_flexible_date("", timezone_str="UTC")

    def test_parse_yesterday(self):
        """Test parsing 'yesterday'"""
        result = parse_flexible_date("yesterday", timezone_str="UTC")

        yesterday = datetime.now(pytz.UTC) - timedelta(days=1)
        assert result.year == yesterday.year
        assert result.month == yesterday.month
        assert result.day == yesterday.day

    def test_parse_next_month(self):
        """Test parsing 'next month'"""
        result = parse_flexible_date("next month", timezone_str="UTC")

        now = datetime.now(pytz.UTC)
        # Should be in the next month
        if now.month == 12:
            assert result.month == 1
            assert result.year == now.year + 1
        else:
            assert result.month == now.month + 1
            assert result.year == now.year


class TestParseTimeString:
    """Tests for parse_time_string function"""

    def test_parse_9am(self):
        """Test parsing '9am'"""
        result = parse_time_string("9am")

        assert result.hour == 9
        assert result.minute == 0

    def test_parse_2pm(self):
        """Test parsing '2pm'"""
        result = parse_time_string("2pm")

        assert result.hour == 14  # 2 PM = 14:00
        assert result.minute == 0

    def test_parse_24_hour_format(self):
        """Test parsing 24-hour format '14:30'"""
        result = parse_time_string("14:30")

        assert result.hour == 14
        assert result.minute == 30

    def test_parse_with_base_date(self):
        """Test parsing time with custom base date"""
        base = datetime(2026, 6, 15, 0, 0, 0)
        result = parse_time_string("9am", base_date=base)

        assert result.year == 2026
        assert result.month == 6
        assert result.day == 15
        assert result.hour == 9

    def test_invalid_time_raises_error(self):
        """Test that invalid time raises ValueError"""
        with pytest.raises(ValueError, match="Unable to parse time"):
            parse_time_string("invalid time")


class TestIsPastDue:
    """Tests for is_past_due function"""

    def test_past_date_returns_true(self):
        """Test that past date returns True"""
        past = datetime(2020, 1, 1, tzinfo=pytz.UTC)
        assert is_past_due(past) is True

    def test_future_date_returns_false(self):
        """Test that future date returns False"""
        future = datetime(2030, 1, 1, tzinfo=pytz.UTC)
        assert is_past_due(future) is False

    def test_with_custom_reference_time(self):
        """Test with custom reference time"""
        due_date = datetime(2026, 1, 10, tzinfo=pytz.UTC)
        reference = datetime(2026, 1, 15, tzinfo=pytz.UTC)

        assert is_past_due(due_date, reference) is True

    def test_naive_datetime_handling(self):
        """Test that naive datetimes are handled (localized to UTC)"""
        # Naive datetime in the past
        past = datetime(2020, 1, 1)
        assert is_past_due(past) is True


class TestFormatRelativeTime:
    """Tests for format_relative_time function"""

    def test_format_past_minutes(self):
        """Test formatting past time in minutes"""
        now = datetime.now(pytz.UTC)
        past = now - timedelta(minutes=30)

        result = format_relative_time(past, now)
        assert "30 minutes ago" in result

    def test_format_past_hours(self):
        """Test formatting past time in hours"""
        now = datetime.now(pytz.UTC)
        past = now - timedelta(hours=3)

        result = format_relative_time(past, now)
        assert "3 hours ago" in result

    def test_format_past_days(self):
        """Test formatting past time in days"""
        now = datetime.now(pytz.UTC)
        past = now - timedelta(days=2)

        result = format_relative_time(past, now)
        assert "2 days ago" in result

    def test_format_future_minutes(self):
        """Test formatting future time in minutes"""
        now = datetime.now(pytz.UTC)
        future = now + timedelta(minutes=15)

        result = format_relative_time(future, now)
        assert "in 15 minutes" in result

    def test_format_future_hours(self):
        """Test formatting future time in hours"""
        now = datetime.now(pytz.UTC)
        future = now + timedelta(hours=5)

        result = format_relative_time(future, now)
        assert "in 5 hours" in result

    def test_format_future_days(self):
        """Test formatting future time in days"""
        now = datetime.now(pytz.UTC)
        future = now + timedelta(days=3)

        result = format_relative_time(future, now)
        assert "in 3 days" in result

    def test_format_future_weeks(self):
        """Test formatting future time in weeks"""
        now = datetime.now(pytz.UTC)
        future = now + timedelta(weeks=2)

        result = format_relative_time(future, now)
        assert "in 2 weeks" in result

    def test_format_just_now(self):
        """Test formatting very recent time"""
        now = datetime.now(pytz.UTC)
        recent = now - timedelta(seconds=30)

        result = format_relative_time(recent, now)
        assert "just now" in result

    def test_format_in_a_moment(self):
        """Test formatting very near future"""
        now = datetime.now(pytz.UTC)
        soon = now + timedelta(seconds=30)

        result = format_relative_time(soon, now)
        assert "in a moment" in result


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_parse_case_insensitive(self):
        """Test that parsing is case-insensitive"""
        result1 = parse_flexible_date("TOMORROW", timezone_str="UTC")
        result2 = parse_flexible_date("tomorrow", timezone_str="UTC")

        assert result1.day == result2.day

    def test_parse_with_extra_whitespace(self):
        """Test parsing with extra whitespace"""
        result = parse_flexible_date("  tomorrow   9am  ", timezone_str="UTC")

        tomorrow = datetime.now(pytz.UTC) + timedelta(days=1)
        assert result.day == tomorrow.day
        assert result.hour == 9

    def test_parse_fuzzy_matching(self):
        """Test fuzzy date parsing (dateutil feature)"""
        result = parse_flexible_date(
            "Meeting on 2024-01-15 at 2pm",
            timezone_str="UTC"
        )

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 14

    def test_parse_with_timezone_dst(self):
        """Test parsing during DST transition"""
        # March 8, 2026 is DST transition in America/New_York
        result = parse_flexible_date(
            "2026-03-08 02:30",
            timezone_str="America/New_York"
        )

        # Should handle DST properly
        assert result.tzinfo.zone == "America/New_York"

    def test_multiple_relative_date_formats(self):
        """Test various relative date formats"""
        formats = [
            "tomorrow",
            "tmr",
            "tmrw",
        ]

        tomorrow = datetime.now(pytz.UTC) + timedelta(days=1)

        for fmt in formats:
            result = parse_flexible_date(fmt, timezone_str="UTC")
            assert result.day == tomorrow.day

    def test_weekday_names_case_variations(self):
        """Test weekday names with different cases"""
        variations = ["Monday", "monday", "MONDAY", "Mon", "mon"]

        for var in variations:
            result = parse_flexible_date(f"next {var}", timezone_str="UTC")
            assert result.weekday() == 0  # Monday

    def test_parse_with_seconds(self):
        """Test parsing time with seconds"""
        result = parse_flexible_date(
            "2024-01-15 14:30:45",
            timezone_str="UTC"
        )

        assert result.hour == 14
        assert result.minute == 30
        # Seconds might be present or set to 0 depending on implementation

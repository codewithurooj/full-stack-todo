"""Tests for timezone conversion utilities.

Tests timezone conversions, DST handling, and edge cases.
"""

import pytest
from datetime import datetime
import pytz
from app.utils.timezone import (
    convert_to_utc,
    convert_from_utc,
    get_user_timezone,
    is_valid_timezone,
    get_current_utc
)


class TestConvertToUTC:
    """Tests for convert_to_utc function"""

    def test_convert_naive_datetime_to_utc(self):
        """Test converting naive datetime to UTC"""
        # 9 AM EST (Eastern Standard Time)
        local_dt = datetime(2026, 2, 15, 9, 0)
        utc_dt = convert_to_utc(local_dt, "America/New_York")

        # EST is UTC-5, so 9 AM EST = 2 PM UTC
        assert utc_dt.hour == 14
        assert utc_dt.tzinfo == pytz.UTC

    def test_convert_aware_datetime_to_utc(self):
        """Test converting timezone-aware datetime to UTC"""
        est = pytz.timezone("America/New_York")
        local_dt = est.localize(datetime(2026, 2, 15, 9, 0))
        utc_dt = convert_to_utc(local_dt, "America/New_York")

        assert utc_dt.hour == 14
        assert utc_dt.tzinfo == pytz.UTC

    def test_convert_pst_to_utc(self):
        """Test converting PST to UTC"""
        # 2 PM PST (Pacific Standard Time)
        local_dt = datetime(2026, 2, 15, 14, 0)
        utc_dt = convert_to_utc(local_dt, "America/Los_Angeles")

        # PST is UTC-8, so 2 PM PST = 10 PM UTC
        assert utc_dt.hour == 22
        assert utc_dt.tzinfo == pytz.UTC

    def test_convert_utc_to_utc(self):
        """Test converting UTC to UTC (should remain unchanged)"""
        local_dt = datetime(2026, 2, 15, 14, 0)
        utc_dt = convert_to_utc(local_dt, "UTC")

        assert utc_dt.hour == 14
        assert utc_dt.tzinfo == pytz.UTC

    def test_invalid_timezone_raises_error(self):
        """Test that invalid timezone raises ValueError"""
        local_dt = datetime(2026, 2, 15, 9, 0)

        with pytest.raises(ValueError, match="Invalid timezone"):
            convert_to_utc(local_dt, "Invalid/Timezone")

    def test_dst_transition_spring_forward(self):
        """Test DST transition - spring forward (2 AM -> 3 AM)"""
        # In 2026, DST starts March 8 at 2 AM
        # 1:30 AM before transition (EST = UTC-5)
        local_dt = datetime(2026, 3, 8, 1, 30)
        utc_dt = convert_to_utc(local_dt, "America/New_York")

        # Should be 6:30 AM UTC
        assert utc_dt.hour == 6
        assert utc_dt.minute == 30

    def test_dst_transition_fall_back(self):
        """Test DST transition - fall back (2 AM -> 1 AM)"""
        # In 2026, DST ends November 1 at 2 AM
        # 1:30 AM during DST (EDT = UTC-4)
        local_dt = datetime(2026, 11, 1, 1, 30)
        utc_dt = convert_to_utc(local_dt, "America/New_York")

        # pytz handles ambiguous times - should pick first occurrence (EDT)
        assert utc_dt.tzinfo == pytz.UTC


class TestConvertFromUTC:
    """Tests for convert_from_utc function"""

    def test_convert_utc_to_est(self):
        """Test converting UTC to EST"""
        utc_dt = datetime(2026, 2, 15, 14, 0, tzinfo=pytz.UTC)
        local_dt = convert_from_utc(utc_dt, "America/New_York")

        # 2 PM UTC = 9 AM EST (UTC-5)
        assert local_dt.hour == 9
        assert local_dt.tzinfo.zone == "America/New_York"

    def test_convert_utc_to_pst(self):
        """Test converting UTC to PST"""
        utc_dt = datetime(2026, 2, 15, 22, 0, tzinfo=pytz.UTC)
        local_dt = convert_from_utc(utc_dt, "America/Los_Angeles")

        # 10 PM UTC = 2 PM PST (UTC-8)
        assert local_dt.hour == 14
        assert local_dt.tzinfo.zone == "America/Los_Angeles"

    def test_convert_utc_to_tokyo(self):
        """Test converting UTC to JST (Japan Standard Time)"""
        utc_dt = datetime(2026, 2, 15, 14, 0, tzinfo=pytz.UTC)
        local_dt = convert_from_utc(utc_dt, "Asia/Tokyo")

        # 2 PM UTC = 11 PM JST (UTC+9)
        assert local_dt.hour == 23
        assert local_dt.tzinfo.zone == "Asia/Tokyo"

    def test_naive_datetime_raises_error(self):
        """Test that naive datetime raises ValueError"""
        naive_dt = datetime(2026, 2, 15, 14, 0)

        with pytest.raises(ValueError, match="must be timezone-aware"):
            convert_from_utc(naive_dt, "America/New_York")

    def test_invalid_timezone_raises_error(self):
        """Test that invalid timezone raises ValueError"""
        utc_dt = datetime(2026, 2, 15, 14, 0, tzinfo=pytz.UTC)

        with pytest.raises(ValueError, match="Invalid timezone"):
            convert_from_utc(utc_dt, "Invalid/Timezone")


class TestGetUserTimezone:
    """Tests for get_user_timezone function"""

    def test_valid_timezone_returns_unchanged(self):
        """Test that valid timezone is returned unchanged"""
        assert get_user_timezone("America/New_York") == "America/New_York"
        assert get_user_timezone("Europe/London") == "Europe/London"
        assert get_user_timezone("Asia/Tokyo") == "Asia/Tokyo"

    def test_none_returns_utc(self):
        """Test that None returns UTC"""
        assert get_user_timezone(None) == "UTC"

    def test_empty_string_returns_utc(self):
        """Test that empty string returns UTC"""
        assert get_user_timezone("") == "UTC"

    def test_invalid_timezone_returns_utc(self):
        """Test that invalid timezone returns UTC as fallback"""
        assert get_user_timezone("Invalid/Timezone") == "UTC"
        assert get_user_timezone("NotATimezone") == "UTC"


class TestIsValidTimezone:
    """Tests for is_valid_timezone function"""

    def test_valid_timezones(self):
        """Test that valid timezones return True"""
        assert is_valid_timezone("America/New_York") is True
        assert is_valid_timezone("Europe/London") is True
        assert is_valid_timezone("UTC") is True
        assert is_valid_timezone("Asia/Tokyo") is True

    def test_invalid_timezones(self):
        """Test that invalid timezones return False"""
        assert is_valid_timezone("Invalid/Timezone") is False
        assert is_valid_timezone("NotATimezone") is False
        assert is_valid_timezone("") is False


class TestGetCurrentUTC:
    """Tests for get_current_utc function"""

    def test_returns_utc_aware_datetime(self):
        """Test that function returns timezone-aware UTC datetime"""
        now = get_current_utc()

        assert now.tzinfo == pytz.UTC
        assert isinstance(now, datetime)

    def test_returns_current_time(self):
        """Test that returned time is approximately current"""
        before = datetime.now(pytz.UTC)
        now = get_current_utc()
        after = datetime.now(pytz.UTC)

        # Should be within 1 second
        assert before <= now <= after


class TestTimezoneEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_leap_year_date(self):
        """Test timezone conversion on leap year date"""
        # Feb 29, 2024 (leap year)
        local_dt = datetime(2024, 2, 29, 12, 0)
        utc_dt = convert_to_utc(local_dt, "America/New_York")

        assert utc_dt.day == 29
        assert utc_dt.month == 2

    def test_year_boundary(self):
        """Test timezone conversion across year boundary"""
        # 11 PM EST on Dec 31 = 4 AM UTC on Jan 1
        local_dt = datetime(2025, 12, 31, 23, 0)
        utc_dt = convert_to_utc(local_dt, "America/New_York")

        assert utc_dt.year == 2026
        assert utc_dt.month == 1
        assert utc_dt.day == 1
        assert utc_dt.hour == 4

    def test_round_trip_conversion(self):
        """Test that UTC -> Local -> UTC preserves time"""
        original_utc = datetime(2026, 2, 15, 14, 30, 0, tzinfo=pytz.UTC)

        # Convert to EST
        local_dt = convert_from_utc(original_utc, "America/New_York")

        # Convert back to UTC
        back_to_utc = convert_to_utc(local_dt, "America/New_York")

        # Should match original (allowing for microsecond differences)
        assert original_utc.replace(microsecond=0) == back_to_utc.replace(microsecond=0)

    def test_multiple_timezone_conversions(self):
        """Test converting through multiple timezones"""
        # Start with UTC
        utc_dt = datetime(2026, 2, 15, 12, 0, tzinfo=pytz.UTC)

        # UTC -> EST
        est_dt = convert_from_utc(utc_dt, "America/New_York")
        assert est_dt.hour == 7  # 12 PM UTC = 7 AM EST

        # EST -> PST (via UTC)
        utc_from_est = convert_to_utc(est_dt, "America/New_York")
        pst_dt = convert_from_utc(utc_from_est, "America/Los_Angeles")
        assert pst_dt.hour == 4  # 7 AM EST = 4 AM PST

        # Should preserve the original UTC time
        assert utc_from_est.replace(microsecond=0) == utc_dt.replace(microsecond=0)

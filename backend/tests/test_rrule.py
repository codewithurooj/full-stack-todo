"""Tests for recurrence pattern generation using rrule.

Tests daily, weekly, monthly patterns, next occurrence calculations,
and RRULE string handling.
"""

import pytest
from datetime import datetime, timedelta
import pytz
from app.utils.rrule import (
    generate_next_occurrence,
    generate_occurrences,
    parse_rrule_string,
    build_rrule_string,
    calculate_next_occurrence_from_rrule
)


class TestGenerateNextOccurrence:
    """Tests for generate_next_occurrence function"""

    def test_daily_pattern(self):
        """Test daily recurrence pattern"""
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)
        next_occ = generate_next_occurrence(
            pattern='daily',
            interval=1,
            start_date=start_date,
            timezone_str='UTC'
        )

        # Next occurrence should be tomorrow at same time
        expected = datetime(2026, 1, 10, 9, 0, tzinfo=pytz.UTC)
        assert next_occ.replace(microsecond=0) == expected.replace(microsecond=0)

    def test_daily_pattern_with_interval(self):
        """Test daily pattern with interval (every 2 days)"""
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)
        next_occ = generate_next_occurrence(
            pattern='daily',
            interval=2,
            start_date=start_date,
            timezone_str='UTC'
        )

        # Next occurrence should be 2 days later
        expected = datetime(2026, 1, 11, 9, 0, tzinfo=pytz.UTC)
        assert next_occ.replace(microsecond=0) == expected.replace(microsecond=0)

    def test_weekly_pattern(self):
        """Test weekly recurrence pattern"""
        # Jan 9, 2026 is Thursday
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)
        next_occ = generate_next_occurrence(
            pattern='weekly',
            interval=1,
            start_date=start_date,
            timezone_str='UTC'
        )

        # Next occurrence should be 1 week later (Jan 16)
        expected = datetime(2026, 1, 16, 9, 0, tzinfo=pytz.UTC)
        assert next_occ.replace(microsecond=0) == expected.replace(microsecond=0)

    def test_weekly_pattern_with_days(self):
        """Test weekly pattern with specific days"""
        # Jan 9, 2026 is Thursday
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)
        next_occ = generate_next_occurrence(
            pattern='weekly',
            interval=1,
            days=['Monday', 'Friday'],
            start_date=start_date,
            timezone_str='UTC'
        )

        # Next occurrence should be Friday Jan 10 (if start is before Friday)
        # or Monday Jan 12 (if start is on/after Friday)
        # Jan 9 is Thursday, so next Mon or Fri would be Jan 12 (Monday)
        assert next_occ.weekday() in [0, 4]  # Monday or Friday

    def test_monthly_pattern(self):
        """Test monthly recurrence pattern"""
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)
        next_occ = generate_next_occurrence(
            pattern='monthly',
            interval=1,
            start_date=start_date,
            timezone_str='UTC'
        )

        # Next occurrence should be Feb 9
        expected = datetime(2026, 2, 9, 9, 0, tzinfo=pytz.UTC)
        assert next_occ.replace(microsecond=0) == expected.replace(microsecond=0)

    def test_with_end_date(self):
        """Test pattern with end date constraint"""
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)
        end_date = datetime(2026, 1, 11, 9, 0, tzinfo=pytz.UTC)

        next_occ = generate_next_occurrence(
            pattern='daily',
            interval=1,
            start_date=start_date,
            end_date=end_date,
            timezone_str='UTC'
        )

        # Should generate next occurrence within end_date
        assert next_occ <= end_date

    def test_invalid_pattern_raises_error(self):
        """Test that invalid pattern raises ValueError"""
        with pytest.raises(ValueError, match="Invalid pattern"):
            generate_next_occurrence(
                pattern='invalid_pattern',
                start_date=datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)
            )

    def test_invalid_timezone_raises_error(self):
        """Test that invalid timezone raises ValueError"""
        with pytest.raises(ValueError, match="Invalid timezone"):
            generate_next_occurrence(
                pattern='daily',
                start_date=datetime(2026, 1, 9, 9, 0),
                timezone_str='Invalid/Timezone'
            )


class TestGenerateOccurrences:
    """Tests for generate_occurrences function"""

    def test_generate_multiple_daily_occurrences(self):
        """Test generating multiple daily occurrences"""
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)
        occurrences = generate_occurrences(
            pattern='daily',
            interval=1,
            start_date=start_date,
            max_count=5,
            timezone_str='UTC'
        )

        assert len(occurrences) == 5

        # Check each occurrence is 1 day apart
        for i in range(len(occurrences) - 1):
            diff = (occurrences[i + 1] - occurrences[i]).days
            assert diff == 1

    def test_generate_weekly_occurrences_with_days(self):
        """Test generating weekly occurrences on specific days"""
        # Jan 9, 2026 is Thursday
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)
        occurrences = generate_occurrences(
            pattern='weekly',
            interval=1,
            days=['Monday', 'Wednesday', 'Friday'],
            start_date=start_date,
            max_count=6,  # 2 weeks of Mon/Wed/Fri
            timezone_str='UTC'
        )

        # All occurrences should be Mon, Wed, or Fri
        for occ in occurrences:
            assert occ.weekday() in [0, 2, 4]  # Mon=0, Wed=2, Fri=4

    def test_generate_monthly_occurrences(self):
        """Test generating monthly occurrences"""
        start_date = datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)
        occurrences = generate_occurrences(
            pattern='monthly',
            interval=1,
            start_date=start_date,
            max_count=3,
            timezone_str='UTC'
        )

        assert len(occurrences) == 3

        # Check months increment
        assert occurrences[0].month == 1  # Jan
        assert occurrences[1].month == 2  # Feb
        assert occurrences[2].month == 3  # Mar

        # Day should remain 15
        for occ in occurrences:
            assert occ.day == 15

    def test_max_count_limit(self):
        """Test that max_count is limited to 365 for safety"""
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)
        occurrences = generate_occurrences(
            pattern='daily',
            interval=1,
            start_date=start_date,
            max_count=500,  # Request 500
            timezone_str='UTC'
        )

        # Should be capped at 365
        assert len(occurrences) <= 365

    def test_end_date_constraint(self):
        """Test that end_date limits generated occurrences"""
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)
        end_date = datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)

        occurrences = generate_occurrences(
            pattern='daily',
            interval=1,
            start_date=start_date,
            end_date=end_date,
            max_count=100,  # Request many, but end_date should limit
            timezone_str='UTC'
        )

        # All occurrences should be <= end_date
        for occ in occurrences:
            assert occ <= end_date

    def test_timezone_awareness(self):
        """Test that all occurrences are timezone-aware"""
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)
        occurrences = generate_occurrences(
            pattern='daily',
            interval=1,
            start_date=start_date,
            max_count=5,
            timezone_str='America/New_York'
        )

        # All occurrences should be timezone-aware
        for occ in occurrences:
            assert occ.tzinfo is not None


class TestParseRRuleString:
    """Tests for parse_rrule_string function"""

    def test_parse_daily_rrule(self):
        """Test parsing daily RRULE string"""
        rrule_str = "FREQ=DAILY;INTERVAL=1;COUNT=5"
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)

        occurrences = parse_rrule_string(rrule_str, start_date)

        assert len(occurrences) == 5
        # First occurrence should be start_date
        assert occurrences[0].replace(microsecond=0) == start_date.replace(microsecond=0)

    def test_parse_weekly_rrule_with_byday(self):
        """Test parsing weekly RRULE with BYDAY"""
        rrule_str = "FREQ=WEEKLY;BYDAY=MO,WE,FR"
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)

        occurrences = parse_rrule_string(rrule_str, start_date)

        # Should generate Mon/Wed/Fri occurrences
        weekdays = [occ.weekday() for occ in occurrences[:6]]
        for wd in weekdays:
            assert wd in [0, 2, 4]  # Mon, Wed, Fri

    def test_parse_monthly_rrule(self):
        """Test parsing monthly RRULE"""
        rrule_str = "FREQ=MONTHLY;INTERVAL=1;COUNT=3"
        start_date = datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)

        occurrences = parse_rrule_string(rrule_str, start_date)

        assert len(occurrences) == 3
        assert occurrences[0].month == 1
        assert occurrences[1].month == 2
        assert occurrences[2].month == 3

    def test_parse_rrule_with_until(self):
        """Test parsing RRULE with UNTIL constraint"""
        rrule_str = "FREQ=DAILY;UNTIL=20260115T090000Z"
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)

        occurrences = parse_rrule_string(rrule_str, start_date)

        # All occurrences should be before/on Jan 15
        end_date = datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)
        for occ in occurrences:
            assert occ <= end_date

    def test_invalid_rrule_raises_error(self):
        """Test that invalid RRULE raises ValueError"""
        invalid_rrule = "INVALID RRULE STRING"
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)

        with pytest.raises(ValueError, match="Failed to parse RRULE"):
            parse_rrule_string(invalid_rrule, start_date)


class TestBuildRRuleString:
    """Tests for build_rrule_string function"""

    def test_build_daily_rrule(self):
        """Test building daily RRULE string"""
        rrule = build_rrule_string('daily', interval=1, count=30)

        assert 'FREQ=DAILY' in rrule
        # INTERVAL=1 is the default and should be omitted
        assert 'COUNT=30' in rrule

    def test_build_weekly_rrule_with_days(self):
        """Test building weekly RRULE with specific days"""
        rrule = build_rrule_string(
            'weekly',
            interval=1,
            days=['Monday', 'Friday']
        )

        assert 'FREQ=WEEKLY' in rrule
        assert 'BYDAY=MO,FR' in rrule

    def test_build_monthly_rrule(self):
        """Test building monthly RRULE string"""
        rrule = build_rrule_string('monthly', interval=1, count=12)

        assert 'FREQ=MONTHLY' in rrule
        assert 'COUNT=12' in rrule

    def test_build_rrule_with_end_date(self):
        """Test building RRULE with end date"""
        end_date = datetime(2026, 12, 31, 23, 59, 59, tzinfo=pytz.UTC)
        rrule = build_rrule_string('daily', interval=1, end_date=end_date)

        assert 'FREQ=DAILY' in rrule
        assert 'UNTIL=' in rrule

    def test_interval_greater_than_one(self):
        """Test building RRULE with interval > 1"""
        rrule = build_rrule_string('daily', interval=3, count=10)

        assert 'INTERVAL=3' in rrule


class TestCalculateNextOccurrenceFromRRule:
    """Tests for calculate_next_occurrence_from_rrule function"""

    def test_calculate_next_daily_occurrence(self):
        """Test calculating next daily occurrence"""
        rrule_str = "FREQ=DAILY;INTERVAL=1"
        start_date = datetime(2026, 1, 1, 9, 0, tzinfo=pytz.UTC)
        after_date = datetime(2026, 1, 9, 12, 0, tzinfo=pytz.UTC)

        next_occ = calculate_next_occurrence_from_rrule(
            rrule_str,
            start_date,
            after_date
        )

        # Should be Jan 10 at 9 AM (next day after Jan 9 12 PM)
        expected = datetime(2026, 1, 10, 9, 0, tzinfo=pytz.UTC)
        assert next_occ.replace(microsecond=0) == expected.replace(microsecond=0)

    def test_calculate_next_weekly_occurrence(self):
        """Test calculating next weekly occurrence"""
        rrule_str = "FREQ=WEEKLY;BYDAY=MO,FR"
        start_date = datetime(2026, 1, 5, 9, 0, tzinfo=pytz.UTC)  # Monday
        after_date = datetime(2026, 1, 6, 12, 0, tzinfo=pytz.UTC)  # Tuesday

        next_occ = calculate_next_occurrence_from_rrule(
            rrule_str,
            start_date,
            after_date
        )

        # Should be Friday Jan 9
        assert next_occ.weekday() == 4  # Friday

    def test_no_more_occurrences_returns_none(self):
        """Test that None is returned when no more occurrences"""
        rrule_str = "FREQ=DAILY;COUNT=5"
        start_date = datetime(2026, 1, 1, 9, 0, tzinfo=pytz.UTC)
        # After all 5 occurrences
        after_date = datetime(2026, 1, 10, 9, 0, tzinfo=pytz.UTC)

        next_occ = calculate_next_occurrence_from_rrule(
            rrule_str,
            start_date,
            after_date
        )

        # No more occurrences after count=5
        assert next_occ is None

    def test_with_until_constraint(self):
        """Test next occurrence with UNTIL constraint"""
        rrule_str = "FREQ=DAILY;UNTIL=20260115T090000Z"
        start_date = datetime(2026, 1, 1, 9, 0, tzinfo=pytz.UTC)
        after_date = datetime(2026, 1, 14, 12, 0, tzinfo=pytz.UTC)

        next_occ = calculate_next_occurrence_from_rrule(
            rrule_str,
            start_date,
            after_date
        )

        # Should be Jan 15 (last occurrence)
        expected = datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)
        assert next_occ.replace(microsecond=0) == expected.replace(microsecond=0)


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_weekly_pattern_with_short_day_names(self):
        """Test weekly pattern with abbreviated day names"""
        start_date = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)
        occurrences = generate_occurrences(
            pattern='weekly',
            days=['Mon', 'Wed', 'Fri'],  # Abbreviated
            start_date=start_date,
            max_count=6,
            timezone_str='UTC'
        )

        # Should work with abbreviated names
        weekdays = [occ.weekday() for occ in occurrences]
        for wd in weekdays:
            assert wd in [0, 2, 4]

    def test_monthly_pattern_on_31st(self):
        """Test monthly pattern starting on 31st (edge case for months with fewer days)"""
        start_date = datetime(2026, 1, 31, 9, 0, tzinfo=pytz.UTC)
        occurrences = generate_occurrences(
            pattern='monthly',
            interval=1,
            start_date=start_date,
            max_count=3,
            timezone_str='UTC'
        )

        # Jan 31, skip Feb (no 31st), Mar 31
        # rrule skips months without the specified day number
        assert occurrences[0].day == 31
        # Next occurrence skips February, goes to March
        assert occurrences[1].month == 3

    def test_leap_year_february(self):
        """Test monthly pattern in leap year February"""
        start_date = datetime(2024, 2, 29, 9, 0, tzinfo=pytz.UTC)  # Leap year
        occurrences = generate_occurrences(
            pattern='monthly',
            interval=1,
            start_date=start_date,
            max_count=2,
            timezone_str='UTC'
        )

        assert occurrences[0].day == 29
        assert occurrences[0].month == 2

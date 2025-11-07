"""
Comprehensive tests for timezone utilities.

Tests UTC datetime handling and period calculations.
"""

import pytest
from datetime import datetime, timedelta, UTC

from app.timezone_utils import get_utc_now, get_utc_end_of_day, get_period_end


class TestGetUtcNow:
    """Tests for get_utc_now function."""

    def test_returns_utc_datetime(self):
        """Test that get_utc_now returns UTC datetime."""
        now = get_utc_now()
        assert now.tzinfo == UTC
        assert isinstance(now, datetime)

    def test_is_aware_datetime(self):
        """Test that returned datetime is timezone-aware."""
        now = get_utc_now()
        assert now.tzinfo is not None


class TestGetUtcEndOfDay:
    """Tests for get_utc_end_of_day function."""

    def test_end_of_today(self):
        """Test getting end of today."""
        end_of_day = get_utc_end_of_day(0)
        
        assert end_of_day.tzinfo == UTC
        assert end_of_day.hour == 23
        assert end_of_day.minute == 59
        assert end_of_day.second == 59

    def test_end_of_tomorrow(self):
        """Test getting end of tomorrow."""
        today_end = get_utc_end_of_day(0)
        tomorrow_end = get_utc_end_of_day(1)
        
        # Should be exactly 1 day apart
        diff = tomorrow_end - today_end
        assert diff.days == 1

    def test_end_of_day_30_days_future(self):
        """Test getting end of day 30 days in future."""
        today = get_utc_now().date()
        end_of_day_30 = get_utc_end_of_day(30)
        
        expected_date = today + timedelta(days=30)
        assert end_of_day_30.date() == expected_date
        assert end_of_day_30.hour == 23
        assert end_of_day_30.minute == 59
        assert end_of_day_30.second == 59

    def test_negative_days_from_now(self):
        """Test getting end of day in the past."""
        yesterday_end = get_utc_end_of_day(-1)
        today_end = get_utc_end_of_day(0)
        
        assert yesterday_end < today_end
        assert yesterday_end.hour == 23
        assert yesterday_end.minute == 59


class TestGetPeriodEnd:
    """Tests for get_period_end function."""

    def test_period_1_day(self):
        """Test 1 day period ends at end of today."""
        period_end = get_period_end(1)
        
        assert period_end.tzinfo == UTC
        assert period_end.hour == 23
        assert period_end.minute == 59
        assert period_end.second == 59
        
        # Should be end of today
        today_end = get_utc_end_of_day(0)
        assert period_end.date() == today_end.date()

    def test_period_30_days(self):
        """Test 30 day period calculation."""
        period_end = get_period_end(30)
        
        # Should be 29 days from today (30 days inclusive)
        expected_end = get_utc_end_of_day(29)
        assert period_end.date() == expected_end.date()
        assert period_end.hour == 23
        assert period_end.minute == 59

    def test_period_365_days(self):
        """Test 1 year period."""
        period_end = get_period_end(365)
        
        expected_end = get_utc_end_of_day(364)
        assert period_end.date() == expected_end.date()

    def test_period_zero_days_raises_error(self):
        """Test that 0 days raises ValueError."""
        with pytest.raises(ValueError, match="period_days must be positive"):
            get_period_end(0)

    def test_period_negative_days_raises_error(self):
        """Test that negative days raises ValueError."""
        with pytest.raises(ValueError, match="period_days must be positive"):
            get_period_end(-1)

    def test_period_large_negative_raises_error(self):
        """Test that large negative value raises ValueError."""
        with pytest.raises(ValueError, match="period_days must be positive"):
            get_period_end(-100)

    def test_period_2_days(self):
        """Test 2 day period for exact calculation."""
        period_end = get_period_end(2)
        
        # 2 days means access through end of tomorrow
        tomorrow_end = get_utc_end_of_day(1)
        assert period_end.date() == tomorrow_end.date()


class TestTimezoneEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_utc_consistency(self):
        """Test that all functions return UTC-aware datetimes."""
        functions = [
            get_utc_now(),
            get_utc_end_of_day(0),
            get_period_end(1),
        ]
        
        for dt in functions:
            assert dt.tzinfo == UTC, f"DateTime {dt} is not UTC-aware"

    def test_end_of_day_always_23_59_59(self):
        """Test that end of day is always 23:59:59."""
        for days in [0, 1, 7, 30, 365]:
            end_of_day = get_utc_end_of_day(days)
            assert end_of_day.hour == 23
            assert end_of_day.minute == 59
            assert end_of_day.second == 59

    def test_period_end_always_23_59_59(self):
        """Test that period end is always 23:59:59."""
        for period_days in [1, 7, 30, 90, 365]:
            period_end = get_period_end(period_days)
            assert period_end.hour == 23
            assert period_end.minute == 59
            assert period_end.second == 59

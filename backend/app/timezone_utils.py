"""
Timezone utilities for UTC datetime handling.

All dates are stored and handled in UTC for consistency across the application.
"""

from datetime import UTC, datetime, time, timedelta


def get_utc_now() -> datetime:
    """Get current time in UTC with timezone awareness."""
    return datetime.now(UTC)


def get_utc_end_of_day(days_from_now: int = 0) -> datetime:
    """
    Get end of day in UTC (23:59:59 UTC).

    Args:
        days_from_now: Number of days from today (0 = today, 1 = tomorrow, etc.)

    Returns:
        UTC datetime representing 23:59:59 UTC of the specified day
    """
    # Get current UTC date
    now_utc = get_utc_now()
    # Add days
    target_date_utc = now_utc.date() + timedelta(days=days_from_now)
    # Create end of day in UTC (23:59:59)
    end_of_day_utc = datetime.combine(target_date_utc, time(23, 59, 59), tzinfo=UTC)
    return end_of_day_utc


def get_period_end(period_days: int) -> datetime:
    """
    Calculate period end date at end of day in UTC.

    For example, if period_days=30 and today is Jan 1, returns 23:59:59 UTC on Jan 31.
    This gives the user access for the full duration of all requested days.

    Args:
        period_days: Number of days for the period

    Returns:
        UTC datetime representing end of period (23:59:59 UTC)
    """
    # period_days=1 means access for today (ends at 23:59:59 today)
    # period_days=30 means access for 30 days (ends at 23:59:59 on day 30)
    return get_utc_end_of_day(period_days - 1)

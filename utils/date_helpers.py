"""Date utility functions for Sales Academy."""

from datetime import datetime, date, timedelta


def current_training_week(cohort_start_date_str):
    """Calculate the current training week (1-6) from cohort start date."""
    if isinstance(cohort_start_date_str, str):
        start = datetime.strptime(cohort_start_date_str, "%Y-%m-%d").date()
    else:
        start = cohort_start_date_str
    today = date.today()
    days_elapsed = (today - start).days
    if days_elapsed < 0:
        return 0
    week = days_elapsed // 7 + 1
    return min(week, 6)


def days_in_program(cohort_start_date_str):
    """Calculate days since program started."""
    if isinstance(cohort_start_date_str, str):
        start = datetime.strptime(cohort_start_date_str, "%Y-%m-%d").date()
    else:
        start = cohort_start_date_str
    today = date.today()
    return max(0, (today - start).days)


def format_date(date_str):
    """Format ISO date string to readable format."""
    if not date_str:
        return "—"
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return d.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return date_str

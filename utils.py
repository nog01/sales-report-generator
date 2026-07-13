"""
utils.py

Small, general-purpose helper functions that are used by more than one
part of the project (formatting numbers, checking dates, and so on).
Keeping them here avoids repeating the same code in app.py and reports.py.
"""

from datetime import datetime


def format_currency(value):
    """Format a number as a currency string, e.g. 1234.5 -> '$1,234.50'."""
    try:
        return f"${value:,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def validate_date_range(start_date, end_date):
    """Return True if start_date is not after end_date, False otherwise."""
    if start_date and end_date and start_date > end_date:
        return False
    return True


def format_date_for_display(date_value):
    """
    Turn a date into a friendly string like 'Jan 05, 2026'.
    Accepts either a date object or a 'YYYY-MM-DD' string.
    """
    if isinstance(date_value, str):
        date_value = datetime.strptime(date_value, "%Y-%m-%d").date()
    return date_value.strftime("%b %d, %Y")

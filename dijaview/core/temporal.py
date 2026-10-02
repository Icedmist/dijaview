import re
from datetime import datetime, timedelta, time
from typing import Optional
from dijaview.core.models import TimeRange

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def parse_temporal_expression(query: str, reference_date: Optional[datetime] = None) -> Optional[TimeRange]:
    """
    Extracts temporal bounds from natural language queries like
    'last Tuesday', 'yesterday', '3 days ago', 'this morning'.
    """
    if not query:
        return None

    now = reference_date or datetime.now()
    lower_query = query.lower()

    # Pattern: 'today' or 'this morning'
    if "today" in lower_query or "this morning" in lower_query:
        start = datetime.combine(now.date(), time.min)
        end = now
        return TimeRange(start.timestamp(), end.timestamp(), "today")

    # Pattern: 'yesterday'
    if "yesterday" in lower_query:
        target_day = now.date() - timedelta(days=1)
        start = datetime.combine(target_day, time.min)
        end = datetime.combine(target_day, time.max)
        return TimeRange(start.timestamp(), end.timestamp(), "yesterday")

    # Pattern: 'N days ago'
    days_ago_match = re.search(r"(\d+)\s+days?\s+ago", lower_query)
    if days_ago_match:
        days = int(days_ago_match.group(1))
        target_day = now.date() - timedelta(days=days)
        start = datetime.combine(target_day, time.min)
        end = datetime.combine(target_day, time.max)
        return TimeRange(start.timestamp(), end.timestamp(), f"{days} days ago")

    # Pattern: 'N hours ago'
    hours_ago_match = re.search(r"(\d+)\s+hours?\s+ago", lower_query)
    if hours_ago_match:
        hours = int(hours_ago_match.group(1))
        start = now - timedelta(hours=hours, minutes=30)
        end = now
        return TimeRange(start.timestamp(), end.timestamp(), f"{hours} hours ago")

    # Pattern: 'last <weekday>' (e.g. 'last tuesday')
    last_weekday_match = re.search(r"last\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", lower_query)
    if last_weekday_match:
        day_name = last_weekday_match.group(1)
        target_weekday = WEEKDAYS[day_name]
        current_weekday = now.weekday()
        
        # Calculate days back
        days_back = (current_weekday - target_weekday) % 7
        if days_back == 0:
            days_back = 7  # 'last tuesday' on a tuesday means 7 days ago
        
        target_day = now.date() - timedelta(days=days_back)
        start = datetime.combine(target_day, time.min)
        end = datetime.combine(target_day, time.max)
        return TimeRange(start.timestamp(), end.timestamp(), f"last {day_name.capitalize()}")

    # Pattern: 'last week'
    if "last week" in lower_query:
        start = now - timedelta(days=now.weekday() + 7)
        start = datetime.combine(start.date(), time.min)
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        return TimeRange(start.timestamp(), end.timestamp(), "last week")

    return None

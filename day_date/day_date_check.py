import json
import re
from datetime import date

def enforce_day_limit(markdown: str, max_days: int) -> str:
    """
    Ensure markdown contains at most max_days day sections.
    If more days exist, truncate and add a note.
    """
    # Find all "## Day N:" patterns
    day_pattern = re.compile(r"^##\s+Day\s+(\d+):", re.MULTILINE)
    matches = list(day_pattern.finditer(markdown))
    
    if not matches:
        return markdown
    
    # Find the starting position of Day (max_days + 1) if it exists
    for match in matches:
        day_num = int(match.group(1))
        if day_num > max_days:
            # Truncate at the start of this day
            truncated = markdown[:match.start()].rstrip()
            # Add closing note
            truncated += f"\n\n---\n*Road trip limited to {max_days} days as requested.*"
            return truncated
    
    return markdown

def _parse_iso_date(value: str) -> date | None:
  """Parse ISO date string (YYYY-MM-DD) safely."""
  if not value:
    return None
  try:
    return date.fromisoformat(str(value))
  except ValueError:
    return None

def compute_road_trip_days(start_date: str, end_date: str, max_days: int = 30) -> tuple[int, int]:
  """
  Return (requested_days, planned_days).
  planned_days is capped at max_days and never less than 1.
  """
  start = _parse_iso_date(start_date)
  end = _parse_iso_date(end_date)

  if start and end and end > start:
    requested_days = (end - start).days
  else:
    requested_days = 7

  planned_days = max(1, min(requested_days, max_days))
  return requested_days, planned_days
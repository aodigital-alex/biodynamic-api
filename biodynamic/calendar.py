"""BiodynamicCalendar — public interface."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from biodynamic.core.day_type import BiodynamicDay, build_day


class BiodynamicCalendar:
    def __init__(self, timezone: str = "UTC"):
        self.timezone = timezone
        ZoneInfo(timezone)  # validate early

    def get_day(self, target: date | str) -> BiodynamicDay:
        return build_day(_parse_date(target), self.timezone)

    def get_now(self) -> BiodynamicDay:
        tz = ZoneInfo(self.timezone)
        today = datetime.now(tz=tz).date()
        return build_day(today, self.timezone)

    def get_range(self, start: date | str, end: date | str) -> list[BiodynamicDay]:
        s = _parse_date(start)
        e = _parse_date(end)
        if (e - s).days > 366:
            raise ValueError("Range cannot exceed 366 days")
        results = []
        current = s
        while current <= e:
            results.append(build_day(current, self.timezone))
            current += timedelta(days=1)
        return results

    def next_day_of_type(
        self,
        day_type: str,
        after: date | str | None = None,
        favorable_only: bool = False,
    ) -> BiodynamicDay:
        _validate_type(day_type)
        start = _parse_date(after) if after else self._today()
        current = start + timedelta(days=1)
        for _ in range(60):
            day = build_day(current, self.timezone)
            if day.day_type == day_type:
                if not favorable_only or day.favorable:
                    return day
            current += timedelta(days=1)
        raise RuntimeError(f"No {day_type} day found within 60 days")

    def filter_by_type(
        self, day_type: str, start: date | str, end: date | str
    ) -> list[BiodynamicDay]:
        _validate_type(day_type)
        return [d for d in self.get_range(start, end) if d.day_type == day_type]

    def best_days(
        self, day_type: str, start: date | str, end: date | str
    ) -> list[BiodynamicDay]:
        _validate_type(day_type)
        return [
            d for d in self.get_range(start, end)
            if d.day_type == day_type and d.favorable
        ]

    def _today(self) -> date:
        return datetime.now(tz=ZoneInfo(self.timezone)).date()


def _parse_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _validate_type(day_type: str) -> None:
    valid = {"fruit", "flower", "leaf", "root"}
    if day_type not in valid:
        raise ValueError(f"day_type must be one of {valid}, got {day_type!r}")

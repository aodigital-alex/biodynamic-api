"""Pydantic v2 response models."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class WarningSchema(BaseModel):
    type: str
    label: str
    starts_at: datetime
    ends_at: datetime
    severity: str


class BiodynamicDaySchema(BaseModel):
    date: date
    timezone: str
    day_type: str
    day_type_emoji: str
    element: str
    constellation: str
    constellation_entry: Optional[datetime]
    constellation_exit: Optional[datetime]
    moon_phase: str
    moon_illumination: float
    moon_ascending: bool
    favorable: bool
    warnings: list[WarningSchema]
    recommendation: str


class RangeSummary(BaseModel):
    fruit_days: int
    flower_days: int
    leaf_days: int
    root_days: int
    unfavorable_periods: int


class RangeResponse(BaseModel):
    start: date
    end: date
    timezone: str
    days: list[BiodynamicDaySchema]
    summary: RangeSummary


class AstronomicalEvent(BaseModel):
    type: str
    label: str
    datetime: datetime
    duration_hours: Optional[float] = None
    avoid_window_start: Optional[datetime] = None
    avoid_window_end: Optional[datetime] = None


class EventsResponse(BaseModel):
    events: list[AstronomicalEvent]


class HealthResponse(BaseModel):
    status: str
    version: str

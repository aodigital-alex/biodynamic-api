"""FastAPI route definitions."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from biodynamic.calendar import BiodynamicCalendar
from biodynamic.core.day_type import BiodynamicDay, Warning
from biodynamic.core.rhythms import (
    find_constellation_transitions,
    next_apogee,
    next_moon_phase,
    next_node_crossing,
    next_perigee,
    node_window,
    perigee_window,
)

from .schemas import (
    AstronomicalEvent,
    BiodynamicDaySchema,
    EventsResponse,
    HealthResponse,
    RangeResponse,
    RangeSummary,
    WarningSchema,
)

router = APIRouter(prefix="/api/v1/biodynamic", tags=["biodynamic"])


def _day_to_schema(day: BiodynamicDay) -> BiodynamicDaySchema:
    return BiodynamicDaySchema(
        date=day.date,
        timezone=day.timezone,
        day_type=day.day_type,
        day_type_emoji=day.day_type_emoji,
        element=day.element,
        constellation=day.constellation,
        constellation_entry=day.constellation_entry,
        constellation_exit=day.constellation_exit,
        moon_phase=day.moon_phase,
        moon_illumination=day.moon_illumination,
        moon_ascending=day.moon_ascending,
        favorable=day.favorable,
        warnings=[
            WarningSchema(
                type=w.type,
                label=w.label,
                starts_at=w.starts_at,
                ends_at=w.ends_at,
                severity=w.severity,
            )
            for w in day.warnings
        ],
        recommendation=day.recommendation,
    )


def _make_summary(days: list[BiodynamicDay]) -> RangeSummary:
    return RangeSummary(
        fruit_days=sum(1 for d in days if d.day_type == "fruit"),
        flower_days=sum(1 for d in days if d.day_type == "flower"),
        leaf_days=sum(1 for d in days if d.day_type == "leaf"),
        root_days=sum(1 for d in days if d.day_type == "root"),
        unfavorable_periods=sum(1 for d in days if not d.favorable),
    )


def _get_cal(tz: str) -> BiodynamicCalendar:
    try:
        return BiodynamicCalendar(timezone=tz)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid timezone: {tz!r}")


@router.get("/health", response_model=HealthResponse)
def health():
    from biodynamic import __version__
    return HealthResponse(status="ok", version=__version__)


@router.get("/today", response_model=BiodynamicDaySchema)
def today(timezone: str = Query("UTC")):
    cal = _get_cal(timezone)
    return _day_to_schema(cal.get_now())


@router.get("/day/{target_date}", response_model=BiodynamicDaySchema)
def day(target_date: date, timezone: str = Query("UTC")):
    cal = _get_cal(timezone)
    try:
        return _day_to_schema(cal.get_day(target_date))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/range", response_model=RangeResponse)
def date_range(
    start: date = Query(...),
    end: date = Query(...),
    timezone: str = Query("UTC"),
    type_filter: Optional[str] = Query(None),
    favorable_only: bool = Query(False),
):
    if (end - start).days > 366:
        raise HTTPException(status_code=400, detail="Range cannot exceed 366 days")
    if (end - start).days < 0:
        raise HTTPException(status_code=400, detail="end must be >= start")

    cal = _get_cal(timezone)
    try:
        days = cal.get_range(start, end)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if type_filter:
        days = [d for d in days if d.day_type == type_filter]
    if favorable_only:
        days = [d for d in days if d.favorable]

    return RangeResponse(
        start=start,
        end=end,
        timezone=timezone,
        days=[_day_to_schema(d) for d in days],
        summary=_make_summary(days),
    )


@router.get("/week", response_model=RangeResponse)
def week(timezone: str = Query("UTC"), from_date: Optional[date] = Query(None)):
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(timezone)
    ref = from_date or datetime.now(tz=tz).date()
    # Monday of that week
    monday = ref - timedelta(days=ref.weekday())
    sunday = monday + timedelta(days=6)
    cal = _get_cal(timezone)
    days = cal.get_range(monday, sunday)
    return RangeResponse(
        start=monday,
        end=sunday,
        timezone=timezone,
        days=[_day_to_schema(d) for d in days],
        summary=_make_summary(days),
    )


@router.get("/month", response_model=RangeResponse)
def month(
    timezone: str = Query("UTC"),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
):
    from zoneinfo import ZoneInfo
    import calendar as cal_mod

    tz = ZoneInfo(timezone)
    now = datetime.now(tz=tz)
    y = year or now.year
    m = month or now.month
    _, last_day = cal_mod.monthrange(y, m)
    start = date(y, m, 1)
    end = date(y, m, last_day)
    cal = _get_cal(timezone)
    days = cal.get_range(start, end)
    return RangeResponse(
        start=start,
        end=end,
        timezone=timezone,
        days=[_day_to_schema(d) for d in days],
        summary=_make_summary(days),
    )


@router.get("/year", response_model=RangeResponse)
def year(timezone: str = Query("UTC"), year: Optional[int] = Query(None)):
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(timezone)
    y = year or datetime.now(tz=tz).year
    start = date(y, 1, 1)
    end = date(y, 12, 31)
    cal = _get_cal(timezone)
    days = cal.get_range(start, end)
    return RangeResponse(
        start=start,
        end=end,
        timezone=timezone,
        days=[_day_to_schema(d) for d in days],
        summary=_make_summary(days),
    )


@router.get("/next/{day_type}", response_model=BiodynamicDaySchema)
def next_day(
    day_type: str,
    after: Optional[date] = Query(None),
    timezone: str = Query("UTC"),
    favorable_only: bool = Query(False),
):
    valid_types = {"fruit", "flower", "leaf", "root", "ascending", "descending"}
    if day_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"type must be one of {valid_types}")

    cal = _get_cal(timezone)
    try:
        if day_type in {"ascending", "descending"}:
            # Search by moon direction
            from datetime import timedelta
            from biodynamic.core.day_type import build_day

            ref = after or datetime.now(tz=__import__("zoneinfo").ZoneInfo(timezone)).date()
            current = ref + timedelta(days=1)
            for _ in range(60):
                d = build_day(current, timezone)
                if (day_type == "ascending") == d.moon_ascending:
                    if not favorable_only or d.favorable:
                        return _day_to_schema(d)
                current += timedelta(days=1)
            raise HTTPException(status_code=404, detail="Not found within 60 days")
        else:
            return _day_to_schema(cal.next_day_of_type(day_type, after=after, favorable_only=favorable_only))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events", response_model=EventsResponse)
def events(
    start: date = Query(...),
    end: date = Query(...),
    timezone: str = Query("UTC"),
):
    if (end - start).days > 366:
        raise HTTPException(status_code=400, detail="Range cannot exceed 366 days")

    from zoneinfo import ZoneInfo

    tz = ZoneInfo(timezone)
    start_utc = datetime(start.year, start.month, start.day, tzinfo=timezone.utc if timezone == "UTC" else tz).astimezone(timezone.utc)
    end_utc = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=tz).astimezone(datetime.timezone.utc)

    result: list[AstronomicalEvent] = []

    # Moon phases
    for phase_name, phase_label in [
        ("new", "New Moon"),
        ("first_quarter", "First Quarter"),
        ("full", "Full Moon"),
        ("last_quarter", "Last Quarter"),
    ]:
        t = start_utc
        while t < end_utc:
            try:
                phase_dt = next_moon_phase(t, phase_name)
                if phase_dt > end_utc:
                    break
                result.append(AstronomicalEvent(
                    type=phase_name,
                    label=phase_label,
                    datetime=phase_dt,
                ))
                t = phase_dt + timedelta(days=25)
            except Exception:
                break

    # Perigee / Apogee
    for finder, label, ev_type in [
        (next_perigee, "Lunar Perigee", "perigee"),
        (next_apogee, "Lunar Apogee", "apogee"),
    ]:
        t = start_utc
        while t < end_utc:
            try:
                evt_dt = finder(t)
                if evt_dt > end_utc:
                    break
                ws, we = perigee_window(evt_dt)
                result.append(AstronomicalEvent(
                    type=ev_type,
                    label=label,
                    datetime=evt_dt,
                    avoid_window_start=ws if ev_type == "perigee" else None,
                    avoid_window_end=we if ev_type == "perigee" else None,
                ))
                t = evt_dt + timedelta(days=12)
            except Exception:
                break

    # Nodes
    t = start_utc
    for _ in range(6):
        try:
            node_dt, node_type = next_node_crossing(t)
            if node_dt > end_utc:
                break
            ns, ne = node_window(node_dt)
            result.append(AstronomicalEvent(
                type="node",
                label=f"{'Ascending' if node_type == 'ascending' else 'Descending'} Node",
                datetime=node_dt,
                avoid_window_start=ns,
                avoid_window_end=ne,
            ))
            t = node_dt + timedelta(hours=3)
        except Exception:
            break

    result.sort(key=lambda e: e.datetime)
    return EventsResponse(events=result)

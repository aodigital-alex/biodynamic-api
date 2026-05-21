"""BiodynamicDay aggregation — combines all rhythms into a single day record."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from biodynamic.core.moon import (
    moon_ascending,
    moon_constellation,
    moon_illumination,
    moon_phase_name,
)
from biodynamic.core.rhythms import (
    find_constellation_transitions,
    next_apogee,
    next_moon_phase,
    next_node_crossing,
    next_perigee,
    node_window,
    perigee_window,
)
from biodynamic.core.zodiac import (
    DAY_TYPE_EMOJI,
    ELEMENT,
    day_type_for_constellation,
)


@dataclass
class Warning:
    type: str
    label: str
    starts_at: datetime
    ends_at: datetime
    severity: str  # "avoid" | "caution"


@dataclass
class BiodynamicDay:
    date: date
    timezone: str

    day_type: str
    day_type_emoji: str
    element: str

    constellation: str
    constellation_entry: datetime | None
    constellation_exit: datetime | None

    moon_phase: str
    moon_illumination: float

    moon_ascending: bool

    warnings: list[Warning]
    favorable: bool
    recommendation: str


def _dominant_constellation(start: datetime, end: datetime) -> tuple[str, datetime | None, datetime | None]:
    """
    Return the constellation with the longest overlap in [start, end],
    plus entry/exit datetimes for that dominant constellation window.
    """
    transitions = find_constellation_transitions(start, end)

    segments: list[tuple[datetime, datetime, str]] = []
    seg_start = start
    seg_const = moon_constellation(start)

    for moment, from_c, to_c in transitions:
        segments.append((seg_start, moment, from_c))
        seg_start = moment
        seg_const = to_c
    segments.append((seg_start, end, seg_const))

    best = max(segments, key=lambda s: (s[1] - s[0]).total_seconds())
    dom_const = best[2]

    # Find entry: first moment dom_const appears
    entry = next((s[0] for s in segments if s[2] == dom_const), None)
    # Find exit: end of last continuous run
    exit_dt = None
    for s in reversed(segments):
        if s[2] == dom_const:
            exit_dt = s[1]
            break

    return dom_const, entry, exit_dt


def _collect_warnings(day_start: datetime, day_end: datetime) -> list[Warning]:
    warnings: list[Warning] = []
    search_from = day_start - timedelta(days=3)

    # Perigee
    try:
        peri = next_perigee(search_from)
        ws, we = perigee_window(peri)
        if ws < day_end and we > day_start:
            overlap_start = max(ws, day_start)
            overlap_end = min(we, day_end)
            warnings.append(Warning(
                type="perigee",
                label="Lunar Perigee",
                starts_at=overlap_start,
                ends_at=overlap_end,
                severity="caution",
            ))
    except Exception:
        pass

    # Node crossings
    t = search_from
    for _ in range(4):
        try:
            node_dt, node_type = next_node_crossing(t)
            ns, ne = node_window(node_dt)
            if ns < day_end and ne > day_start:
                overlap_start = max(ns, day_start)
                overlap_end = min(ne, day_end)
                warnings.append(Warning(
                    type="node",
                    label=f"{'Ascending' if node_type == 'ascending' else 'Descending'} Node",
                    starts_at=overlap_start,
                    ends_at=overlap_end,
                    severity="avoid",
                ))
            t = node_dt + timedelta(hours=3)
        except Exception:
            break

    return warnings


def build_day(target_date: date, tz_name: str = "UTC") -> BiodynamicDay:
    tz = ZoneInfo(tz_name)

    day_start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=tz)
    day_end = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, tzinfo=tz)

    # Convert to UTC for astronomy calculations
    day_start_utc = day_start.astimezone(timezone.utc)
    day_end_utc = day_end.astimezone(timezone.utc)
    noon_utc = day_start_utc + timedelta(hours=12)

    constellation, entry, exit_dt = _dominant_constellation(day_start_utc, day_end_utc)
    element = ELEMENT[constellation]
    day_type = day_type_for_constellation(constellation)
    emoji = DAY_TYPE_EMOJI[day_type]

    phase = moon_phase_name(noon_utc)
    illum = moon_illumination(noon_utc)
    ascending = moon_ascending(noon_utc)

    warnings = _collect_warnings(day_start_utc, day_end_utc)
    favorable = len(warnings) == 0

    recommendation = _build_recommendation(day_type, constellation, ascending, favorable, warnings)

    return BiodynamicDay(
        date=target_date,
        timezone=tz_name,
        day_type=day_type,
        day_type_emoji=emoji,
        element=element,
        constellation=constellation,
        constellation_entry=entry,
        constellation_exit=exit_dt,
        moon_phase=phase,
        moon_illumination=round(illum, 3),
        moon_ascending=ascending,
        warnings=warnings,
        favorable=favorable,
        recommendation=recommendation,
    )


def _build_recommendation(
    day_type: str,
    constellation: str,
    ascending: bool,
    favorable: bool,
    warnings: list[Warning],
) -> str:
    type_labels = {
        "fruit": "fruit and seed crops",
        "root": "root vegetables and soil work",
        "flower": "flowering plants and aromatics",
        "leaf": "leafy greens and water-loving plants",
    }
    direction = "ascending" if ascending else "descending"
    action = "harvesting and grafting" if ascending else "planting and soil work"

    if favorable:
        return (
            f"Good day for {type_labels[day_type]}. "
            f"Moon {direction} in {constellation.capitalize()} — favours {action}."
        )
    else:
        warning_labels = ", ".join(w.label for w in warnings)
        return (
            f"Use caution: {warning_labels}. "
            f"Day type is {day_type} ({constellation.capitalize()}), "
            f"moon {direction}."
        )

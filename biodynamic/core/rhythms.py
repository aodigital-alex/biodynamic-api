"""Perigee/apogee, lunar nodes, and constellation transition moments."""

from datetime import datetime, timedelta, timezone

import astronomy

from biodynamic.core.moon import _to_astro_time, moon_constellation
from biodynamic.core.zodiac import constellation_from_tropical, tropical_to_sidereal


def _astro_time_to_dt(t: astronomy.Time) -> datetime:
    jd = t.tt
    unix = (jd - 2440587.5) * 86400.0
    return datetime.fromtimestamp(unix, tz=timezone.utc)


# ---------------------------------------------------------------------------
# Perigee / Apogee
# ---------------------------------------------------------------------------

def next_perigee(after: datetime) -> datetime:
    t = _to_astro_time(after)
    result = astronomy.SearchLunarApsis(t)
    # kind 0 = perigee, 1 = apogee
    if result.kind == 0:
        return _astro_time_to_dt(result.time)
    result = astronomy.NextLunarApsis(result)
    return _astro_time_to_dt(result.time)


def next_apogee(after: datetime) -> datetime:
    t = _to_astro_time(after)
    result = astronomy.SearchLunarApsis(t)
    if result.kind == 1:
        return _astro_time_to_dt(result.time)
    result = astronomy.NextLunarApsis(result)
    return _astro_time_to_dt(result.time)


def perigee_window(perigee_dt: datetime, hours: float = 6.0) -> tuple[datetime, datetime]:
    half = timedelta(hours=hours)
    return perigee_dt - half, perigee_dt + half


# ---------------------------------------------------------------------------
# Lunar Nodes
# ---------------------------------------------------------------------------

def _moon_ecliptic_latitude(dt: datetime) -> float:
    t = _to_astro_time(dt)
    ecl = astronomy.EclipticGeoMoon(t)
    return ecl.lat  # ecliptic latitude


def next_node_crossing(after: datetime, step_minutes: float = 30.0) -> tuple[datetime, str]:
    """
    Find the next moment the Moon crosses the ecliptic (latitude = 0).
    Returns (datetime, node_type) where node_type is 'ascending' or 'descending'.
    """
    step = timedelta(minutes=step_minutes)
    t0 = after
    lat0 = _moon_ecliptic_latitude(t0)

    for _ in range(int(30 * 24 * 60 / step_minutes)):  # search up to 30 days
        t1 = t0 + step
        lat1 = _moon_ecliptic_latitude(t1)
        if lat0 * lat1 <= 0:  # sign change → crossing
            # bisect to ~1 minute precision
            lo, hi = t0, t1
            for _ in range(10):
                mid = lo + (hi - lo) / 2
                lat_mid = _moon_ecliptic_latitude(mid)
                if lat_mid * lat0 <= 0:
                    hi = mid
                else:
                    lo = mid
                    lat0 = lat_mid
            crossing = lo + (hi - lo) / 2
            node_type = "ascending" if lat0 < 0 else "descending"
            return crossing, node_type
        t0, lat0 = t1, lat1

    raise RuntimeError("No node crossing found within 30 days")


def node_window(node_dt: datetime, hours: float = 2.0) -> tuple[datetime, datetime]:
    half = timedelta(hours=hours)
    return node_dt - half, node_dt + half


# ---------------------------------------------------------------------------
# Moon phase exact moments
# ---------------------------------------------------------------------------

_PHASE_TARGETS = {
    "new": 0.0,
    "first_quarter": 90.0,
    "full": 180.0,
    "last_quarter": 270.0,
}


def next_moon_phase(after: datetime, phase: str) -> datetime:
    target = _PHASE_TARGETS[phase]
    t = _to_astro_time(after)
    result = astronomy.SearchMoonPhase(target, t, 35.0)
    if result is None:
        raise RuntimeError(f"Could not find moon phase {phase}")
    return _astro_time_to_dt(result)


# ---------------------------------------------------------------------------
# Constellation transitions
# ---------------------------------------------------------------------------

def find_constellation_transitions(
    start: datetime, end: datetime, step_minutes: float = 15.0
) -> list[tuple[datetime, str, str]]:
    """
    Return a list of (moment, from_constellation, to_constellation) for
    every time the Moon changes sidereal constellation between start and end.
    """
    step = timedelta(minutes=step_minutes)
    transitions = []
    t = start
    prev_const = moon_constellation(t)

    while t < end:
        t_next = min(t + step, end)
        curr_const = moon_constellation(t_next)
        if curr_const != prev_const:
            # bisect
            lo, hi = t, t_next
            for _ in range(10):
                mid = lo + (hi - lo) / 2
                c = moon_constellation(mid)
                if c == prev_const:
                    lo = mid
                else:
                    hi = mid
            moment = lo + (hi - lo) / 2
            transitions.append((moment, prev_const, curr_const))
            prev_const = curr_const
        t = t_next

    return transitions

"""Moon position, phase and declination calculations via astronomy-engine."""

from datetime import datetime, timezone

import astronomy

from biodynamic.core.zodiac import constellation_from_tropical, tropical_to_sidereal


def _to_astro_time(dt: datetime) -> astronomy.Time:
    """Convert a UTC-aware datetime to astronomy.Time."""
    if dt.tzinfo is None:
        raise ValueError("datetime must be UTC-aware")
    ut = dt.replace(tzinfo=timezone.utc).timestamp() / 86400.0 + 2440587.5
    return astronomy.Time(ut)


def moon_ecliptic_longitude(dt: datetime) -> tuple[float, float]:
    """Return (tropical_longitude_deg, julian_date) for the Moon at dt (UTC)."""
    t = _to_astro_time(dt)
    ecl = astronomy.EclipticGeoMoon(t)
    return ecl.lon, t.tt  # tropical ecliptic longitude, Julian TT


def moon_sidereal_longitude(dt: datetime) -> float:
    """Return sidereal ecliptic longitude of the Moon at dt (UTC)."""
    trop, jd = moon_ecliptic_longitude(dt)
    return tropical_to_sidereal(trop, jd)


def moon_constellation(dt: datetime) -> str:
    """Return the sidereal constellation the Moon is in at dt (UTC)."""
    trop, jd = moon_ecliptic_longitude(dt)
    return constellation_from_tropical(trop, jd)


def moon_phase_angle(dt: datetime) -> float:
    """Return the Moon's phase angle in degrees (0 = new, 180 = full)."""
    t = _to_astro_time(dt)
    return astronomy.MoonPhase(t)


def moon_illumination(dt: datetime) -> float:
    """Return the fraction of the Moon's disk that is illuminated (0.0–1.0)."""
    t = _to_astro_time(dt)
    illum = astronomy.Illumination(astronomy.Body.Moon, t)
    return illum.phase_fraction


def moon_phase_name(dt: datetime) -> str:
    """Return a descriptive moon phase name."""
    angle = moon_phase_angle(dt)
    if angle < 22.5:
        return "new"
    elif angle < 67.5:
        return "waxing_crescent"
    elif angle < 112.5:
        return "first_quarter"
    elif angle < 157.5:
        return "waxing_gibbous"
    elif angle < 202.5:
        return "full"
    elif angle < 247.5:
        return "waning_gibbous"
    elif angle < 292.5:
        return "last_quarter"
    elif angle < 337.5:
        return "waning_crescent"
    else:
        return "new"


def moon_declination(dt: datetime) -> float:
    """Return Moon's declination in degrees at dt (UTC)."""
    t = _to_astro_time(dt)
    eq = astronomy.Equator(astronomy.Body.Moon, t, astronomy.Observer(0, 0, 0), True, True)
    return eq.dec


def moon_ascending(dt: datetime, step_hours: float = 6.0) -> bool:
    """
    Return True if the Moon's declination is increasing (ascending phase).
    Compares declination now vs step_hours ago.
    """
    from datetime import timedelta

    dec_now = moon_declination(dt)
    dec_before = moon_declination(dt - timedelta(hours=step_hours))
    return dec_now > dec_before

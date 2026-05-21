"""Sidereal zodiac mapping using Fagan-Bradley ayanamsa."""

from datetime import datetime

# Fagan-Bradley ayanamsa anchored to J2000.0: 24°2'22" (standard value)
# Source: Astronomical Almanac / Fagan-Bradley standard
_FAGAN_BRADLEY_J2000 = 24.0 + 2.0 / 60.0 + 22.0 / 3600.0  # = 24.0394°
_AYANAMSA_RATE_SEC_PER_YEAR = 50.258  # arc-seconds per Julian year (IAU precession)
_J2000 = 2451545.0  # Julian date of J2000.0

# Constellation order (0°–360° sidereal longitude)
CONSTELLATIONS = [
    "aries",
    "taurus",
    "gemini",
    "cancer",
    "leo",
    "virgo",
    "libra",
    "scorpio",
    "sagittarius",
    "capricorn",
    "aquarius",
    "pisces",
]

ELEMENT = {
    "aries": "fire",
    "leo": "fire",
    "sagittarius": "fire",
    "taurus": "earth",
    "virgo": "earth",
    "capricorn": "earth",
    "gemini": "air",
    "libra": "air",
    "aquarius": "air",
    "cancer": "water",
    "scorpio": "water",
    "pisces": "water",
}

DAY_TYPE = {
    "fire": "fruit",
    "earth": "root",
    "air": "flower",
    "water": "leaf",
}

DAY_TYPE_EMOJI = {
    "fruit": "🍇",
    "root": "🥕",
    "flower": "🌸",
    "leaf": "🥬",
}


def ayanamsa(jd: float) -> float:
    """Return Fagan-Bradley ayanamsa in degrees for the given Julian date."""
    years_since_2000 = (jd - _J2000) / 365.25
    return _FAGAN_BRADLEY_J2000 + (_AYANAMSA_RATE_SEC_PER_YEAR * years_since_2000) / 3600.0


def tropical_to_sidereal(tropical_lon: float, jd: float) -> float:
    """Convert tropical ecliptic longitude to sidereal, normalised to [0, 360)."""
    sid = (tropical_lon - ayanamsa(jd)) % 360.0
    if sid < 0:
        sid += 360.0
    return sid


def constellation_from_sidereal(sidereal_lon: float) -> str:
    """Return constellation name for a sidereal ecliptic longitude (0–360°)."""
    index = int(sidereal_lon // 30) % 12
    return CONSTELLATIONS[index]


def constellation_from_tropical(tropical_lon: float, jd: float) -> str:
    sid = tropical_to_sidereal(tropical_lon, jd)
    return constellation_from_sidereal(sid)


def day_type_for_constellation(constellation: str) -> str:
    return DAY_TYPE[ELEMENT[constellation]]

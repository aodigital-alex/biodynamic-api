"""Tests for sidereal zodiac calculations."""

import pytest
from biodynamic.core.zodiac import (
    ayanamsa,
    constellation_from_sidereal,
    day_type_for_constellation,
    tropical_to_sidereal,
)


def test_ayanamsa_2000():
    # J2000 = JD 2451545.0; Fagan-Bradley ayanamsa ≈ 25.25°
    jd_2000 = 2451545.0
    result = ayanamsa(jd_2000)
    assert 25.0 < result < 25.5


def test_ayanamsa_increases_over_time():
    jd_1900 = 2415020.0
    jd_2000 = 2451545.0
    assert ayanamsa(jd_2000) > ayanamsa(jd_1900)


def test_constellation_from_sidereal_aries():
    assert constellation_from_sidereal(0.0) == "aries"
    assert constellation_from_sidereal(15.0) == "aries"
    assert constellation_from_sidereal(29.9) == "aries"


def test_constellation_from_sidereal_taurus():
    assert constellation_from_sidereal(30.0) == "taurus"


def test_constellation_from_sidereal_pisces():
    assert constellation_from_sidereal(330.0) == "pisces"
    assert constellation_from_sidereal(359.9) == "pisces"


def test_constellation_wraps():
    assert constellation_from_sidereal(360.0) == "aries"


def test_day_types():
    assert day_type_for_constellation("aries") == "fruit"
    assert day_type_for_constellation("leo") == "fruit"
    assert day_type_for_constellation("taurus") == "root"
    assert day_type_for_constellation("gemini") == "flower"
    assert day_type_for_constellation("cancer") == "leaf"


def test_tropical_to_sidereal_range():
    jd = 2451545.0
    for tropical in range(0, 360, 30):
        sid = tropical_to_sidereal(float(tropical), jd)
        assert 0.0 <= sid < 360.0

"""Tests for moon calculations."""

from datetime import datetime, timezone

import pytest
from biodynamic.core.moon import (
    moon_ascending,
    moon_constellation,
    moon_illumination,
    moon_phase_angle,
    moon_phase_name,
)


_KNOWN_NEW_MOON = datetime(2026, 5, 12, 1, 0, tzinfo=timezone.utc)
_KNOWN_FULL_MOON = datetime(2026, 5, 27, 3, 0, tzinfo=timezone.utc)


def test_moon_phase_angle_range():
    dt = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
    angle = moon_phase_angle(dt)
    assert 0.0 <= angle < 360.0


def test_moon_illumination_range():
    dt = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
    illum = moon_illumination(dt)
    assert 0.0 <= illum <= 1.0


def test_moon_illumination_near_new_moon():
    illum = moon_illumination(_KNOWN_NEW_MOON)
    assert illum < 0.1


def test_moon_illumination_near_full_moon():
    illum = moon_illumination(_KNOWN_FULL_MOON)
    assert illum > 0.9


def test_moon_phase_name_returns_valid():
    dt = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
    name = moon_phase_name(dt)
    valid = {
        "new", "waxing_crescent", "first_quarter", "waxing_gibbous",
        "full", "waning_gibbous", "last_quarter", "waning_crescent",
    }
    assert name in valid


def test_moon_constellation_returns_valid():
    dt = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
    from biodynamic.core.zodiac import CONSTELLATIONS
    const = moon_constellation(dt)
    assert const in CONSTELLATIONS


def test_moon_ascending_returns_bool():
    dt = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
    result = moon_ascending(dt)
    assert isinstance(result, bool)

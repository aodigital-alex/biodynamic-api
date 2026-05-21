# biodynamic

Open source Python library and REST API for biodynamic calendar calculations.

Biodynamic farming follows the rhythms of the Moon and stars. Winemakers, farmers, and gardeners use a biodynamic calendar to choose optimal days for planting, harvesting, or working with specific crops. This library provides accurate, fully open source calculations based on astronomical algorithms — no lookup tables, no closed-source apps.

**License:** MIT

---

## Quick start

```bash
pip install biodynamic
```

```python
from biodynamic import BiodynamicCalendar

cal = BiodynamicCalendar(timezone="Europe/Madrid")

today = cal.get_now()
print(today.day_type)        # "fruit"
print(today.day_type_emoji)  # "🍇"
print(today.favorable)       # True

# Find the next best fruit day
next_fruit = cal.next_day_of_type("fruit", favorable_only=True)
```

---

## Run the API locally

```bash
pip install "biodynamic[dev]"
biodynamic-api
# → http://localhost:8000/docs
```

### Docker

```bash
docker build -t biodynamic .
docker run -p 8000:8000 biodynamic
```

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/biodynamic/today` | Current day |
| GET | `/api/v1/biodynamic/day/{date}` | Specific date (YYYY-MM-DD) |
| GET | `/api/v1/biodynamic/range` | Date range (max 366 days) |
| GET | `/api/v1/biodynamic/week` | Current week (Mon–Sun) |
| GET | `/api/v1/biodynamic/month` | Current month |
| GET | `/api/v1/biodynamic/year` | Full year summary |
| GET | `/api/v1/biodynamic/next/{type}` | Next day of type (fruit/flower/leaf/root) |
| GET | `/api/v1/biodynamic/events` | Astronomical events in range |
| GET | `/api/v1/biodynamic/health` | Healthcheck |

All endpoints accept a `timezone` query parameter (IANA, default: `UTC`).

---

## How it works

The library uses the **sidereal zodiac** (not the tropical zodiac used in Western astrology). The sidereal zodiac is offset from the tropical by the *ayanamsa* — approximately 24° as of 2025 — following the Fagan-Bradley calculation.

The Moon's position is calculated using [astronomy-engine](https://github.com/cosinekitty/astronomy), a port of Jean Meeus' *Astronomical Algorithms* with accuracy better than 1 arc-minute. The sidereal longitude determines which constellation the Moon is in, which maps to an element, and then to a day type:

| Constellation | Element | Day type |
|---------------|---------|----------|
| Aries, Leo, Sagittarius | Fire | 🍇 Fruit/Seed |
| Taurus, Virgo, Capricorn | Earth | 🥕 Root |
| Gemini, Libra, Aquarius | Air | 🌸 Flower |
| Cancer, Scorpio, Pisces | Water | 🥬 Leaf |

Additional rhythms calculated:
- **Moon phases** — New, First Quarter, Full, Last Quarter
- **Ascending / descending Moon** — determined by lunar declination trend
- **Perigee / Apogee** — closest and farthest points in lunar orbit
- **Lunar nodes** — crossings of the ecliptic plane (unfavourable ±2 hours)

**References:**
- Jean Meeus, *Astronomical Algorithms* (2nd ed., Willmann-Bell, 1998)
- [astronomy-engine](https://github.com/cosinekitty/astronomy) — MIT license
- Maria Thun, *Biodynamic Calendar* (annual publication)

---

## Running tests

```bash
pip install -e ".[dev]"
pytest
```

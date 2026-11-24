import json
from datetime import date, datetime, timedelta

import requests
from flask import current_app

from ..extensions import db
from ..models import WeatherCache, utcnow

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DAILY_FIELDS = (
    "temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max"
)

STATUS_OK = "ok"
STATUS_TOO_FAR = "too_far"
STATUS_PAST = "past"
STATUS_ERROR = "error"


class WeatherError(Exception):
    """Raised when the forecast service cannot be reached or answers badly."""


def _fetch(latitude, longitude, day, timeout):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": DAILY_FIELDS,
        "start_date": day.isoformat(),
        "end_date": day.isoformat(),
        "timezone": "auto",
    }
    try:
        response = requests.get(FORECAST_URL, params=params, timeout=timeout)
        response.raise_for_status()
        daily = response.json()["daily"]
        return {
            "temp_min": daily["temperature_2m_min"][0],
            "temp_max": daily["temperature_2m_max"][0],
            "rain_probability": daily["precipitation_probability_max"][0],
            "wind_max": daily["wind_speed_10m_max"][0],
        }
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        raise WeatherError("Forecast request failed") from exc


def _cache_row(latitude, longitude, day):
    return db.session.execute(
        db.select(WeatherCache).filter_by(latitude=latitude, longitude=longitude, day=day)
    ).scalar_one_or_none()


def get_daily_forecast(latitude, longitude, when):
    """Return {"status": ..., "data": {...} or None} for the day of `when`."""
    day = when.date() if isinstance(when, datetime) else when
    delta = (day - date.today()).days
    if delta < 0:
        return {"status": STATUS_PAST, "data": None}
    if delta >= current_app.config["FORECAST_MAX_DAYS"]:
        return {"status": STATUS_TOO_FAR, "data": None}

    latitude, longitude = round(latitude, 2), round(longitude, 2)
    row = _cache_row(latitude, longitude, day)
    max_age = timedelta(hours=current_app.config["WEATHER_CACHE_HOURS"])
    if row is not None and utcnow() - row.fetched_at < max_age:
        return {"status": STATUS_OK, "data": json.loads(row.payload)}

    try:
        data = _fetch(latitude, longitude, day, current_app.config["HTTP_TIMEOUT"])
    except WeatherError:
        if row is not None:  # stale data is better than nothing
            return {"status": STATUS_OK, "data": json.loads(row.payload)}
        return {"status": STATUS_ERROR, "data": None}

    if row is None:
        row = WeatherCache(latitude=latitude, longitude=longitude, day=day, payload="")
        db.session.add(row)
    row.payload = json.dumps(data)
    row.fetched_at = utcnow()
    db.session.commit()
    return {"status": STATUS_OK, "data": data}

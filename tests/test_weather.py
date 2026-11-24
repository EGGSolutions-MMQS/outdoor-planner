from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import requests

from outdoor_planner.extensions import db
from outdoor_planner.models import WeatherCache, utcnow
from outdoor_planner.services import weather

API_PAYLOAD = {
    "daily": {
        "temperature_2m_max": [21.5],
        "temperature_2m_min": [11.0],
        "precipitation_probability_max": [40],
        "wind_speed_10m_max": [14.2],
    }
}
EXPECTED = {"temp_min": 11.0, "temp_max": 21.5, "rain_probability": 40, "wind_max": 14.2}


def _response():
    response = MagicMock()
    response.json.return_value = API_PAYLOAD
    return response


def _in_days(days):
    return datetime.now() + timedelta(days=days)


def test_forecast_is_fetched_then_served_from_cache(app):
    with app.app_context(), patch.object(weather.requests, "get", return_value=_response()) as get:
        first = weather.get_daily_forecast(45.69, 9.67, _in_days(3))
        second = weather.get_daily_forecast(45.69, 9.67, _in_days(3))
    assert first == {"status": "ok", "data": EXPECTED}
    assert second == first
    assert get.call_count == 1


def test_expired_cache_is_refreshed(app):
    with app.app_context(), patch.object(weather.requests, "get", return_value=_response()) as get:
        weather.get_daily_forecast(45.69, 9.67, _in_days(3))
        row = db.session.execute(db.select(WeatherCache)).scalar_one()
        row.fetched_at = utcnow() - timedelta(hours=4)
        db.session.commit()
        weather.get_daily_forecast(45.69, 9.67, _in_days(3))
    assert get.call_count == 2


def test_more_than_16_days_ahead_makes_no_http_call(app):
    with app.app_context(), patch.object(weather.requests, "get") as get:
        result = weather.get_daily_forecast(45.69, 9.67, _in_days(30))
    assert result == {"status": "too_far", "data": None}
    get.assert_not_called()


def test_past_day_makes_no_http_call(app):
    with app.app_context(), patch.object(weather.requests, "get") as get:
        result = weather.get_daily_forecast(45.69, 9.67, _in_days(-2))
    assert result["status"] == "past"
    get.assert_not_called()


def test_network_error_returns_error_status(app):
    with app.app_context(), patch.object(
        weather.requests, "get", side_effect=requests.ConnectionError("down")
    ):
        result = weather.get_daily_forecast(45.69, 9.67, _in_days(3))
    assert result == {"status": "error", "data": None}


def test_detail_page_shows_too_far_message(client, make_user, make_outing):
    outing_id = make_outing(make_user("owner_org", "organizer"), days=40)
    page = client.get(f"/outings/{outing_id}")
    assert "Previsioni non ancora disponibili".encode() in page.data

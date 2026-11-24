from unittest.mock import MagicMock, patch

import pytest
import requests

from outdoor_planner.services import geocoding


def test_search_returns_places():
    response = MagicMock()
    response.json.return_value = {
        "results": [
            {"name": "Bergamo", "admin1": "Lombardia", "country": "Italia",
             "latitude": 45.69, "longitude": 9.67},
            {"name": "Senza coordinate"},
        ]
    }
    with patch.object(geocoding.requests, "get", return_value=response):
        places = geocoding.search("Bergamo")
    assert places == [
        {"label": "Bergamo, Lombardia, Italia", "latitude": 45.69, "longitude": 9.67}
    ]


def test_search_wraps_network_errors():
    with patch.object(geocoding.requests, "get", side_effect=requests.Timeout()):
        with pytest.raises(geocoding.GeocodingError):
            geocoding.search("Bergamo")

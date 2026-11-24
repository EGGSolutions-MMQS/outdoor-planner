import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
MAX_RESULTS = 5


class GeocodingError(Exception):
    """Raised when the geocoding service cannot be reached or answers badly."""


def _label(item):
    parts = [item.get("name"), item.get("admin1"), item.get("country")]
    return ", ".join(p for p in parts if p)


def search(name, timeout=5):
    """Search places by name with the Open-Meteo Geocoding API."""
    params = {"name": name, "count": MAX_RESULTS, "language": "it", "format": "json"}
    try:
        response = requests.get(GEOCODING_URL, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise GeocodingError("Geocoding request failed") from exc

    places = []
    for item in data.get("results") or []:
        if "latitude" in item and "longitude" in item:
            places.append(
                {
                    "label": _label(item),
                    "latitude": float(item["latitude"]),
                    "longitude": float(item["longitude"]),
                }
            )
    return places

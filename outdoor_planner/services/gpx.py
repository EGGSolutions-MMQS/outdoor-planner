import os
import uuid
from dataclasses import dataclass
from io import BytesIO
from math import asin, cos, radians, sin, sqrt

from defusedxml import DefusedXmlException
from defusedxml import ElementTree as SafeET
from werkzeug.utils import secure_filename

EARTH_RADIUS_KM = 6371.0088
POINT_TAGS = ("trkpt", "rtept")
LINE_TAGS = ("trkseg", "rte")


class GpxError(Exception):
    """Raised when a file is not a usable GPX track."""


@dataclass
class GpxStats:
    distance_km: float
    points: int


def _local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def haversine_km(lat1, lon1, lat2, lon2):
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def parse_gpx(data):
    """Parse GPX bytes and return total distance (km) and number of points."""
    try:
        root = SafeET.parse(BytesIO(data)).getroot()
    except (SafeET.ParseError, DefusedXmlException) as exc:
        raise GpxError("File GPX non valido") from exc

    total_km = 0.0
    total_points = 0
    for line in root.iter():
        if _local(line.tag) not in LINE_TAGS:
            continue
        coords = []
        for point in line:
            if _local(point.tag) in POINT_TAGS:
                try:
                    coords.append((float(point.attrib["lat"]), float(point.attrib["lon"])))
                except (KeyError, ValueError) as exc:
                    raise GpxError("Punto GPX senza coordinate valide") from exc
        total_points += len(coords)
        total_km += sum(haversine_km(*a, *b) for a, b in zip(coords, coords[1:]))

    if total_points == 0:
        raise GpxError("Il file GPX non contiene punti")
    return GpxStats(distance_km=round(total_km, 2), points=total_points)


def clean_original_name(name):
    return secure_filename(name or "") or "traccia.gpx"


def save_gpx(data, folder):
    """Store GPX bytes under a random name and return that name."""
    filename = f"{uuid.uuid4().hex}.gpx"
    with open(os.path.join(folder, filename), "wb") as handle:
        handle.write(data)
    return filename


def delete_gpx(folder, filename):
    if not filename:
        return
    path = os.path.join(folder, secure_filename(filename))
    if os.path.isfile(path):
        os.remove(path)

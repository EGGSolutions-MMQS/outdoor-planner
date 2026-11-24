import io
from unittest.mock import patch

import pytest

from conftest import FIXTURES
from outdoor_planner.extensions import db
from outdoor_planner.models import Outing
from outdoor_planner.services import gpx

PLACE = [{"label": "Bergamo, Lombardia, Italia", "latitude": 45.69, "longitude": 9.67}]


def test_parse_sample_gpx():
    stats = gpx.parse_gpx((FIXTURES / "sample.gpx").read_bytes())
    assert stats.points == 5
    # 0.04 degrees of latitude along a meridian: about 4.45 km
    assert stats.distance_km == pytest.approx(4.45, abs=0.05)


@pytest.mark.parametrize(
    "content",
    [
        b"not xml at all",
        b'<gpx xmlns="http://www.topografix.com/GPX/1/1"></gpx>',
        b'<!DOCTYPE gpx [<!ENTITY a "boom">]><gpx>&a;</gpx>',
        b'<gpx><trk><trkseg><trkpt lat="x" lon="1"/></trkseg></trk></gpx>',
    ],
)
def test_parse_rejects_invalid_or_malicious_gpx(content):
    with pytest.raises(gpx.GpxError):
        gpx.parse_gpx(content)


def _create_with_file(client, filename, content):
    with patch("outdoor_planner.outings.routes.geocoding.search", return_value=PLACE):
        client.post("/outings/new", data={"title": "G", "location_query": "B", "search": "1"})
    return client.post(
        "/outings/new",
        data={
            "title": "Con traccia",
            "location_choice": "0",
            "starts_at": "2099-05-01T09:00",
            "max_seats": "4",
            "save": "1",
            "gpx": (io.BytesIO(content), filename),
        },
        content_type="multipart/form-data",
    )


def test_upload_gpx_stores_stats_and_file(app, client, make_user, login):
    make_user("owner_org", "organizer")
    login("owner_org")
    response = _create_with_file(client, "traccia.gpx", (FIXTURES / "sample.gpx").read_bytes())
    assert response.status_code == 302
    with app.app_context():
        outing = db.session.execute(db.select(Outing)).scalar_one()
        assert outing.gpx_points == 5
        assert outing.gpx_filename != "traccia.gpx"  # random name on disk
    page = client.get(response.headers["Location"])
    assert b"Distanza: 4.45 km" in page.data
    assert client.get(f"/outings/{outing.id}/gpx").status_code == 200


def test_upload_rejects_wrong_extension_and_bad_content(app, client, make_user, login):
    make_user("owner_org", "organizer")
    login("owner_org")
    assert _create_with_file(client, "virus.exe", b"x").status_code == 200
    assert _create_with_file(client, "rotta.gpx", b"<gpx>").status_code == 200
    with app.app_context():
        assert db.session.query(Outing).count() == 0

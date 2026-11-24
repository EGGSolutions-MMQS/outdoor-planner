"""Seed command: creates invented users and outings. No real personal data."""

from datetime import datetime, timedelta
from pathlib import Path

import click
from flask import current_app
from flask.cli import with_appcontext

from .extensions import db
from .models import ROLE_ORGANIZER, ROLE_PARTICIPANT, Comment, Outing, Signup, User
from .services import gpx

# Documented in the README: shared test password for all invented users.
DEMO_PASSWORD = "demo-pass-2026"

USERS = [
    ("marta_org", ROLE_ORGANIZER),
    ("luca_org", ROLE_ORGANIZER),
    ("sara_part", ROLE_PARTICIPANT),
    ("paolo_part", ROLE_PARTICIPANT),
    ("giulia_part", ROLE_PARTICIPANT),
]

# (key, organizer, title, description, place, lat, lon, days from now, seats)
OUTINGS = [
    ("alto", "marta_org", "Escursione al Monte Alto",
     "Anello facile di mezza giornata. Portare acqua e scarpe da trekking.",
     "Bergamo, Lombardia, Italia", 45.6983, 9.6773, 3, 10),
    ("como", "marta_org", "Giro in bici sul Lago di Como",
     "Circa 40 km su ciclabile, ritmo tranquillo, sosta pranzo a metà percorso.",
     "Como, Lombardia, Italia", 45.8081, 9.0852, 10, 8),
    ("calcetto", "luca_org", "Partita a calcetto al parco",
     "Partita amichevole, due squadre da tre. Solo due posti disponibili.",
     "Milano, Lombardia, Italia", 45.4642, 9.1900, 5, 2),
    ("ciaspole", "luca_org", "Ciaspolata in Val Brembana",
     "Uscita con le ciaspole, attrezzatura a noleggio sul posto.",
     "San Pellegrino Terme, Lombardia, Italia", 45.8397, 9.6717, 25, 12),
    ("passata", "marta_org", "Giro di primavera (già svolto)",
     "Uscita di esempio già conclusa: resta visibile ma senza iscrizioni.",
     "Lecco, Lombardia, Italia", 45.8566, 9.3977, -20, 6),
]

SIGNUPS = {
    "alto": ["sara_part", "giulia_part"],
    "como": ["giulia_part"],
    "calcetto": ["sara_part", "paolo_part"],
    "passata": ["paolo_part"],
}

COMMENTS = [
    ("alto", "sara_part", "Ci sono! C'è un punto ristoro lungo il sentiero?"),
    ("alto", "marta_org", "Portate qualcosa da mangiare, non ci sono rifugi aperti."),
    ("como", "giulia_part", "Bici da corsa o city bike vanno bene?"),
]


def _starts_at(days):
    day = datetime.now() + timedelta(days=days)
    return day.replace(hour=9, minute=0, second=0, microsecond=0)


def _attach_sample_gpx(outing):
    sample = Path(__file__).resolve().parent.parent / "samples" / "sample-hike.gpx"
    if not sample.is_file():
        return
    data = sample.read_bytes()
    stats = gpx.parse_gpx(data)
    outing.gpx_filename = gpx.save_gpx(data, current_app.config["UPLOAD_FOLDER"])
    outing.gpx_original_name = sample.name
    outing.gpx_distance_km = stats.distance_km
    outing.gpx_points = stats.points


def _remove_uploaded_files():
    inspector = db.inspect(db.engine)
    if not inspector.has_table(Outing.__tablename__):
        return
    for outing in db.session.execute(db.select(Outing)).scalars():
        gpx.delete_gpx(current_app.config["UPLOAD_FOLDER"], outing.gpx_filename)


def seed_database():
    users = {}
    for username, role in USERS:
        user = User(username=username, role=role)
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        users[username] = user

    outings = {}
    for key, organizer, title, description, place, lat, lon, days, seats in OUTINGS:
        outing = Outing(
            title=title,
            description=description,
            location_name=place,
            latitude=lat,
            longitude=lon,
            starts_at=_starts_at(days),
            max_seats=seats,
            organizer=users[organizer],
        )
        if key == "alto":
            _attach_sample_gpx(outing)
        db.session.add(outing)
        outings[key] = outing

    for key, usernames in SIGNUPS.items():
        for username in usernames:
            db.session.add(Signup(outing=outings[key], user=users[username]))
    for key, username, body in COMMENTS:
        db.session.add(Comment(outing=outings[key], author=users[username], body=body))
    db.session.commit()


@click.command("seed")
@click.option("--reset", is_flag=True, help="Drop all existing data before seeding.")
@with_appcontext
def seed_command(reset):
    """Create the database with invented users and outings."""
    if reset:
        _remove_uploaded_files()
        db.drop_all()
    db.create_all()
    if db.session.execute(db.select(User)).first():
        click.echo("Database already has data: use --reset to recreate it.")
        raise SystemExit(1)
    seed_database()
    click.echo(f"Seeded {len(USERS)} users and {len(OUTINGS)} outings.")

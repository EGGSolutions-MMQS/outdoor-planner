from datetime import datetime
from functools import wraps

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Outing
from ..services import geocoding
from ..services import weather as weather_service
from .forms import OutingForm

bp = Blueprint("outings", __name__, url_prefix="/outings")

GEO_SESSION_KEY = "geo_results"


def organizer_required(view):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_organizer:
            abort(403)
        return view(*args, **kwargs)

    return wrapper


def get_own_outing_or_403(outing_id):
    outing = db.get_or_404(Outing, outing_id)
    if outing.organizer_id != current_user.id:
        abort(403)
    return outing


def _set_choices(form):
    results = session.get(GEO_SESSION_KEY, [])
    form.location_choice.choices = [(str(i), r["label"]) for i, r in enumerate(results)]
    return results


def _search_location(form):
    query = (form.location_query.data or "").strip()
    if not query:
        flash("Scrivi il nome di un luogo da cercare.", "error")
        return
    try:
        results = geocoding.search(query, timeout=4)
    except geocoding.GeocodingError:
        flash("Ricerca luogo non disponibile, riprova più tardi.", "error")
        return
    if not results:
        flash("Nessun luogo trovato.", "error")
    session[GEO_SESSION_KEY] = results
    _set_choices(form)
    form.location_choice.data = "0" if results else ""


def _chosen_place(form, results, outing):
    choice = form.location_choice.data or ""
    if choice.isdigit() and int(choice) < len(results):
        place = results[int(choice)]
        return place["label"], place["latitude"], place["longitude"]
    if outing is not None:
        return outing.location_name, outing.latitude, outing.longitude
    return None


def _check_dates_and_seats(form, outing):
    starts_at = form.starts_at.data
    if starts_at and (outing is None or starts_at != outing.starts_at):
        if starts_at < datetime.now():
            form.starts_at.errors.append("La data deve essere nel futuro.")
    if outing is not None and form.max_seats.data is not None:
        if form.max_seats.data < len(outing.signups):
            form.max_seats.errors.append("Ci sono già più iscritti di questi posti.")
    return not (form.starts_at.errors or form.max_seats.errors)


def _handle_form(outing=None):
    if request.method == "GET":
        session.pop(GEO_SESSION_KEY, None)
        form = OutingForm(obj=outing)
        if outing is not None:
            form.location_query.data = outing.location_name
        _set_choices(form)
        return render_template("outings/form.html", form=form, outing=outing)

    form = OutingForm()
    results = _set_choices(form)

    if form.search.data:
        _search_location(form)
        return render_template("outings/form.html", form=form, outing=outing)

    if form.validate_on_submit():
        form.starts_at.errors = list(form.starts_at.errors)
        form.max_seats.errors = list(form.max_seats.errors)
        place = _chosen_place(form, results, outing)
        if place is None:
            flash("Cerca e scegli un luogo.", "error")
        elif _check_dates_and_seats(form, outing):
            if outing is None:
                outing = Outing(organizer_id=current_user.id)
                db.session.add(outing)
            outing.title = form.title.data.strip()
            outing.description = (form.description.data or "").strip()
            outing.location_name, outing.latitude, outing.longitude = place
            outing.starts_at = form.starts_at.data
            outing.max_seats = form.max_seats.data
            db.session.commit()
            session.pop(GEO_SESSION_KEY, None)
            flash("Uscita salvata.", "success")
            return redirect(url_for("outings.detail", outing_id=outing.id))
    return render_template("outings/form.html", form=form, outing=outing)


@bp.route("/new", methods=["GET", "POST"])
@organizer_required
def create():
    return _handle_form()


@bp.route("/<int:outing_id>")
def detail(outing_id):
    outing = db.get_or_404(Outing, outing_id)
    weather = weather_service.get_daily_forecast(outing.latitude, outing.longitude, outing.starts_at)
    return render_template("outings/detail.html", outing=outing, weather=weather)


@bp.route("/<int:outing_id>/edit", methods=["GET", "POST"])
@organizer_required
def edit(outing_id):
    return _handle_form(get_own_outing_or_403(outing_id))


@bp.route("/<int:outing_id>/delete", methods=["POST"])
@organizer_required
def delete(outing_id):
    outing = get_own_outing_or_403(outing_id)
    db.session.delete(outing)
    db.session.commit()
    flash("Uscita cancellata.", "success")
    return redirect(url_for("main.index"))

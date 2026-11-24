from datetime import datetime
from functools import wraps

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from flask_login import current_user, login_required

from ..extensions import db
from ..models import ROLE_PARTICIPANT, Comment, Outing, Signup
from ..services import geocoding, gpx
from ..services import weather as weather_service
from .forms import CommentForm, OutingForm

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


def participant_required(view):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != ROLE_PARTICIPANT:
            abort(403)
        return view(*args, **kwargs)

    return wrapper


def _find_signup(outing_id):
    return db.session.execute(
        db.select(Signup).filter_by(outing_id=outing_id, user_id=current_user.id)
    ).scalar_one_or_none()


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


def _read_gpx_upload(form):
    """Return (stats, data, original_name) for an uploaded file, or None; sets form error."""
    upload = form.gpx.data
    if not upload or not getattr(upload, "filename", ""):
        return None
    data = upload.read()
    try:
        stats = gpx.parse_gpx(data)
    except gpx.GpxError as exc:
        form.gpx.errors.append(str(exc))
        return False
    return stats, data, gpx.clean_original_name(upload.filename)


def _apply_gpx(outing, upload, remove):
    folder = current_app.config["UPLOAD_FOLDER"]
    if upload:
        stats, data, original_name = upload
        gpx.delete_gpx(folder, outing.gpx_filename)
        outing.gpx_filename = gpx.save_gpx(data, folder)
        outing.gpx_original_name = original_name
        outing.gpx_distance_km = stats.distance_km
        outing.gpx_points = stats.points
    elif remove and outing.gpx_filename:
        gpx.delete_gpx(folder, outing.gpx_filename)
        outing.gpx_filename = outing.gpx_original_name = None
        outing.gpx_distance_km = outing.gpx_points = None


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
            form.gpx.errors = list(form.gpx.errors)
            upload = _read_gpx_upload(form)
            if upload is False:
                return render_template("outings/form.html", form=form, outing=outing)
            if outing is None:
                outing = Outing(organizer_id=current_user.id)
                db.session.add(outing)
            outing.title = form.title.data.strip()
            outing.description = (form.description.data or "").strip()
            outing.location_name, outing.latitude, outing.longitude = place
            outing.starts_at = form.starts_at.data
            outing.max_seats = form.max_seats.data
            _apply_gpx(outing, upload, form.remove_gpx.data)
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
    signed_up = current_user.is_authenticated and _find_signup(outing.id) is not None
    return render_template(
        "outings/detail.html",
        outing=outing,
        weather=weather,
        signed_up=signed_up,
        comment_form=CommentForm(),
    )


@bp.route("/<int:outing_id>/edit", methods=["GET", "POST"])
@organizer_required
def edit(outing_id):
    return _handle_form(get_own_outing_or_403(outing_id))


@bp.route("/<int:outing_id>/delete", methods=["POST"])
@organizer_required
def delete(outing_id):
    outing = get_own_outing_or_403(outing_id)
    gpx.delete_gpx(current_app.config["UPLOAD_FOLDER"], outing.gpx_filename)
    db.session.delete(outing)
    db.session.commit()
    flash("Uscita cancellata.", "success")
    return redirect(url_for("main.index"))


@bp.route("/<int:outing_id>/signup", methods=["POST"])
@participant_required
def signup(outing_id):
    outing = db.get_or_404(Outing, outing_id)
    if outing.is_past:
        flash("L'uscita è già stata svolta.", "error")
    elif _find_signup(outing.id) is not None:
        flash("Sei già iscritto a questa uscita.", "error")
    elif outing.seats_left <= 0:
        flash("Posti esauriti.", "error")
    else:
        db.session.add(Signup(outing_id=outing.id, user_id=current_user.id))
        db.session.commit()
        flash("Iscrizione completata.", "success")
    return redirect(url_for("outings.detail", outing_id=outing.id))


@bp.route("/<int:outing_id>/unsubscribe", methods=["POST"])
@participant_required
def unsubscribe(outing_id):
    outing = db.get_or_404(Outing, outing_id)
    existing = _find_signup(outing.id)
    if existing is None:
        flash("Non sei iscritto a questa uscita.", "error")
    else:
        db.session.delete(existing)
        db.session.commit()
        flash("Iscrizione cancellata.", "success")
    return redirect(url_for("outings.detail", outing_id=outing.id))


@bp.route("/<int:outing_id>/comments", methods=["POST"])
@login_required
def add_comment(outing_id):
    outing = db.get_or_404(Outing, outing_id)
    form = CommentForm()
    if outing.is_past:
        flash("L'uscita è già stata svolta: commenti chiusi.", "error")
    elif form.validate_on_submit():
        db.session.add(
            Comment(outing_id=outing.id, author_id=current_user.id, body=form.body.data.strip())
        )
        db.session.commit()
        flash("Commento pubblicato.", "success")
    else:
        flash("Il commento è vuoto o troppo lungo (max 1000 caratteri).", "error")
    return redirect(url_for("outings.detail", outing_id=outing.id))


@bp.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = db.get_or_404(Comment, comment_id)
    if comment.author_id != current_user.id:
        abort(403)
    outing_id = comment.outing_id
    db.session.delete(comment)
    db.session.commit()
    flash("Commento cancellato.", "success")
    return redirect(url_for("outings.detail", outing_id=outing_id))


@bp.route("/<int:outing_id>/gpx")
def download_gpx(outing_id):
    outing = db.get_or_404(Outing, outing_id)
    if not outing.gpx_filename:
        abort(404)
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        outing.gpx_filename,
        as_attachment=True,
        download_name=outing.gpx_original_name or "traccia.gpx",
    )

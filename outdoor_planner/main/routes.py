from datetime import datetime

from flask import Blueprint, render_template, request

from ..extensions import db
from ..models import Outing

bp = Blueprint("main", __name__)

MAX_QUERY_LENGTH = 100


def _like_pattern(text):
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@bp.route("/")
def index():
    q = request.args.get("q", "").strip()[:MAX_QUERY_LENGTH]
    stmt = db.select(Outing).where(Outing.starts_at >= datetime.now()).order_by(Outing.starts_at)
    if q:
        pattern = _like_pattern(q)
        stmt = stmt.where(
            db.or_(
                Outing.title.ilike(pattern, escape="\\"),
                Outing.location_name.ilike(pattern, escape="\\"),
            )
        )
    outings = db.session.execute(stmt).scalars().all()
    return render_template("main/index.html", outings=outings, q=q)

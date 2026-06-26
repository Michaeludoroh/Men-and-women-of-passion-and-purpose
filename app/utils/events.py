import re
from datetime import datetime

from flask import url_for


def slugify(text):
    text = (text or "").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text or "event"


def unique_slug(title, event_id=None):
    from ..models import Event

    base = slugify(title)
    slug = base
    counter = 2
    while True:
        query = Event.query.filter_by(slug=slug)
        if event_id:
            query = query.filter(Event.id != event_id)
        if not query.first():
            return slug
        slug = f"{base}-{counter}"
        counter += 1


def parse_datetime_local(value):
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError("Invalid date/time format")


def format_datetime_local(dt):
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%dT%H:%M")


def published_upcoming_query(now=None):
    from ..extensions import db
    from ..models import Event

    now = now or datetime.utcnow()
    return (
        Event.query.filter_by(is_published=True)
        .filter(
            db.or_(
                Event.end_date >= now,
                db.and_(Event.end_date.is_(None), Event.start_date >= now),
            )
        )
        .order_by(Event.start_date.asc())
    )


def published_past_query(now=None):
    from ..extensions import db
    from ..models import Event

    now = now or datetime.utcnow()
    return (
        Event.query.filter_by(is_published=True)
        .filter(
            db.or_(
                Event.end_date < now,
                db.and_(Event.end_date.is_(None), Event.start_date < now),
            )
        )
        .order_by(Event.start_date.desc())
    )


def absolute_static_url(path):
    if not path:
        return None
    return url_for("static", filename=path, _external=True)

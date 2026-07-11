from functools import wraps
from flask import Blueprint, jsonify, request, current_app
from ..extensions import db, csrf
from ..models import Sermon, PrayerRequest, ContactMessage, Leader, GalleryImage, Course, GALLERY_CATEGORIES, Event
from ..utils.social import get_social_dict

api = Blueprint("api", __name__, url_prefix="/api/v1")


def api_response(data=None, message="OK", status=200, success=True):
    return jsonify({"success": success, "message": message, "data": data}), status


def require_api_key(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        configured_key = (current_app.config.get("API_KEY") or "").strip()
        is_production = current_app.config.get("ENV") == "production"

        if is_production and not configured_key:
            return api_response(message="Unauthorized", status=401, success=False)

        if configured_key:
            provided = request.headers.get("X-API-Key", "")
            if provided != configured_key:
                return api_response(message="Unauthorized", status=401, success=False)

        return view_func(*args, **kwargs)

    return wrapped


def sermon_to_dict(sermon):
    if hasattr(sermon, "to_dict"):
        return sermon.to_dict()
    return {
        "id": sermon.id,
        "title": sermon.title,
        "description": sermon.description,
        "video_url": sermon.video_url,
        "category": sermon.category,
        "created_at": sermon.created_at.isoformat() if sermon.created_at else None,
    }


def course_to_dict(course):
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "tutor": course.tutor,
    }


@api.route("/health")
def health():
    return api_response({"status": "healthy", "version": "1.0"})


@api.route("/ministry")
def ministry_info():
    config = current_app.config
    return api_response(
        {
            "name": config["MINISTRY_NAME"],
            "tagline": config["MINISTRY_TAGLINE"],
            "mission": config["MINISTRY_MISSION"],
            "vision": config["MINISTRY_VISION"],
            "contact": {
                "email": config["MINISTRY_EMAIL"],
                "phone": config["MINISTRY_PHONE"],
                "address": config["MINISTRY_ADDRESS"],
            },
            "social": get_social_dict(),
            "app_download": {
                "app_store_url": config["APP_STORE_URL"],
                "play_store_url": config["PLAY_STORE_URL"],
            },
            "gallery_categories": [
                {"key": key, "label": label} for key, label in GALLERY_CATEGORIES
            ],
        }
    )


@api.route("/sermons")
def list_sermons():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    limit = min(int(request.args.get("limit", 50)), 100)

    sermons_query = Sermon.query.order_by(Sermon.created_at.desc())
    if query:
        sermons_query = sermons_query.filter(Sermon.title.ilike(f"%{query}%"))
    if category:
        sermons_query = sermons_query.filter(Sermon.category == category)

    sermons = sermons_query.limit(limit).all()
    return api_response([sermon_to_dict(s) for s in sermons])


@api.route("/sermons/<int:sermon_id>")
def get_sermon(sermon_id):
    sermon = Sermon.query.get_or_404(sermon_id)
    return api_response(sermon_to_dict(sermon))


@api.route("/leaders")
def list_leaders():
    leaders = (
        Leader.query.filter(db.or_(Leader.is_active.is_(True), Leader.is_active.is_(None)))
        .order_by(Leader.display_order.asc(), Leader.id.asc())
        .all()
    )
    return api_response([leader.to_dict() for leader in leaders])


@api.route("/leaders/<int:leader_id>")
def get_leader(leader_id):
    leader = Leader.query.get_or_404(leader_id)
    if leader.is_active is False:
        return api_response(message="Leader not found", status=404, success=False)
    return api_response(leader.to_dict())


@api.route("/gallery")
def list_gallery():
    category = request.args.get("category", "").strip()
    media_type = request.args.get("media", "").strip().lower()
    featured_only = request.args.get("featured", "").lower() in ("1", "true", "yes")
    limit = min(int(request.args.get("limit", 50)), 100)

    gallery_query = GalleryImage.query.filter(
        db.or_(GalleryImage.is_published.is_(True), GalleryImage.is_published.is_(None))
    ).order_by(GalleryImage.display_order.asc(), GalleryImage.created_at.desc())
    if category:
        gallery_query = gallery_query.filter(GalleryImage.category == category)
    if media_type == "image":
        gallery_query = gallery_query.filter(
            db.or_(GalleryImage.media_type == "image", GalleryImage.media_type.is_(None))
        )
    elif media_type == "video":
        gallery_query = gallery_query.filter(GalleryImage.media_type.in_(("video", "external")))
    elif media_type == "external":
        gallery_query = gallery_query.filter_by(media_type="external")
    if featured_only:
        gallery_query = gallery_query.filter(GalleryImage.is_featured.is_(True))

    images = gallery_query.limit(limit).all()
    return api_response([image.to_dict() for image in images])


@api.route("/gallery/<int:image_id>")
def get_gallery_image(image_id):
    image = GalleryImage.query.get_or_404(image_id)
    if image.is_published is False:
        return api_response(message="Gallery item not found", status=404, success=False)
    return api_response(image.to_dict())


@api.route("/courses")
def list_courses():
    courses = Course.query.order_by(Course.id.asc()).all()
    return api_response([course_to_dict(c) for c in courses])


@api.route("/prayer-requests", methods=["POST"])
@csrf.exempt
@require_api_key
def create_prayer_request():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    phone = (payload.get("phone") or "").strip() or None
    category = (payload.get("category") or "other").strip()
    request_text = (payload.get("request") or "").strip()
    consent = payload.get("consent_follow_up", False)

    if not name or not email or len(request_text) < 10:
        return api_response(
            message="name, email, and request (min 10 chars) are required",
            status=400,
            success=False,
        )

    prayer_req = PrayerRequest(
        name=name,
        email=email,
        phone=phone,
        category=category,
        request=request_text,
        consent_follow_up=bool(consent),
    )
    db.session.add(prayer_req)
    db.session.commit()

    from ..services.notifications import notify_ministry_prayer_request, send_prayer_confirmation
    notify_ministry_prayer_request(prayer_req)
    send_prayer_confirmation(prayer_req)
    current_app.logger.info("API prayer request from %s", email)
    return api_response({"id": prayer_req.id}, message="Prayer request received", status=201)


@api.route("/contact", methods=["POST"])
@csrf.exempt
@require_api_key
def contact_message():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    phone = (payload.get("phone") or "").strip() or None
    subject = (payload.get("subject") or "").strip()
    message = (payload.get("message") or "").strip()

    errors = []
    if not name:
        errors.append("name is required")
    if not email:
        errors.append("email is required")
    if not subject:
        errors.append("subject is required")
    if len(message) < 10:
        errors.append("message must be at least 10 characters")

    if errors:
        return api_response(
            message="; ".join(errors),
            status=400,
            success=False,
        )

    contact_msg = ContactMessage(
        name=name,
        email=email,
        phone=phone,
        subject=subject,
        message=message,
    )
    db.session.add(contact_msg)
    db.session.commit()
    current_app.logger.info("API contact message from %s", email)
    return api_response(
        {"id": contact_msg.id},
        message="Contact message submitted successfully",
        status=201,
    )


def _events_query_from_args(published_only=True):
    from datetime import datetime

    now = datetime.utcnow()
    query = Event.query
    if published_only:
        query = query.filter_by(is_published=True)

    featured = request.args.get("featured", "").lower() in ("1", "true", "yes")
    upcoming = request.args.get("upcoming", "").lower() in ("1", "true", "yes")
    past = request.args.get("past", "").lower() in ("1", "true", "yes")
    q = request.args.get("q", "").strip()

    if featured:
        query = query.filter(Event.is_featured.is_(True))
    if upcoming:
        query = query.filter(
            db.or_(
                Event.end_date >= now,
                db.and_(Event.end_date.is_(None), Event.start_date >= now),
            )
        )
        query = query.order_by(Event.start_date.asc())
    elif past:
        query = query.filter(
            db.or_(
                Event.end_date < now,
                db.and_(Event.end_date.is_(None), Event.start_date < now),
            )
        )
        query = query.order_by(Event.start_date.desc())
    else:
        query = query.order_by(Event.start_date.desc())

    if q:
        query = query.filter(Event.title.ilike(f"%{q}%"))

    return query


@api.route("/events")
def list_events():
    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(max(int(request.args.get("per_page", 20)), 1), 100)

    pagination = _events_query_from_args(published_only=True).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return api_response(
        {
            "items": [event.to_dict(absolute_urls=True) for event in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
        }
    )


@api.route("/events/<int:event_id>")
def get_event(event_id):
    event = Event.query.filter_by(id=event_id, is_published=True).first()
    if not event:
        return api_response(message="Event not found", status=404, success=False)
    return api_response(event.to_dict(absolute_urls=True))

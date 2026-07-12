from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request, Response
from flask_login import current_user, login_required
from datetime import datetime
from ..models import Sermon, Application, Leader, GalleryImage, GALLERY_CATEGORIES, Event
from ..forms import ApplicationForm, ContactForm
from ..models import ContactMessage
from ..extensions import db
from ..utils.events import published_upcoming_query, published_past_query
from ..services.website_settings import get_about_intro, mission_bullets

main = Blueprint("main", __name__)


@main.route("/")
def index():
    featured_sermons = Sermon.query.order_by(Sermon.created_at.desc()).limit(3).all()
    featured_gallery = (
        GalleryImage.query.filter_by(is_featured=True)
        .filter(db.or_(GalleryImage.is_published.is_(True), GalleryImage.is_published.is_(None)))
        .order_by(GalleryImage.display_order.asc(), GalleryImage.created_at.desc())
        .limit(6)
        .all()
    )
    founders = (
        Leader.query.filter_by(is_founder=True)
        .filter(db.or_(Leader.is_active.is_(True), Leader.is_active.is_(None)))
        .order_by(Leader.display_order.asc())
        .limit(2)
        .all()
    )
    now = datetime.utcnow()
    featured_events = (
        published_upcoming_query(now)
        .filter(Event.is_featured.is_(True))
        .limit(3)
        .all()
    )
    if not featured_events:
        featured_events = published_upcoming_query(now).limit(3).all()
    return render_template(
        "index.html",
        featured_sermons=featured_sermons,
        featured_gallery=featured_gallery,
        featured_events=featured_events,
        founders=founders,
        category_labels=dict(GALLERY_CATEGORIES),
    )


@main.route("/about")
def about():
    return render_template(
        "about.html",
        about_intro=get_about_intro(),
        mission_bullets=mission_bullets(),
    )


@main.route("/about-minister-joy")
def about_minister_joy():
    leader = Leader.query.filter(Leader.name.ilike("%joy%")).first()
    return render_template("about_minister_joy.html", leader=leader)


@main.route("/leadership")
def leadership():
    from ..constants import ORG_LEVELS, ORG_LEVEL_ORDER
    leaders = (
        Leader.query.filter(db.or_(Leader.is_active.is_(True), Leader.is_active.is_(None)))
        .order_by(Leader.display_order.asc(), Leader.id.asc())
        .all()
    )
    org_chart = {}
    for level_key, level_label in ORG_LEVELS:
        level_leaders = [l for l in leaders if (l.org_level or "coordinator") == level_key]
        if level_leaders:
            org_chart[level_key] = {"label": level_label, "leaders": level_leaders}
    return render_template("leadership.html", leaders=leaders, org_chart=org_chart, org_levels=ORG_LEVELS)


@main.route("/gallery")
def gallery():
    category = request.args.get("category", "").strip()
    media_type = request.args.get("media", "all").strip().lower()
    if media_type not in ("all", "image", "video"):
        media_type = "all"
    page = max(request.args.get("page", 1, type=int), 1)
    default_per_page = current_app.config.get("GALLERY_PER_PAGE", 12)
    per_page = request.args.get("per_page", default_per_page, type=int)
    per_page = min(max(per_page, 6), 48)

    gallery_query = GalleryImage.query.filter(
        db.or_(GalleryImage.is_published.is_(True), GalleryImage.is_published.is_(None))
    ).order_by(
        GalleryImage.display_order.asc(),
        GalleryImage.created_at.desc(),
    )
    if category:
        gallery_query = gallery_query.filter(GalleryImage.category == category)
    if media_type == "image":
        gallery_query = gallery_query.filter(
            db.or_(GalleryImage.media_type == "image", GalleryImage.media_type.is_(None))
        )
    elif media_type == "video":
        gallery_query = gallery_query.filter(GalleryImage.media_type.in_(("video", "external")))

    pagination = gallery_query.paginate(page=page, per_page=per_page, error_out=False)
    category_labels = dict(GALLERY_CATEGORIES)

    return render_template(
        "gallery.html",
        images=pagination.items,
        pagination=pagination,
        per_page=per_page,
        per_page_options=current_app.config.get("GALLERY_PER_PAGE_OPTIONS", (6, 12, 24, 36)),
        categories=GALLERY_CATEGORIES,
        category_labels=category_labels,
        active_category=category,
        active_media=media_type,
    )


@main.route("/events")
def events():
    now = datetime.utcnow()
    featured_event = (
        published_upcoming_query(now)
        .filter(Event.is_featured.is_(True))
        .first()
    )
    if not featured_event:
        featured_event = published_upcoming_query(now).first()

    upcoming_events = published_upcoming_query(now).all()
    if featured_event:
        upcoming_events = [e for e in upcoming_events if e.id != featured_event.id]

    past_events = published_past_query(now).all()
    return render_template(
        "events.html",
        featured_event=featured_event,
        upcoming_events=upcoming_events,
        past_events=past_events,
    )


@main.route("/app")
def app_download():
    return render_template("app_download.html")


@main.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy_policy.html")


@main.route("/terms-of-service")
def terms_of_service():
    return render_template("terms_of_service.html")


@main.route("/support")
def support():
    return render_template("support.html")


@main.route("/account-deletion")
def account_deletion():
    return render_template("account_deletion.html")


@main.route("/robots.txt")
def robots_txt():
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /auth/",
        "Disallow: /api/",
        "Disallow: /dashboard",
        "Disallow: /profile",
        f"Sitemap: {url_for('main.sitemap_xml', _external=True)}",
        "",
    ]
    return Response("\n".join(lines), mimetype="text/plain")


@main.route("/sitemap.xml")
def sitemap_xml():
    pages = [
        ("main.index", "1.0", "daily"),
        ("main.about", "0.8", "monthly"),
        ("main.about_minister_joy", "0.7", "monthly"),
        ("main.leadership", "0.7", "monthly"),
        ("main.gallery", "0.8", "weekly"),
        ("main.events", "0.8", "weekly"),
        ("main.app_download", "0.9", "monthly"),
        ("main.contact", "0.7", "monthly"),
        ("main.applications", "0.6", "monthly"),
        ("main.privacy_policy", "0.5", "yearly"),
        ("main.terms_of_service", "0.5", "yearly"),
        ("main.support", "0.6", "monthly"),
        ("main.account_deletion", "0.5", "yearly"),
        ("sermon.sermons", "0.8", "weekly"),
        ("prayer.prayer_request", "0.7", "monthly"),
        ("classes.classes_home", "0.7", "monthly"),
        ("giving.giving_page", "0.7", "monthly"),
        ("partnership.partnership_page", "0.7", "monthly"),
    ]
    urls = []
    for endpoint, priority, changefreq in pages:
        try:
            loc = url_for(endpoint, _external=True)
        except Exception:
            continue
        urls.append(
            f"  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <changefreq>{changefreq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            f"  </url>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    return Response(xml, mimetype="application/xml")


@main.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        contact_msg = ContactMessage(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data or None,
            subject=form.subject.data,
            message=form.message.data,
        )
        db.session.add(contact_msg)
        db.session.commit()
        flash("Your message has been sent successfully. We will get back to you soon.", "success")
        return redirect(url_for("main.contact"))
    return render_template("contact.html", form=form)


@main.route("/dashboard")
@login_required
def dashboard():
    sermons = Sermon.query.order_by(Sermon.created_at.desc()).limit(6).all()
    return render_template("dashboard.html", sermons=sermons)


@main.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    from ..forms import ProfileForm

    form = ProfileForm(name=current_user.name)
    if form.validate_on_submit():
        current_user.name = form.name.data
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("main.profile"))
    return render_template("profile.html", form=form)


@main.route("/applications", methods=["GET", "POST"])
def applications():
    form = ApplicationForm()
    if form.validate_on_submit():
        app_data = Application(
            name=form.name.data,
            email=form.email.data,
            program_type=form.program_type.data,
            message=form.message.data,
        )
        db.session.add(app_data)
        db.session.commit()
        flash("Application submitted successfully.", "success")
        return redirect(url_for("main.applications"))
    return render_template("applications.html", form=form)

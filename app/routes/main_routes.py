from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
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
        .order_by(GalleryImage.created_at.desc())
        .limit(6)
        .all()
    )
    founders = Leader.query.filter_by(is_founder=True).order_by(Leader.display_order.asc()).limit(2).all()
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
    leaders = Leader.query.order_by(Leader.display_order.asc(), Leader.id.asc()).all()
    return render_template("leadership.html", leaders=leaders)


@main.route("/gallery")
def gallery():
    category = request.args.get("category", "").strip()
    page = max(request.args.get("page", 1, type=int), 1)
    default_per_page = current_app.config.get("GALLERY_PER_PAGE", 12)
    per_page = request.args.get("per_page", default_per_page, type=int)
    per_page = min(max(per_page, 6), 48)

    gallery_query = GalleryImage.query.order_by(GalleryImage.created_at.desc())
    if category:
        gallery_query = gallery_query.filter(GalleryImage.category == category)

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

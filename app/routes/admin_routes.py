import csv
import io
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, Response
from flask_login import login_required, current_user
from ..models import User, Sermon, PrayerRequest, ContactMessage, Donation, Course, Assignment, Leader, GalleryImage, Event, Application, WebsiteSettings, Partnership, PartnershipPayment, ReminderSettings
from ..forms import SermonForm, CourseForm, AssignmentForm, LeaderForm, GalleryImageForm, EventForm, WebsiteSettingsForm, ReminderSettingsForm
from ..extensions import db
from ..constants import GIVING_CATEGORIES
from ..services.upload import (
    save_upload,
    save_video_upload,
    save_gallery_poster,
    save_sermon_image,
    save_sermon_video,
    save_sermon_poster,
    delete_upload,
    allowed_image,
    allowed_video,
    detect_media_type,
)
from ..utils.events import unique_slug, parse_datetime_local, format_datetime_local
from ..services.website_settings import get_ministry_context, get_about_intro

admin = Blueprint("admin", __name__)


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=request.path))
        if current_user.role != "admin":
            flash("Access denied: Admins only.", "danger")
            return redirect(url_for("main.index"))
        return view_func(*args, **kwargs)

    return wrapped


def _admin_stats():
    return {
        "sermons": Sermon.query.count(),
        "prayers": PrayerRequest.query.count(),
        "applications": Application.query.count(),
        "unread_applications": Application.query.filter_by(is_read=False).count(),
        "contacts": ContactMessage.query.count(),
        "unread_contacts": ContactMessage.query.filter_by(is_read=False).count(),
        "donations": Donation.query.count(),
        "partnerships": Partnership.query.count(),
        "active_partnerships": Partnership.query.filter_by(status="active").count(),
        "leaders": Leader.query.count(),
        "gallery": GalleryImage.query.count(),
        "events": Event.query.count(),
        "published_events": Event.query.filter_by(is_published=True).count(),
        "courses": Course.query.count(),
        "assignments": Assignment.query.count(),
    }


@admin.route("/")
@login_required
@admin_required
def admin_dashboard():
    current_app.logger.info(
        "Website admin dashboard viewed user_id=%s email=%s ip=%s",
        current_user.id,
        current_user.email,
        request.remote_addr,
    )
    return render_template(
        "admin/admin_dashboard.html",
        stats=_admin_stats(),
    )


@admin.route("/users")
@login_required
@admin_required
def manage_users():
    current_app.logger.info(
        "Admin users page viewed user_id=%s email=%s ip=%s",
        current_user.id,
        current_user.email,
        request.remote_addr,
    )
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/manage_users.html", users=users)


@admin.route("/prayers")
@login_required
@admin_required
def manage_prayers():
    current_app.logger.info(
        "Admin prayers page viewed user_id=%s email=%s ip=%s",
        current_user.id,
        current_user.email,
        request.remote_addr,
    )
    search = request.args.get("q", "").strip()
    filter_status = request.args.get("status", "active")

    prayers_query = PrayerRequest.query.order_by(PrayerRequest.date.desc())
    if filter_status == "active":
        prayers_query = prayers_query.filter_by(is_archived=False)
    elif filter_status == "archived":
        prayers_query = prayers_query.filter_by(is_archived=True)
    elif filter_status == "prayed":
        prayers_query = prayers_query.filter_by(is_prayed_for=True, is_archived=False)
    elif filter_status == "pending":
        prayers_query = prayers_query.filter_by(is_prayed_for=False, is_archived=False)

    if search:
        prayers_query = prayers_query.filter(
            db.or_(
                PrayerRequest.name.ilike(f"%{search}%"),
                PrayerRequest.email.ilike(f"%{search}%"),
                PrayerRequest.request.ilike(f"%{search}%"),
                PrayerRequest.category.ilike(f"%{search}%"),
            )
        )

    prayers = prayers_query.all()
    return render_template(
        "admin/manage_prayers.html",
        prayers=prayers,
        search=search,
        filter_status=filter_status,
    )


@admin.route("/prayers/<int:prayer_id>/toggle-prayed", methods=["POST"])
@login_required
@admin_required
def toggle_prayer_prayed(prayer_id):
    prayer = PrayerRequest.query.get_or_404(prayer_id)
    prayer.is_prayed_for = not prayer.is_prayed_for
    db.session.commit()
    flash("Prayer status updated.", "success")
    return redirect(request.referrer or url_for("admin.manage_prayers"))


@admin.route("/prayers/<int:prayer_id>/archive", methods=["POST"])
@login_required
@admin_required
def archive_prayer(prayer_id):
    prayer = PrayerRequest.query.get_or_404(prayer_id)
    prayer.is_archived = True
    db.session.commit()
    flash("Prayer request archived.", "info")
    return redirect(request.referrer or url_for("admin.manage_prayers"))


@admin.route("/prayers/<int:prayer_id>/unarchive", methods=["POST"])
@login_required
@admin_required
def unarchive_prayer(prayer_id):
    prayer = PrayerRequest.query.get_or_404(prayer_id)
    prayer.is_archived = False
    db.session.commit()
    flash("Prayer request restored.", "success")
    return redirect(request.referrer or url_for("admin.manage_prayers"))


@admin.route("/prayers/<int:prayer_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_prayer(prayer_id):
    prayer = PrayerRequest.query.get_or_404(prayer_id)
    db.session.delete(prayer)
    db.session.commit()
    flash("Prayer request deleted.", "info")
    return redirect(url_for("admin.manage_prayers"))


@admin.route("/applications")
@login_required
@admin_required
def manage_applications():
    filter_status = request.args.get("status", "all")
    applications_query = Application.query.order_by(Application.created_at.desc())
    if filter_status == "unread":
        applications_query = applications_query.filter_by(is_read=False)
    elif filter_status == "read":
        applications_query = applications_query.filter_by(is_read=True)
    applications = applications_query.all()
    return render_template(
        "admin/manage_applications.html",
        applications=applications,
        filter_status=filter_status,
    )


@admin.route("/applications/<int:application_id>")
@login_required
@admin_required
def view_application(application_id):
    application = Application.query.get_or_404(application_id)
    if not application.is_read:
        application.is_read = True
        db.session.commit()
    return render_template("admin/view_application.html", application=application)


@admin.route("/applications/<int:application_id>/toggle-read", methods=["POST"])
@login_required
@admin_required
def toggle_application_read(application_id):
    application = Application.query.get_or_404(application_id)
    application.is_read = not application.is_read
    db.session.commit()
    flash("Application status updated.", "success")
    return redirect(request.referrer or url_for("admin.manage_applications"))


@admin.route("/applications/<int:application_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_application(application_id):
    application = Application.query.get_or_404(application_id)
    db.session.delete(application)
    db.session.commit()
    flash("Application deleted.", "info")
    return redirect(url_for("admin.manage_applications"))


@admin.route("/site-settings", methods=["GET", "POST"])
@login_required
@admin_required
def manage_site_settings():
    settings = WebsiteSettings.get_singleton()
    ministry = get_ministry_context()
    form = WebsiteSettingsForm(
        about_intro=settings.about_intro or get_about_intro(),
        tagline=settings.tagline or ministry["MINISTRY_TAGLINE"],
        mission=settings.mission or ministry["MINISTRY_MISSION"],
        vision=settings.vision or ministry["MINISTRY_VISION"],
        ministry_email=settings.ministry_email or ministry["MINISTRY_EMAIL"],
        ministry_phone=settings.ministry_phone or ministry["MINISTRY_PHONE"],
        ministry_address=settings.ministry_address or ministry["MINISTRY_ADDRESS"],
        app_store_url=settings.app_store_url or ministry["APP_STORE_URL"],
        play_store_url=settings.play_store_url or ministry["PLAY_STORE_URL"],
    )
    if form.validate_on_submit():
        settings.about_intro = form.about_intro.data.strip()
        settings.tagline = form.tagline.data.strip()
        settings.mission = form.mission.data.strip()
        settings.vision = form.vision.data.strip()
        settings.ministry_email = form.ministry_email.data.strip()
        settings.ministry_phone = (form.ministry_phone.data or "").strip() or None
        settings.ministry_address = (form.ministry_address.data or "").strip() or None
        settings.app_store_url = (form.app_store_url.data or "").strip() or None
        settings.play_store_url = (form.play_store_url.data or "").strip() or None
        db.session.commit()
        flash("Website settings saved.", "success")
        return redirect(url_for("admin.manage_site_settings"))
    return render_template("admin/manage_site_settings.html", form=form)


@admin.route("/donations")
@login_required
@admin_required
def manage_donations():
    current_app.logger.info(
        "Admin donations page viewed user_id=%s email=%s ip=%s",
        current_user.id,
        current_user.email,
        request.remote_addr,
    )
    search = request.args.get("q", "").strip()
    donations_query = Donation.query.order_by(Donation.created_at.desc())
    if search:
        donations_query = donations_query.filter(
            db.or_(
                Donation.name.ilike(f"%{search}%"),
                Donation.email.ilike(f"%{search}%"),
                Donation.payment_reference.ilike(f"%{search}%"),
            )
        )
    donations = donations_query.all()
    return render_template(
        "admin/manage_donations.html",
        donations=donations,
        search=search,
        categories=GIVING_CATEGORIES,
    )


@admin.route("/partnerships")
@login_required
@admin_required
def manage_partnerships():
    search = request.args.get("q", "").strip()
    filter_status = request.args.get("status", "all")
    partnerships_query = Partnership.query.order_by(Partnership.created_at.desc())
    if filter_status != "all":
        partnerships_query = partnerships_query.filter_by(status=filter_status)
    if search:
        partnerships_query = partnerships_query.filter(
            db.or_(
                Partnership.name.ilike(f"%{search}%"),
                Partnership.email.ilike(f"%{search}%"),
            )
        )
    partnerships = partnerships_query.all()
    return render_template(
        "admin/manage_partnerships.html",
        partnerships=partnerships,
        search=search,
        filter_status=filter_status,
    )


@admin.route("/partnerships/<int:partnership_id>")
@login_required
@admin_required
def view_partnership(partnership_id):
    partnership = Partnership.query.get_or_404(partnership_id)
    payments = PartnershipPayment.query.filter_by(partnership_id=partnership.id).order_by(PartnershipPayment.created_at.desc()).all()
    return render_template("admin/view_partnership.html", partnership=partnership, payments=payments)


@admin.route("/reminder-settings", methods=["GET", "POST"])
@login_required
@admin_required
def manage_reminder_settings():
    settings = ReminderSettings.get_singleton()
    form = ReminderSettingsForm(
        email_reminders_enabled=settings.email_reminders_enabled,
        sms_reminders_enabled=settings.sms_reminders_enabled,
        reminder_days_before=str(settings.reminder_days_before),
    )
    if form.validate_on_submit():
        settings.email_reminders_enabled = form.email_reminders_enabled.data
        settings.sms_reminders_enabled = form.sms_reminders_enabled.data
        settings.reminder_days_before = int(form.reminder_days_before.data)
        db.session.commit()
        flash("Reminder settings saved.", "success")
        return redirect(url_for("admin.manage_reminder_settings"))
    return render_template("admin/manage_reminder_settings.html", form=form, settings=settings)


@admin.route("/reminders/send-now", methods=["POST"])
@login_required
@admin_required
def send_reminders_now():
    from ..services.reminders import process_partnership_reminders
    count = process_partnership_reminders()
    flash(f"Processed reminders. {count} notification(s) sent.", "success")
    return redirect(url_for("admin.manage_reminder_settings"))


@admin.route("/sermons", methods=["GET", "POST"])
@login_required
@admin_required
def manage_sermons():
    form = SermonForm()
    form.submit.label.text = "Save Sermon"
    max_seconds = current_app.config.get("SERMON_MAX_VIDEO_SECONDS", 300)
    max_bytes = current_app.config.get("SERMON_MAX_VIDEO_BYTES", 100 * 1024 * 1024)

    if form.validate_on_submit():
        payload, err = _apply_sermon_media(form, require_media=True)
        if err:
            flash(err, "danger")
            return redirect(url_for("admin.manage_sermons"))

        poster_path = None
        if form.media_source.data in ("video", "external") and form.poster.data and form.poster.data.filename:
            poster_path = save_sermon_poster(form.poster.data)
            if form.poster.data.filename and not poster_path:
                flash("Poster must be an image (PNG, JPG, GIF, or WEBP). Sermon was still saved.", "warning")

        sermon = Sermon(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            category=form.category.data,
            video_url=(form.video_url.data or "").strip() or None,
            media_type=payload["media_type"],
            media_path=payload["media_path"],
            poster_path=poster_path,
            external_url=payload["external_url"],
            embed_url=payload["embed_url"],
            provider=payload["provider"],
            provider_video_id=payload["provider_video_id"],
            thumbnail_url=payload["thumbnail_url"],
            duration_seconds=payload["duration_seconds"],
            mime_type=payload["mime_type"],
            file_size=payload["file_size"],
        )
        db.session.add(sermon)
        db.session.commit()
        current_app.logger.info(
            "Admin created sermon sermon_id=%s title=%s media_type=%s user_id=%s email=%s ip=%s",
            sermon.id,
            sermon.title,
            sermon.media_type,
            current_user.id,
            current_user.email,
            request.remote_addr,
        )
        flash(f"Sermon saved ({sermon.media_type}).", "success")
        return redirect(url_for("admin.manage_sermons"))

    current_app.logger.info(
        "Admin sermons page viewed user_id=%s email=%s ip=%s",
        current_user.id,
        current_user.email,
        request.remote_addr,
    )
    sermons = Sermon.query.order_by(Sermon.created_at.desc()).all()
    return render_template(
        "admin/manage_sermons.html",
        sermons=sermons,
        form=form,
        sermon_max_video_seconds=max_seconds,
        sermon_max_video_mb=max_bytes // (1024 * 1024),
    )


@admin.route("/sermons/<int:sermon_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_sermon(sermon_id):
    sermon = Sermon.query.get_or_404(sermon_id)
    form = SermonForm()
    form.submit.label.text = "Save Changes"
    max_seconds = current_app.config.get("SERMON_MAX_VIDEO_SECONDS", 300)
    max_bytes = current_app.config.get("SERMON_MAX_VIDEO_BYTES", 100 * 1024 * 1024)

    if request.method == "GET":
        _populate_sermon_form(form, sermon)

    if form.validate_on_submit():
        source = form.media_source.data
        media_file = form.media.data
        has_new_file = media_file and getattr(media_file, "filename", None)
        need_media = source == "external" or has_new_file or (
            source != (sermon.media_type or "image") and source in ("image", "video", "external")
        )

        if source == "external" or has_new_file:
            payload, err = _apply_sermon_media(form, require_media=(source == "external" or has_new_file))
            if err:
                flash(err, "danger")
                return render_template(
                    "admin/edit_sermon.html",
                    form=form,
                    sermon=sermon,
                    sermon_max_video_seconds=max_seconds,
                    sermon_max_video_mb=max_bytes // (1024 * 1024),
                )
            if sermon.media_path and payload.get("media_path") and sermon.media_path != payload["media_path"]:
                delete_upload(sermon.media_path)
            if source == "external":
                if sermon.media_path:
                    delete_upload(sermon.media_path)
                if sermon.poster_path and not (form.poster.data and form.poster.data.filename):
                    # keep existing poster unless replaced below
                    pass
            for key, value in payload.items():
                setattr(sermon, key, value)
            if payload["media_type"] == "image" and sermon.poster_path:
                delete_upload(sermon.poster_path)
                sermon.poster_path = None
        elif need_media and source in ("image", "video") and source != (sermon.media_type or "image"):
            flash("Upload a new file when switching between image and MP4.", "danger")
            return render_template(
                "admin/edit_sermon.html",
                form=form,
                sermon=sermon,
                sermon_max_video_seconds=max_seconds,
                sermon_max_video_mb=max_bytes // (1024 * 1024),
            )
        else:
            sermon.media_type = source

        if form.poster.data and form.poster.data.filename:
            if (sermon.media_type or "image") not in ("video", "external"):
                flash("Poster images are only used for videos.", "warning")
            else:
                new_poster = save_sermon_poster(form.poster.data)
                if not new_poster:
                    flash("Poster must be an image (PNG, JPG, GIF, or WEBP).", "danger")
                    return render_template(
                        "admin/edit_sermon.html",
                        form=form,
                        sermon=sermon,
                        sermon_max_video_seconds=max_seconds,
                        sermon_max_video_mb=max_bytes // (1024 * 1024),
                    )
                if sermon.poster_path:
                    delete_upload(sermon.poster_path)
                sermon.poster_path = new_poster

        sermon.title = form.title.data.strip()
        sermon.description = form.description.data.strip()
        sermon.category = form.category.data
        sermon.video_url = (form.video_url.data or "").strip() or None
        db.session.commit()
        flash("Sermon updated successfully.", "success")
        return redirect(url_for("admin.manage_sermons"))

    return render_template(
        "admin/edit_sermon.html",
        form=form,
        sermon=sermon,
        sermon_max_video_seconds=max_seconds,
        sermon_max_video_mb=max_bytes // (1024 * 1024),
    )


def _sermon_video_limits():
    max_seconds = current_app.config.get("SERMON_MAX_VIDEO_SECONDS", 300)
    max_bytes = current_app.config.get("SERMON_MAX_VIDEO_BYTES", 100 * 1024 * 1024)
    return max_seconds, max_bytes


def _populate_sermon_form(form, sermon):
    form.title.data = sermon.title
    form.description.data = sermon.description
    form.category.data = sermon.category
    form.media_source.data = sermon.media_type if sermon.media_type in ("image", "video", "external") else "image"
    form.external_url.data = sermon.external_url or ""
    form.video_url.data = sermon.video_url or ""


def _apply_sermon_media(form, require_media=True):
    """Validate and build media payload for sermon create/edit. Returns (dict, error)."""
    from ..services.sermon_media import get_sermon_mp4_duration_seconds, parse_sermon_external_url

    source = form.media_source.data
    max_seconds, max_bytes = _sermon_video_limits()

    if source == "external":
        raw = (form.external_url.data or "").strip()
        if not raw:
            return None, "Please paste an external video URL."
        try:
            info = parse_sermon_external_url(raw)
        except ValueError as exc:
            return None, str(exc)
        return {
            "media_path": None,
            "media_type": "external",
            "mime_type": None,
            "file_size": None,
            "duration_seconds": None,
            "external_url": info.watch_url,
            "embed_url": info.embed_url,
            "provider": info.provider,
            "provider_video_id": info.video_id,
            "thumbnail_url": info.thumbnail_url,
        }, None

    media_file = form.media.data
    if not media_file or not getattr(media_file, "filename", None):
        if require_media:
            return None, "Please choose a file to upload."
        return None, None

    file_size = None
    try:
        media_file.stream.seek(0, 2)
        file_size = media_file.stream.tell()
        media_file.stream.seek(0)
    except Exception:
        file_size = None

    if source == "image":
        path = save_sermon_image(media_file)
        if not path:
            return None, "Unsupported image. Use PNG, JPG, JPEG, GIF, or WEBP."
        return {
            "media_path": path,
            "media_type": "image",
            "mime_type": getattr(media_file, "mimetype", None) or "image/jpeg",
            "file_size": file_size,
            "duration_seconds": None,
            "external_url": None,
            "embed_url": None,
            "provider": None,
            "provider_video_id": None,
            "thumbnail_url": None,
        }, None

    if source == "video":
        if file_size is not None and file_size > max_bytes:
            return None, f"Video is too large. Maximum size is {max_bytes // (1024 * 1024)} MB."
        mime = (getattr(media_file, "mimetype", None) or "").lower()
        if mime and mime not in ("video/mp4", "application/mp4", "application/octet-stream"):
            return None, "Unsupported video format. Upload an MP4 file (video/mp4) only."
        duration = get_sermon_mp4_duration_seconds(media_file)
        if duration is not None and duration > max_seconds:
            return None, (
                f"Video is too long ({int(duration)}s). "
                f"Maximum duration is {max_seconds} seconds (5 minutes)."
            )
        path, _media_type = save_sermon_video(media_file)
        if not path:
            return None, "Unsupported video. Upload an MP4 file only (AVI, MOV, MKV, etc. are rejected)."
        return {
            "media_path": path,
            "media_type": "video",
            "mime_type": "video/mp4",
            "file_size": file_size,
            "duration_seconds": duration,
            "external_url": None,
            "embed_url": None,
            "provider": None,
            "provider_video_id": None,
            "thumbnail_url": None,
        }, None

    return None, "Invalid media type."


@admin.route("/sermons/<int:sermon_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_sermon(sermon_id):
    sermon = Sermon.query.get_or_404(sermon_id)
    title = sermon.title
    if sermon.media_path:
        delete_upload(sermon.media_path)
    if sermon.poster_path:
        delete_upload(sermon.poster_path)
    db.session.delete(sermon)
    db.session.commit()
    current_app.logger.info(
        "Admin deleted sermon sermon_id=%s title=%s user_id=%s email=%s ip=%s",
        sermon_id,
        title,
        current_user.id,
        current_user.email,
        request.remote_addr,
    )
    flash("Sermon deleted.", "info")
    return redirect(url_for("admin.manage_sermons"))


@admin.route("/users/<int:user_id>/make-admin", methods=["POST"])
@login_required
@admin_required
def make_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.role = "admin"
    db.session.commit()
    current_app.logger.info(
        "Admin promoted user target_user_id=%s target_email=%s by_user_id=%s by_email=%s ip=%s",
        user.id,
        user.email,
        current_user.id,
        current_user.email,
        request.remote_addr,
    )
    flash(f"{user.name} is now an admin.", "success")
    return redirect(url_for("admin.manage_users"))


@admin.route("/classes", methods=["GET", "POST"])
@login_required
@admin_required
def manage_classes():
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            title=form.title.data,
            description=form.description.data,
            tutor=form.tutor.data,
        )
        db.session.add(course)
        db.session.commit()
        flash("Course created successfully.", "success")
        return redirect(url_for("admin.manage_classes"))

    courses = Course.query.order_by(Course.id.desc()).all()
    return render_template("admin/manage_classes.html", courses=courses, form=form)


@admin.route("/classes/<int:course_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted.", "info")
    return redirect(url_for("admin.manage_classes"))


@admin.route("/assignments", methods=["GET", "POST"])
@login_required
@admin_required
def manage_assignments():
    form = AssignmentForm()
    if form.validate_on_submit():
        # Note: To add course_id to AssignmentForm or use select. Default first course.
        first_course = Course.query.first()
        if first_course:
            assignment = Assignment(
                course_id=first_course.id,
                title=form.title.data,
                file=form.file.data.filename if form.file.data else None,
            )
            db.session.add(assignment)
            db.session.commit()
            flash("Assignment created successfully.", "success")
        else:
            flash("No courses available. Create a course first.", "danger")
        return redirect(url_for("admin.manage_assignments"))

    assignments = Assignment.query.join(Course).order_by(Assignment.id.desc()).all()
    return render_template("admin/manage_assignments.html", assignments=assignments, form=form)


def _optional_text(value):
    text = (value or "").strip()
    return text or None


def _apply_leader_form_fields(leader, form):
    """Apply non-media leader fields from the form onto an existing or new Leader."""
    leader.name = form.name.data.strip()
    leader.role = form.role.data.strip()
    leader.title = _optional_text(form.title.data)
    leader.department = _optional_text(form.department.data)
    leader.bio = form.bio.data.strip()
    leader.email = _optional_text(form.email.data)
    leader.phone = _optional_text(form.phone.data)
    leader.facebook_url = _optional_text(form.facebook_url.data)
    leader.instagram_url = _optional_text(form.instagram_url.data)
    leader.youtube_url = _optional_text(form.youtube_url.data)
    leader.twitter_url = _optional_text(form.twitter_url.data)
    leader.is_founder = form.is_founder.data == "1"
    leader.is_active = form.is_active.data == "1"
    leader.org_level = form.org_level.data
    try:
        leader.display_order = int(form.display_order.data or 0)
    except (TypeError, ValueError):
        leader.display_order = 0


def _handle_leader_media(leader, form, is_new=False):
    """
    Keep / replace / remove photo and video.
    Returns (ok: bool, error_message: str|None).
    """
    photo_file = form.photo.data
    video_file = form.video.data

    if form.remove_photo.data and not is_new:
        if leader.photo:
            delete_upload(leader.photo)
        leader.photo = None
    elif photo_file and getattr(photo_file, "filename", None):
        if not allowed_image(photo_file.filename):
            return False, "Invalid photo. Use PNG, JPG, JPEG, GIF, or WEBP."
        new_photo = save_upload(photo_file, "leaders")
        if not new_photo:
            return False, "Unable to save profile image. Please try again."
        if leader.photo:
            delete_upload(leader.photo)
        leader.photo = new_photo

    if form.remove_video.data and not is_new:
        if leader.video:
            delete_upload(leader.video)
        leader.video = None
    elif video_file and getattr(video_file, "filename", None):
        if not allowed_video(video_file.filename):
            return False, "Invalid leader video. Use MP4 or WebM only."
        new_video = save_video_upload(video_file, "leader_videos")
        if not new_video:
            return False, "Unable to save leader video. Please try again."
        if leader.video:
            delete_upload(leader.video)
        leader.video = new_video

    return True, None


def _populate_leader_form(form, leader):
    form.name.data = leader.name
    form.role.data = leader.role
    form.title.data = leader.title or ""
    form.department.data = leader.department or ""
    form.bio.data = leader.bio
    form.email.data = leader.email or ""
    form.phone.data = leader.phone or ""
    form.facebook_url.data = leader.facebook_url or ""
    form.instagram_url.data = leader.instagram_url or ""
    form.youtube_url.data = leader.youtube_url or ""
    form.twitter_url.data = leader.twitter_url or ""
    form.is_founder.data = "1" if leader.is_founder else "0"
    form.is_active.data = "1" if (leader.is_active is None or leader.is_active) else "0"
    form.display_order.data = str(leader.display_order or 0)
    form.org_level.data = leader.org_level or "coordinator"
    form.remove_photo.data = False
    form.remove_video.data = False


@admin.route("/leaders", methods=["GET", "POST"])
@login_required
@admin_required
def manage_leaders():
    form = LeaderForm()
    form.submit.label.text = "Add Leader"
    if form.validate_on_submit():
        leader = Leader()
        ok, error = _handle_leader_media(leader, form, is_new=True)
        if not ok:
            flash(error, "danger")
            leaders = Leader.query.order_by(Leader.display_order.asc(), Leader.id.asc()).all()
            return render_template("admin/manage_leaders.html", leaders=leaders, form=form)
        _apply_leader_form_fields(leader, form)
        db.session.add(leader)
        db.session.commit()
        flash("Leader added successfully.", "success")
        return redirect(url_for("admin.manage_leaders"))

    leaders = Leader.query.order_by(Leader.display_order.asc(), Leader.id.asc()).all()
    return render_template("admin/manage_leaders.html", leaders=leaders, form=form)


@admin.route("/leaders/<int:leader_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_leader(leader_id):
    leader = Leader.query.get_or_404(leader_id)
    form = LeaderForm()
    form.submit.label.text = "Save Changes"

    if request.method == "GET":
        _populate_leader_form(form, leader)

    if form.validate_on_submit():
        ok, error = _handle_leader_media(leader, form, is_new=False)
        if not ok:
            flash(error, "danger")
            return render_template("admin/edit_leader.html", form=form, leader=leader)
        _apply_leader_form_fields(leader, form)
        db.session.commit()
        flash("Leader updated successfully. Changes are live on the public Leadership page.", "success")
        return redirect(url_for("admin.manage_leaders"))

    return render_template("admin/edit_leader.html", form=form, leader=leader)


@admin.route("/leaders/<int:leader_id>/remove-photo", methods=["POST"])
@login_required
@admin_required
def remove_leader_photo(leader_id):
    leader = Leader.query.get_or_404(leader_id)
    if leader.photo:
        delete_upload(leader.photo)
        leader.photo = None
        db.session.commit()
        flash("Profile image removed.", "info")
    else:
        flash("This leader has no profile image to remove.", "warning")
    return redirect(request.referrer or url_for("admin.edit_leader", leader_id=leader.id))


@admin.route("/leaders/<int:leader_id>/remove-video", methods=["POST"])
@login_required
@admin_required
def remove_leader_video(leader_id):
    leader = Leader.query.get_or_404(leader_id)
    if leader.video:
        delete_upload(leader.video)
        leader.video = None
        db.session.commit()
        flash("Leader video removed.", "info")
    else:
        flash("This leader has no video to remove.", "warning")
    return redirect(request.referrer or url_for("admin.edit_leader", leader_id=leader.id))


@admin.route("/leaders/<int:leader_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_leader(leader_id):
    leader = Leader.query.get_or_404(leader_id)
    if leader.photo:
        delete_upload(leader.photo)
    if leader.video:
        delete_upload(leader.video)
    db.session.delete(leader)
    db.session.commit()
    flash("Leader removed.", "info")
    return redirect(url_for("admin.manage_leaders"))


def _gallery_display_order(form):
    try:
        return int(form.display_order.data or 0)
    except (TypeError, ValueError):
        return 0


def _populate_gallery_form(form, item):
    form.title.data = item.title
    form.description.data = item.description or ""
    form.event_name.data = item.event_name or ""
    form.category.data = item.category
    form.media_source.data = item.media_type if item.media_type in ("image", "video", "external") else "image"
    form.external_url.data = item.external_url or ""
    form.display_order.data = str(item.display_order or 0)
    form.is_featured.data = "1" if item.is_featured else "0"
    form.is_published.data = "1" if (item.is_published is None or item.is_published) else "0"


def _gallery_video_limits():
    max_seconds = current_app.config.get("GALLERY_MAX_VIDEO_SECONDS", 300)
    max_bytes = current_app.config.get("GALLERY_MAX_VIDEO_BYTES", 100 * 1024 * 1024)
    return max_seconds, max_bytes


def _apply_uploaded_gallery_file(form, source):
    """Validate and save image or MP4 based on media_source. Returns dict or None + flash."""
    from ..services.gallery_media import validate_gallery_mp4_file
    from ..services.upload import save_gallery_image_only, save_gallery_video_only

    media_file = form.media.data
    if not media_file or not getattr(media_file, "filename", None):
        return None, "Please choose a file to upload."

    max_seconds, max_bytes = _gallery_video_limits()
    detected_mime = (getattr(media_file, "mimetype", None) or "").strip()
    original_name = (getattr(media_file, "filename", None) or "").strip()

    if source == "image":
        path, media_type = save_gallery_image_only(media_file)
        if not path:
            current_app.logger.info(
                "Gallery image upload rejected name=%s mime=%s",
                original_name[:120],
                detected_mime[:80],
            )
            return None, "Unsupported format. Use PNG, JPG, JPEG, GIF, or WEBP."
        file_size = None
        try:
            media_file.stream.seek(0, 2)
            file_size = media_file.stream.tell()
            media_file.stream.seek(0)
        except Exception:
            file_size = None
        current_app.logger.info(
            "Gallery image upload ok name=%s mime=%s size=%s path=%s",
            original_name[:120],
            detected_mime[:80],
            file_size,
            path,
        )
        return {
            "image_path": path,
            "media_type": "image",
            "mime_type": detected_mime or "image/jpeg",
            "file_size": file_size,
            "duration_seconds": None,
            "external_url": None,
            "embed_url": None,
            "provider": None,
            "provider_video_id": None,
            "thumbnail_url": None,
        }, None

    if source == "video":
        meta, err = validate_gallery_mp4_file(
            media_file,
            max_seconds=max_seconds,
            max_bytes=max_bytes,
        )
        if err:
            current_app.logger.info(
                "Gallery MP4 upload rejected name=%s mime=%s reason=%s",
                original_name[:120],
                detected_mime[:80],
                err,
            )
            return None, err

        path, media_type = save_gallery_video_only(media_file)
        if not path:
            current_app.logger.info(
                "Gallery MP4 save failed name=%s mime=%s size=%s duration=%s",
                original_name[:120],
                detected_mime[:80],
                (meta or {}).get("file_size"),
                (meta or {}).get("duration_seconds"),
            )
            return None, "Upload failed. Unable to save the MP4 file."

        current_app.logger.info(
            "Gallery MP4 upload ok name=%s mime=%s size=%s duration=%s path=%s",
            original_name[:120],
            (meta or {}).get("mime_type") or detected_mime[:80],
            (meta or {}).get("file_size"),
            (meta or {}).get("duration_seconds"),
            path,
        )
        return {
            "image_path": path,
            "media_type": "video",
            "mime_type": "video/mp4",
            "file_size": (meta or {}).get("file_size"),
            "duration_seconds": (meta or {}).get("duration_seconds"),
            "external_url": None,
            "embed_url": None,
            "provider": None,
            "provider_video_id": None,
            "thumbnail_url": None,
        }, None

    return None, "Invalid media type."


def _apply_external_gallery_url(form):
    from ..services.gallery_media import parse_external_video_url

    raw = (form.external_url.data or "").strip()
    if not raw:
        return None, "Please paste an external video URL."
    try:
        info = parse_external_video_url(raw)
    except ValueError as exc:
        return None, str(exc)
    return {
        "image_path": None,
        "media_type": "external",
        "mime_type": None,
        "file_size": None,
        "duration_seconds": None,
        "external_url": info.watch_url,
        "embed_url": info.embed_url,
        "provider": info.provider,
        "provider_video_id": info.video_id,
        "thumbnail_url": info.thumbnail_url,
    }, None


def _clear_gallery_local_files(item):
    if item.image_path:
        delete_upload(item.image_path)
        item.image_path = None
    if item.poster_path:
        delete_upload(item.poster_path)
        item.poster_path = None


@admin.route("/gallery", methods=["GET", "POST"])
@login_required
@admin_required
def manage_gallery():
    form = GalleryImageForm()
    form.submit.label.text = "Save Media"
    media_filter = request.args.get("media", "all")
    max_seconds, max_bytes = _gallery_video_limits()

    if form.validate_on_submit():
        source = form.media_source.data
        poster_path = None

        if source == "external":
            payload, err = _apply_external_gallery_url(form)
        else:
            payload, err = _apply_uploaded_gallery_file(form, source)

        if err:
            flash(err, "danger")
            return redirect(url_for("admin.manage_gallery"))

        if source in ("video", "external") and form.poster.data and form.poster.data.filename:
            poster_path = save_gallery_poster(form.poster.data)
            if form.poster.data.filename and not poster_path:
                flash("Poster must be an image (PNG, JPG, GIF, or WEBP). Media was still saved.", "warning")

        item = GalleryImage(
            title=form.title.data.strip(),
            description=(form.description.data or "").strip() or None,
            event_name=(form.event_name.data or "").strip() or None,
            category=form.category.data,
            image_path=payload["image_path"],
            media_type=payload["media_type"],
            poster_path=poster_path,
            external_url=payload["external_url"],
            embed_url=payload["embed_url"],
            provider=payload["provider"],
            provider_video_id=payload["provider_video_id"],
            thumbnail_url=payload["thumbnail_url"],
            duration_seconds=payload["duration_seconds"],
            mime_type=payload["mime_type"],
            file_size=payload["file_size"],
            display_order=_gallery_display_order(form),
            is_featured=form.is_featured.data == "1",
            is_published=form.is_published.data == "1",
        )
        db.session.add(item)
        db.session.commit()
        flash(f"Gallery {payload['media_type']} saved successfully.", "success")
        return redirect(url_for("admin.manage_gallery"))

    items_query = GalleryImage.query.order_by(
        GalleryImage.display_order.asc(),
        GalleryImage.created_at.desc(),
    )
    if media_filter == "image":
        items_query = items_query.filter(
            db.or_(GalleryImage.media_type == "image", GalleryImage.media_type.is_(None))
        )
    elif media_filter == "video":
        items_query = items_query.filter(GalleryImage.media_type.in_(("video", "external")))
    elif media_filter == "external":
        items_query = items_query.filter_by(media_type="external")

    items = items_query.all()
    return render_template(
        "admin/manage_gallery.html",
        images=items,
        form=form,
        media_filter=media_filter,
        gallery_max_video_seconds=max_seconds,
        gallery_max_video_mb=max_bytes // (1024 * 1024),
    )


@admin.route("/gallery/<int:image_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_gallery_image(image_id):
    item = GalleryImage.query.get_or_404(image_id)
    form = GalleryImageForm()
    form.submit.label.text = "Save Changes"
    max_seconds, max_bytes = _gallery_video_limits()

    if request.method == "GET":
        _populate_gallery_form(form, item)

    if form.validate_on_submit():
        source = form.media_source.data
        media_file = form.media.data
        has_new_file = media_file and getattr(media_file, "filename", None)
        external_changed = source == "external" and (form.external_url.data or "").strip()

        if source == "external":
            if external_changed or item.media_type != "external":
                payload, err = _apply_external_gallery_url(form)
                if err:
                    flash(err, "danger")
                    return render_template(
                        "admin/edit_gallery.html",
                        form=form,
                        item=item,
                        gallery_max_video_seconds=max_seconds,
                        gallery_max_video_mb=max_bytes // (1024 * 1024),
                    )
                _clear_gallery_local_files(item)
                for key, value in payload.items():
                    setattr(item, key, value)
        else:
            if has_new_file:
                payload, err = _apply_uploaded_gallery_file(form, source)
                if err:
                    flash(err, "danger")
                    return render_template(
                        "admin/edit_gallery.html",
                        form=form,
                        item=item,
                        gallery_max_video_seconds=max_seconds,
                        gallery_max_video_mb=max_bytes // (1024 * 1024),
                    )
                # Clear previous local/external fields as needed
                if item.image_path and item.image_path != payload["image_path"]:
                    delete_upload(item.image_path)
                if item.media_type == "external":
                    item.external_url = None
                    item.embed_url = None
                    item.provider = None
                    item.provider_video_id = None
                    item.thumbnail_url = None
                for key, value in payload.items():
                    setattr(item, key, value)
                if payload["media_type"] == "image" and item.poster_path:
                    delete_upload(item.poster_path)
                    item.poster_path = None
            elif item.media_type != source and source in ("image", "video"):
                flash("Upload a new file when switching between image and MP4.", "danger")
                return render_template(
                    "admin/edit_gallery.html",
                    form=form,
                    item=item,
                    gallery_max_video_seconds=max_seconds,
                    gallery_max_video_mb=max_bytes // (1024 * 1024),
                )

        if form.poster.data and form.poster.data.filename:
            if (item.media_type or "image") not in ("video", "external"):
                flash("Poster images are only used for videos.", "warning")
            else:
                new_poster = save_gallery_poster(form.poster.data)
                if not new_poster:
                    flash("Poster must be an image (PNG, JPG, GIF, or WEBP).", "danger")
                    return render_template(
                        "admin/edit_gallery.html",
                        form=form,
                        item=item,
                        gallery_max_video_seconds=max_seconds,
                        gallery_max_video_mb=max_bytes // (1024 * 1024),
                    )
                if item.poster_path:
                    delete_upload(item.poster_path)
                item.poster_path = new_poster

        item.title = form.title.data.strip()
        item.description = (form.description.data or "").strip() or None
        item.event_name = (form.event_name.data or "").strip() or None
        item.category = form.category.data
        item.display_order = _gallery_display_order(form)
        item.is_featured = form.is_featured.data == "1"
        item.is_published = form.is_published.data == "1"
        db.session.commit()
        flash("Gallery item updated successfully.", "success")
        return redirect(url_for("admin.manage_gallery"))

    return render_template(
        "admin/edit_gallery.html",
        form=form,
        item=item,
        gallery_max_video_seconds=max_seconds,
        gallery_max_video_mb=max_bytes // (1024 * 1024),
    )


@admin.route("/gallery/<int:image_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_gallery_image(image_id):
    item = GalleryImage.query.get_or_404(image_id)
    if item.image_path:
        delete_upload(item.image_path)
    if item.poster_path:
        delete_upload(item.poster_path)
    db.session.delete(item)
    db.session.commit()
    flash("Gallery item deleted.", "info")
    return redirect(url_for("admin.manage_gallery"))


@admin.route("/gallery/<int:image_id>/toggle-featured", methods=["POST"])
@login_required
@admin_required
def toggle_gallery_featured(image_id):
    item = GalleryImage.query.get_or_404(image_id)
    item.is_featured = not item.is_featured
    db.session.commit()
    status = "featured" if item.is_featured else "unfeatured"
    flash(f"Media marked as {status}.", "success")
    return redirect(url_for("admin.manage_gallery"))


@admin.route("/gallery/<int:image_id>/toggle-published", methods=["POST"])
@login_required
@admin_required
def toggle_gallery_published(image_id):
    item = GalleryImage.query.get_or_404(image_id)
    item.is_published = not (item.is_published if item.is_published is not None else True)
    db.session.commit()
    status = "published" if item.is_published else "hidden"
    flash(f"Media marked as {status}.", "success")
    return redirect(url_for("admin.manage_gallery"))


@admin.route("/contacts")
@login_required
@admin_required
def manage_contacts():
    filter_status = request.args.get("status", "all")
    contacts_query = ContactMessage.query.order_by(ContactMessage.created_at.desc())
    if filter_status == "unread":
        contacts_query = contacts_query.filter_by(is_read=False)
    elif filter_status == "read":
        contacts_query = contacts_query.filter_by(is_read=True)
    contacts = contacts_query.all()
    return render_template(
        "admin/manage_contacts.html",
        contacts=contacts,
        filter_status=filter_status,
    )


@admin.route("/contacts/<int:message_id>")
@login_required
@admin_required
def view_contact(message_id):
    contact = ContactMessage.query.get_or_404(message_id)
    if not contact.is_read:
        contact.is_read = True
        db.session.commit()
    return render_template("admin/view_contact.html", contact=contact)


@admin.route("/contacts/<int:message_id>/toggle-read", methods=["POST"])
@login_required
@admin_required
def toggle_contact_read(message_id):
    contact = ContactMessage.query.get_or_404(message_id)
    contact.is_read = not contact.is_read
    db.session.commit()
    flash("Message status updated.", "success")
    return redirect(request.referrer or url_for("admin.manage_contacts"))


@admin.route("/contacts/<int:message_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_contact(message_id):
    contact = ContactMessage.query.get_or_404(message_id)
    db.session.delete(contact)
    db.session.commit()
    flash("Contact message deleted.", "info")
    return redirect(url_for("admin.manage_contacts"))


@admin.route("/contacts/export")
@login_required
@admin_required
def export_contacts():
    contacts = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Email", "Phone", "Subject", "Message", "Created At", "Is Read"])
    for contact in contacts:
        writer.writerow([
            contact.id,
            contact.name,
            contact.email,
            contact.phone or "",
            contact.subject,
            contact.message,
            contact.created_at.strftime("%Y-%m-%d %H:%M") if contact.created_at else "",
            "Yes" if contact.is_read else "No",
        ])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=contact_messages.csv"},
    )


def _apply_event_form(event, form, is_new=False):
    try:
        start_date = parse_datetime_local(form.start_date.data)
        end_date = parse_datetime_local(form.end_date.data) if form.end_date.data else None
    except ValueError:
        flash("Invalid date/time format. Use the date picker.", "danger")
        return False

    if end_date and end_date < start_date:
        flash("End date must be after the start date.", "danger")
        return False

    banner_path = save_upload(form.banner_image.data, "events") if form.banner_image.data else None
    if is_new and not banner_path:
        pass
    elif banner_path:
        event.banner_image = banner_path

    event.title = form.title.data
    event.slug = unique_slug(form.title.data, event.id if not is_new else None)
    event.description = form.description.data
    event.venue = form.venue.data or None
    event.location = form.location.data or None
    event.start_date = start_date
    event.end_date = end_date
    event.registration_link = form.registration_link.data or None
    event.is_featured = form.is_featured.data == "1"
    event.is_published = form.is_published.data == "1"
    return True


@admin.route("/events")
@login_required
@admin_required
def manage_events():
    events = Event.query.order_by(Event.start_date.desc()).all()
    return render_template("admin/manage_events.html", events=events)


@admin.route("/events/new", methods=["GET", "POST"])
@login_required
@admin_required
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            slug=unique_slug(form.title.data),
            description=form.description.data,
            venue=form.venue.data or None,
            location=form.location.data or None,
            start_date=datetime.utcnow(),
            registration_link=form.registration_link.data or None,
            is_featured=form.is_featured.data == "1",
            is_published=form.is_published.data == "1",
        )
        if not _apply_event_form(event, form, is_new=True):
            return render_template("admin/event_form.html", form=form, event=None, is_new=True)

        db.session.add(event)
        db.session.commit()
        current_app.logger.info(
            "Admin created event event_id=%s title=%s user_id=%s",
            event.id,
            event.title,
            current_user.id,
        )
        flash("Event created successfully.", "success")
        return redirect(url_for("admin.manage_events"))

    return render_template("admin/event_form.html", form=form, event=None, is_new=True)


@admin.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    form = EventForm(obj=event)
    if request.method == "GET":
        form.start_date.data = format_datetime_local(event.start_date)
        form.end_date.data = format_datetime_local(event.end_date)
        form.is_featured.data = "1" if event.is_featured else "0"
        form.is_published.data = "1" if event.is_published else "0"

    if form.validate_on_submit():
        if not _apply_event_form(event, form, is_new=False):
            return render_template("admin/event_form.html", form=form, event=event, is_new=False)

        db.session.commit()
        current_app.logger.info(
            "Admin updated event event_id=%s title=%s user_id=%s",
            event.id,
            event.title,
            current_user.id,
        )
        flash("Event updated successfully.", "success")
        return redirect(url_for("admin.manage_events"))

    return render_template("admin/event_form.html", form=form, event=event, is_new=False)


@admin.route("/events/<int:event_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted.", "info")
    return redirect(url_for("admin.manage_events"))


@admin.route("/events/<int:event_id>/toggle-publish", methods=["POST"])
@login_required
@admin_required
def toggle_event_publish(event_id):
    event = Event.query.get_or_404(event_id)
    event.is_published = not event.is_published
    db.session.commit()
    status = "published" if event.is_published else "unpublished"
    flash(f"Event {status}.", "success")
    return redirect(url_for("admin.manage_events"))


@admin.route("/events/<int:event_id>/toggle-featured", methods=["POST"])
@login_required
@admin_required
def toggle_event_featured(event_id):
    event = Event.query.get_or_404(event_id)
    event.is_featured = not event.is_featured
    db.session.commit()
    status = "featured" if event.is_featured else "unfeatured"
    flash(f"Event marked as {status}.", "success")
    return redirect(url_for("admin.manage_events"))

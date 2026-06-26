import csv
import io
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, Response
from flask_login import login_required, current_user
from ..models import User, Sermon, PrayerRequest, ContactMessage, Donation, Course, Assignment, Leader, GalleryImage, Event
from ..forms import SermonForm, CourseForm, AssignmentForm, LeaderForm, GalleryImageForm, EventForm
from ..extensions import db
from ..services.upload import save_upload
from ..utils.events import unique_slug, parse_datetime_local, format_datetime_local

admin = Blueprint("admin", __name__)


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role != "admin":
            flash("Access denied: Admins only.", "danger")
            return redirect(url_for("main.index"))
        return view_func(*args, **kwargs)

    return wrapped


@admin.route("/")
@login_required
@admin_required
def admin_dashboard():
    current_app.logger.info(
        "Admin dashboard viewed user_id=%s email=%s ip=%s",
        current_user.id,
        current_user.email,
        request.remote_addr,
    )
    stats = {
        "users": User.query.count(),
        "sermons": Sermon.query.count(),
        "prayers": PrayerRequest.query.count(),
        "contacts": ContactMessage.query.count(),
        "unread_contacts": ContactMessage.query.filter_by(is_read=False).count(),
        "donations": Donation.query.count(),
        "courses": Course.query.count(),
        "assignments": Assignment.query.count(),
        "leaders": Leader.query.count(),
        "gallery": GalleryImage.query.count(),
        "events": Event.query.count(),
        "published_events": Event.query.filter_by(is_published=True).count(),
    }
    return render_template("admin/admin_dashboard.html", stats=stats)


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
    prayers = PrayerRequest.query.order_by(PrayerRequest.date.desc()).all()
    return render_template("admin/manage_prayers.html", prayers=prayers)


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
    donations = Donation.query.order_by(Donation.created_at.desc()).all()
    return render_template("admin/manage_donations.html", donations=donations)


@admin.route("/sermons", methods=["GET", "POST"])
@login_required
@admin_required
def manage_sermons():
    form = SermonForm()
    if form.validate_on_submit():
        sermon = Sermon(
            title=form.title.data,
            description=form.description.data,
            video_url=form.video_url.data,
            category=form.category.data,
        )
        db.session.add(sermon)
        db.session.commit()
        current_app.logger.info(
            "Admin created sermon sermon_id=%s title=%s user_id=%s email=%s ip=%s",
            sermon.id,
            sermon.title,
            current_user.id,
            current_user.email,
            request.remote_addr,
        )
        flash("Sermon created successfully.", "success")
        return redirect(url_for("admin.manage_sermons"))

    current_app.logger.info(
        "Admin sermons page viewed user_id=%s email=%s ip=%s",
        current_user.id,
        current_user.email,
        request.remote_addr,
    )
    sermons = Sermon.query.order_by(Sermon.created_at.desc()).all()
    return render_template("admin/manage_sermons.html", sermons=sermons, form=form)


@admin.route("/sermons/<int:sermon_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_sermon(sermon_id):
    sermon = Sermon.query.get_or_404(sermon_id)
    db.session.delete(sermon)
    db.session.commit()
    current_app.logger.info(
        "Admin deleted sermon sermon_id=%s title=%s user_id=%s email=%s ip=%s",
        sermon_id,
        sermon.title,
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


@admin.route("/leaders", methods=["GET", "POST"])
@login_required
@admin_required
def manage_leaders():
    form = LeaderForm()
    if form.validate_on_submit():
        photo_path = save_upload(form.photo.data, "leaders") if form.photo.data else None
        leader = Leader(
            name=form.name.data,
            role=form.role.data,
            title=form.title.data,
            bio=form.bio.data,
            photo=photo_path,
            is_founder=form.is_founder.data == "1",
            display_order=int(form.display_order.data or 0),
        )
        db.session.add(leader)
        db.session.commit()
        flash("Leader added successfully.", "success")
        return redirect(url_for("admin.manage_leaders"))

    leaders = Leader.query.order_by(Leader.display_order.asc(), Leader.id.asc()).all()
    return render_template("admin/manage_leaders.html", leaders=leaders, form=form)


@admin.route("/leaders/<int:leader_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_leader(leader_id):
    leader = Leader.query.get_or_404(leader_id)
    db.session.delete(leader)
    db.session.commit()
    flash("Leader removed.", "info")
    return redirect(url_for("admin.manage_leaders"))


@admin.route("/gallery", methods=["GET", "POST"])
@login_required
@admin_required
def manage_gallery():
    form = GalleryImageForm()
    if form.validate_on_submit():
        image_path = save_upload(form.image.data, "gallery")
        if not image_path:
            flash("Invalid image file. Use PNG, JPG, JPEG, GIF, or WEBP.", "danger")
            return redirect(url_for("admin.manage_gallery"))

        image = GalleryImage(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            image_path=image_path,
            is_featured=form.is_featured.data == "1",
        )
        db.session.add(image)
        db.session.commit()
        flash("Gallery image uploaded successfully.", "success")
        return redirect(url_for("admin.manage_gallery"))

    images = GalleryImage.query.order_by(GalleryImage.created_at.desc()).all()
    return render_template("admin/manage_gallery.html", images=images, form=form)


@admin.route("/gallery/<int:image_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_gallery_image(image_id):
    image = GalleryImage.query.get_or_404(image_id)
    db.session.delete(image)
    db.session.commit()
    flash("Gallery image deleted.", "info")
    return redirect(url_for("admin.manage_gallery"))


@admin.route("/gallery/<int:image_id>/toggle-featured", methods=["POST"])
@login_required
@admin_required
def toggle_gallery_featured(image_id):
    image = GalleryImage.query.get_or_404(image_id)
    image.is_featured = not image.is_featured
    db.session.commit()
    status = "featured" if image.is_featured else "unfeatured"
    flash(f"Image marked as {status}.", "success")
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

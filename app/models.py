from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="member")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submissions = db.relationship("Submission", backref="student", lazy=True)
    enrollments = db.relationship("CourseEnrollment", backref="user", lazy=True)

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    def is_enrolled(self, course_id):
        enrollment = CourseEnrollment.query.filter_by(user_id=self.id, course_id=course_id).first()
        return enrollment is not None


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Sermon(db.Model):
    """Ministry teachings and preaching — independent from GalleryImage."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    video_url = db.Column(db.String(500), nullable=True)  # legacy preview URL/path
    category = db.Column(db.String(120), nullable=False, default="General")
    media_type = db.Column(db.String(20), nullable=False, default="image")  # image | video | external
    media_path = db.Column(db.String(300), nullable=True)  # local image or uploaded MP4
    poster_path = db.Column(db.String(300), nullable=True)
    external_url = db.Column(db.String(500), nullable=True)
    embed_url = db.Column(db.String(500), nullable=True)
    provider = db.Column(db.String(40), nullable=True)
    provider_video_id = db.Column(db.String(120), nullable=True)
    thumbnail_url = db.Column(db.String(500), nullable=True)
    duration_seconds = db.Column(db.Float, nullable=True)
    mime_type = db.Column(db.String(80), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_external(self):
        return (self.media_type or "") == "external"

    @property
    def is_uploaded_video(self):
        return (self.media_type or "") == "video"

    @property
    def is_image(self):
        mt = self.media_type or "image"
        if mt == "image":
            return True
        # Legacy rows with no media_type fields yet
        if mt not in ("video", "external") and not self.media_path and not self.external_url:
            return not bool(self.video_url)
        return False

    @property
    def media_url(self):
        if self.is_external:
            return self.external_url
        if self.media_path:
            return f"/static/{self.media_path}"
        # Legacy preview clip
        if self.video_url:
            if self.video_url.startswith("http://") or self.video_url.startswith("https://"):
                return self.video_url
            return f"/static/{self.video_url.lstrip('/')}"
        return None

    @property
    def watch_url(self):
        """Destination when the visitor chooses to watch the full sermon."""
        if self.is_external and self.external_url:
            return self.external_url
        if self.is_uploaded_video and self.media_path:
            return f"/static/{self.media_path}"
        if self.external_url:
            return self.external_url
        return None

    @property
    def poster_url(self):
        if self.poster_path:
            return f"/static/{self.poster_path}"
        if self.thumbnail_url:
            return self.thumbnail_url
        if (self.media_type or "image") == "image" and self.media_path:
            return f"/static/{self.media_path}"
        return None

    @property
    def provider_label(self):
        labels = {
            "youtube": "YouTube",
            "facebook": "Facebook",
            "instagram": "Instagram",
            "tiktok": "TikTok",
            "vimeo": "Vimeo",
            "twitter": "X",
        }
        return labels.get(self.provider or "", (self.provider or "").title())

    @property
    def preview_video_src(self):
        """Muted autoplay preview source for uploaded MP4 (or legacy video_url)."""
        if self.is_uploaded_video and self.media_path:
            return f"/static/{self.media_path}"
        if self.video_url and not self.is_external:
            if self.video_url.startswith("http://") or self.video_url.startswith("https://"):
                # Only use http video_url as preview if it looks like a direct media file
                lower = self.video_url.lower()
                if any(lower.endswith(ext) for ext in (".mp4", ".webm", ".ogg")):
                    return self.video_url
                return None
            return f"/static/{self.video_url.lstrip('/')}"
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "media_type": self.media_type or "image",
            "video_url": self.video_url,
            "media_url": self.media_url,
            "watch_url": self.watch_url,
            "poster_url": self.poster_url,
            "external_url": self.external_url,
            "embed_url": self.embed_url,
            "provider": self.provider,
            "provider_label": self.provider_label,
            "thumbnail_url": self.thumbnail_url,
            "duration_seconds": self.duration_seconds,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PrayerRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    category = db.Column(db.String(50), nullable=False, default="other")
    request = db.Column(db.Text, nullable=False)
    consent_follow_up = db.Column(db.Boolean, default=False)
    is_prayed_for = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "category": self.category,
            "request": self.request,
            "consent_follow_up": self.consent_follow_up,
            "is_prayed_for": self.is_prayed_for,
            "is_archived": self.is_archived,
            "date": self.date.isoformat() if self.date else None,
        }


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "subject": self.subject,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_read": self.is_read,
        }


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tutor = db.Column(db.String(120), nullable=False)

    assignments = db.relationship("Assignment", backref="course", lazy=True)
    enrollments = db.relationship("CourseEnrollment", backref="course", lazy=True, cascade="all, delete-orphan")


class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    file = db.Column(db.String(300), nullable=True)

    submissions = db.relationship("Submission", backref="assignment", lazy=True)


class CourseEnrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='unique_enrollment'),)


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id"), nullable=False)
    answer_file = db.Column(db.String(300), nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="NGN")
    category = db.Column(db.String(50), nullable=False, default="tithing")
    payment_reference = db.Column(db.String(200), nullable=False, unique=True)
    gateway = db.Column(db.String(50), default="paystack")
    payment_status = db.Column(db.String(20), default="pending")
    verified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="donations", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "amount": self.amount,
            "currency": self.currency,
            "category": self.category,
            "payment_reference": self.payment_reference,
            "gateway": self.gateway,
            "payment_status": self.payment_status,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    program_type = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)


class WebsiteSettings(db.Model):
    """Editable website copy and contact details (single row)."""
    id = db.Column(db.Integer, primary_key=True)
    about_intro = db.Column(db.Text)
    mission = db.Column(db.Text)
    vision = db.Column(db.Text)
    tagline = db.Column(db.Text)
    ministry_email = db.Column(db.String(255))
    ministry_phone = db.Column(db.String(50))
    ministry_address = db.Column(db.Text)
    app_store_url = db.Column(db.String(500))
    play_store_url = db.Column(db.String(500))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_singleton(cls):
        row = cls.query.first()
        if row:
            return row
        row = cls()
        db.session.add(row)
        db.session.commit()
        return row


GALLERY_CATEGORIES = [
    ("conferences", "Conferences"),
    ("empowerment", "Empowerment Projects"),
    ("anniversary", "Anniversary"),
    ("events", "Events"),
    ("outreach", "Outreach Programs"),
]


class Leader(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    bio = db.Column(db.Text, nullable=False)
    photo = db.Column(db.String(300), nullable=True)
    video = db.Column(db.String(300), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    department = db.Column(db.String(120), nullable=True)
    facebook_url = db.Column(db.String(500), nullable=True)
    instagram_url = db.Column(db.String(500), nullable=True)
    youtube_url = db.Column(db.String(500), nullable=True)
    twitter_url = db.Column(db.String(500), nullable=True)
    is_founder = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    org_level = db.Column(db.String(50), default="coordinator")
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "title": self.title,
            "bio": self.bio,
            "photo_url": f"/static/{self.photo}" if self.photo else None,
            "video_url": f"/static/{self.video}" if self.video else None,
            "email": self.email,
            "phone": self.phone,
            "department": self.department,
            "social": {
                "facebook": self.facebook_url,
                "instagram": self.instagram_url,
                "youtube": self.youtube_url,
                "twitter": self.twitter_url,
            },
            "is_founder": self.is_founder,
            "is_active": self.is_active,
            "org_level": self.org_level,
            "display_order": self.display_order,
        }


class Partnership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="NGN")
    frequency = db.Column(db.String(30), nullable=False, default="monthly")
    payment_method = db.Column(db.String(30), nullable=False, default="flutterwave")
    status = db.Column(db.String(20), default="active")
    next_due_date = db.Column(db.DateTime, nullable=True)
    last_payment_date = db.Column(db.DateTime, nullable=True)
    last_reminder_sent = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref="partnerships", lazy=True)
    payments = db.relationship("PartnershipPayment", backref="partnership", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "amount": self.amount,
            "currency": self.currency,
            "frequency": self.frequency,
            "payment_method": self.payment_method,
            "status": self.status,
            "next_due_date": self.next_due_date.isoformat() if self.next_due_date else None,
            "last_payment_date": self.last_payment_date.isoformat() if self.last_payment_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PartnershipPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    partnership_id = db.Column(db.Integer, db.ForeignKey("partnership.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="NGN")
    payment_reference = db.Column(db.String(200), nullable=True)
    gateway = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default="pending")
    paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ReminderSettings(db.Model):
    """Singleton settings for partnership reminder notifications."""
    id = db.Column(db.Integer, primary_key=True)
    email_reminders_enabled = db.Column(db.Boolean, default=True)
    sms_reminders_enabled = db.Column(db.Boolean, default=False)
    reminder_days_before = db.Column(db.Integer, default=1)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_singleton(cls):
        row = cls.query.first()
        if row:
            return row
        row = cls()
        db.session.add(row)
        db.session.commit()
        return row


class GalleryImage(db.Model):
    """Gallery media item — images, uploaded MP4, or external video links."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False, default="events")
    event_name = db.Column(db.String(200), nullable=True)
    image_path = db.Column(db.String(300), nullable=True)  # local image or uploaded MP4 path
    media_type = db.Column(db.String(20), nullable=False, default="image")  # image | video | external
    poster_path = db.Column(db.String(300), nullable=True)  # optional local poster/thumbnail
    external_url = db.Column(db.String(500), nullable=True)  # canonical watch URL on platform
    embed_url = db.Column(db.String(500), nullable=True)
    provider = db.Column(db.String(40), nullable=True)  # youtube, facebook, ...
    provider_video_id = db.Column(db.String(120), nullable=True)
    thumbnail_url = db.Column(db.String(500), nullable=True)  # remote thumbnail when available
    duration_seconds = db.Column(db.Float, nullable=True)
    mime_type = db.Column(db.String(80), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    display_order = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_external(self):
        return (self.media_type or "") == "external"

    @property
    def is_uploaded_video(self):
        return (self.media_type or "image") == "video"

    @property
    def is_video(self):
        """True for uploaded MP4 or external video links (used by video filters/UI)."""
        return (self.media_type or "image") in ("video", "external")

    @property
    def media_url(self):
        if self.is_external:
            return self.external_url
        return f"/static/{self.image_path}" if self.image_path else None

    @property
    def watch_url(self):
        """URL opened when the user clicks an external gallery item."""
        if self.is_external:
            return self.external_url
        return self.media_url

    @property
    def poster_url(self):
        if self.poster_path:
            return f"/static/{self.poster_path}"
        if self.thumbnail_url:
            return self.thumbnail_url
        if (self.media_type or "image") == "image" and self.image_path:
            return f"/static/{self.image_path}"
        return None

    @property
    def provider_label(self):
        labels = {
            "youtube": "YouTube",
            "facebook": "Facebook",
            "instagram": "Instagram",
            "tiktok": "TikTok",
            "vimeo": "Vimeo",
            "twitter": "X",
        }
        return labels.get(self.provider or "", (self.provider or "").title())

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "event_name": self.event_name,
            "media_type": self.media_type or "image",
            "image_url": self.media_url if not self.is_external else self.poster_url,
            "media_url": self.media_url,
            "watch_url": self.watch_url,
            "poster_url": self.poster_url,
            "external_url": self.external_url,
            "embed_url": self.embed_url,
            "provider": self.provider,
            "provider_label": self.provider_label,
            "thumbnail_url": self.thumbnail_url,
            "duration_seconds": self.duration_seconds,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "display_order": self.display_order or 0,
            "is_featured": self.is_featured,
            "is_published": self.is_published if self.is_published is not None else True,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    venue = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(300), nullable=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    banner_image = db.Column(db.String(300), nullable=True)
    registration_link = db.Column(db.String(500), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_upcoming(self, now=None):
        now = now or datetime.utcnow()
        end = self.end_date or self.start_date
        return end >= now

    def short_description(self, length=140):
        text = (self.description or "").strip()
        if len(text) <= length:
            return text
        return text[: length - 3].rstrip() + "..."

    def to_dict(self, absolute_urls=False):
        from flask import url_for

        banner_url = None
        if self.banner_image:
            banner_url = url_for(
                "static",
                filename=self.banner_image,
                _external=absolute_urls,
            )

        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "short_description": self.short_description(),
            "venue": self.venue,
            "location": self.location,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "banner_image": self.banner_image,
            "banner_url": banner_url,
            "registration_link": self.registration_link,
            "is_featured": self.is_featured,
            "is_published": self.is_published,
            "is_upcoming": self.is_upcoming(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


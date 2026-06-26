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
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    video_url = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(120), nullable=False, default="General")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PrayerRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    request = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)


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
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_reference = db.Column(db.String(200), nullable=False, unique=True)
    gateway = db.Column(db.String(50), default='paystack')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    program_type = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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
    is_founder = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "title": self.title,
            "bio": self.bio,
            "photo_url": f"/static/{self.photo}" if self.photo else None,
            "is_founder": self.is_founder,
            "display_order": self.display_order,
        }


class GalleryImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False, default="events")
    image_path = db.Column(db.String(300), nullable=False)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "image_url": f"/static/{self.image_path}",
            "is_featured": self.is_featured,
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


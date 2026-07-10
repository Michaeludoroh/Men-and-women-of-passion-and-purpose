from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    TextAreaField,
    SelectField,
    FloatField,
    FileField,
    BooleanField,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional
from .constants import (
    PRAYER_CATEGORIES,
    CURRENCIES,
    PAYMENT_METHODS,
    GIVING_CATEGORIES,
    PARTNERSHIP_FREQUENCIES,
    ORG_LEVELS,
)


class RegisterForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class PrayerRequestForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    phone = StringField("Phone Number", validators=[Optional(), Length(max=30)])
    category = SelectField(
        "Prayer Category",
        choices=PRAYER_CATEGORIES,
        validators=[DataRequired()],
    )
    request = TextAreaField("Prayer Request", validators=[DataRequired(), Length(min=10)])
    consent_follow_up = BooleanField("I consent to follow-up contact regarding my prayer request")
    submit = SubmitField("Submit Prayer Request")


class ContactForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    subject = StringField("Subject", validators=[DataRequired(), Length(min=3, max=200)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(min=10)])
    submit = SubmitField("Send Message")


class SermonForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=10)])
    video_url = StringField("Video URL")
    category = SelectField(
        "Category",
        choices=[
            ("Faith", "Faith"),
            ("Prayer", "Prayer"),
            ("Leadership", "Leadership"),
            ("Purpose", "Purpose"),
            ("General", "General"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save Sermon")


class DonationForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    amount = FloatField("Amount", validators=[DataRequired(), NumberRange(min=1)])
    category = SelectField(
        "Giving Category",
        choices=[(k, v["label"]) for k, v in GIVING_CATEGORIES.items()],
        default="tithing",
        validators=[DataRequired()],
    )
    currency = SelectField("Currency", choices=CURRENCIES, default="NGN", validators=[DataRequired()])
    gateway = SelectField(
        "Payment Method",
        choices=PAYMENT_METHODS,
        default="flutterwave",
        validators=[DataRequired()],
    )
    submit = SubmitField("Proceed to Payment")


class PartnershipForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    phone = StringField("Phone Number", validators=[Optional(), Length(max=30)])
    amount = FloatField("Partnership Amount", validators=[DataRequired(), NumberRange(min=1)])
    currency = SelectField("Currency", choices=CURRENCIES, default="NGN", validators=[DataRequired()])
    frequency = SelectField(
        "Partnership Frequency",
        choices=PARTNERSHIP_FREQUENCIES,
        validators=[DataRequired()],
    )
    payment_method = SelectField(
        "Payment Method",
        choices=PAYMENT_METHODS,
        validators=[DataRequired()],
    )
    submit = SubmitField("Become a Partner")


class ReminderSettingsForm(FlaskForm):
    email_reminders_enabled = BooleanField("Enable Email Reminders")
    sms_reminders_enabled = BooleanField("Enable SMS Reminders")
    reminder_days_before = SelectField(
        "Send Reminder Days Before Due",
        choices=[("1", "1 Day"), ("2", "2 Days"), ("3", "3 Days"), ("7", "7 Days")],
        default="1",
        validators=[DataRequired()],
    )
    submit = SubmitField("Save Reminder Settings")


class CourseForm(FlaskForm):
    title = StringField("Course Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[DataRequired()])
    tutor = StringField("Tutor", validators=[DataRequired(), Length(max=120)])
    submit = SubmitField("Create Course")


class SchoolRegistrationForm(FlaskForm):
    submit = SubmitField("Register for School")


class AssignmentForm(FlaskForm):
    title = StringField("Assignment Title", validators=[DataRequired(), Length(max=200)])
    file = FileField("Upload Assignment File")
    submit = SubmitField("Upload Assignment")


class SubmissionForm(FlaskForm):
    answer_file = FileField("Upload Completed Assignment")
    submit = SubmitField("Submit Assignment")


class ProfileForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    submit = SubmitField("Update Profile")


class ApplicationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    program_type = SelectField(
        "Program Type",
        choices=[
            ("Empowerment", "Empowerment"),
            ("Leadership", "Leadership"),
            ("Scholarship", "Scholarship"),
            ("Outreach", "Outreach"),
        ],
        validators=[DataRequired()],
    )
    message = TextAreaField("Message", validators=[DataRequired(), Length(min=10)])
    submit = SubmitField("Submit Application")


class LeaderForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    role = StringField("Position / Role", validators=[DataRequired(), Length(max=120)])
    title = StringField("Title", validators=[Optional(), Length(max=200)])
    department = StringField("Department", validators=[Optional(), Length(max=120)])
    bio = TextAreaField("Biography", validators=[DataRequired(), Length(min=10)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    phone = StringField("Phone Number", validators=[Optional(), Length(max=30)])
    facebook_url = StringField("Facebook URL", validators=[Optional(), Length(max=500)])
    instagram_url = StringField("Instagram URL", validators=[Optional(), Length(max=500)])
    youtube_url = StringField("YouTube URL", validators=[Optional(), Length(max=500)])
    twitter_url = StringField("X / Twitter URL", validators=[Optional(), Length(max=500)])
    photo = FileField("Profile Image")
    video = FileField("Leader Video")
    remove_photo = BooleanField("Remove current profile image")
    remove_video = BooleanField("Remove current video")
    is_founder = SelectField(
        "Founder",
        choices=[("0", "No"), ("1", "Yes")],
        default="0",
        validators=[DataRequired()],
    )
    is_active = SelectField(
        "Status",
        choices=[("1", "Active"), ("0", "Inactive")],
        default="1",
        validators=[DataRequired()],
    )
    display_order = StringField("Display Order", default="0")
    org_level = SelectField(
        "Organization Level",
        choices=ORG_LEVELS,
        default="coordinator",
        validators=[DataRequired()],
    )
    submit = SubmitField("Save Changes")


class GalleryImageForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional()])
    category = SelectField(
        "Category",
        choices=[
            ("conferences", "Conferences"),
            ("empowerment", "Empowerment Projects"),
            ("anniversary", "Anniversary"),
            ("events", "Events"),
            ("outreach", "Outreach Programs"),
        ],
        validators=[DataRequired()],
    )
    media = FileField("Media File (Image or Video)")
    poster = FileField("Video Poster / Thumbnail (optional)")
    display_order = StringField("Display Order", default="0")
    is_featured = SelectField(
        "Featured",
        choices=[("0", "No"), ("1", "Yes")],
        default="0",
        validators=[DataRequired()],
    )
    is_published = SelectField(
        "Visibility",
        choices=[("1", "Published"), ("0", "Hidden")],
        default="1",
        validators=[DataRequired()],
    )
    submit = SubmitField("Save Media")


class EventForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=10)])
    venue = StringField("Venue", validators=[Optional(), Length(max=200)])
    location = StringField("Location", validators=[Optional(), Length(max=300)])
    start_date = StringField(
        "Start Date & Time",
        validators=[DataRequired()],
        render_kw={"type": "datetime-local"},
    )
    end_date = StringField(
        "End Date & Time",
        validators=[Optional()],
        render_kw={"type": "datetime-local"},
    )
    registration_link = StringField("Registration Link", validators=[Optional(), Length(max=500)])
    banner_image = FileField("Banner Image")
    is_featured = SelectField(
        "Featured",
        choices=[("0", "No"), ("1", "Yes")],
        default="0",
        validators=[DataRequired()],
    )
    is_published = SelectField(
        "Published",
        choices=[("0", "Draft"), ("1", "Published")],
        default="0",
        validators=[DataRequired()],
    )
    submit = SubmitField("Save Event")


class WebsiteSettingsForm(FlaskForm):
    about_intro = TextAreaField(
        "About Page Intro",
        validators=[DataRequired(), Length(min=10, max=2000)],
        description="Hero paragraph on the About page.",
    )
    tagline = TextAreaField(
        "Homepage Tagline",
        validators=[DataRequired(), Length(min=10, max=500)],
    )
    mission = TextAreaField(
        "Mission",
        validators=[DataRequired(), Length(min=10, max=3000)],
        description="One bullet per line for the About page; also shown on the homepage.",
    )
    vision = TextAreaField("Vision", validators=[DataRequired(), Length(min=10, max=2000)])
    ministry_email = StringField("Public Email", validators=[DataRequired(), Email(), Length(max=255)])
    ministry_phone = StringField("Public Phone", validators=[Optional(), Length(max=50)])
    ministry_address = TextAreaField("Public Address", validators=[Optional(), Length(max=500)])
    app_store_url = StringField("App Store URL", validators=[Optional(), Length(max=500)])
    play_store_url = StringField("Google Play URL", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Save Website Settings")

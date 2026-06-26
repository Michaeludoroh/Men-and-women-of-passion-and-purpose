from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    TextAreaField,
    SelectField,
    FloatField,
    FileField,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional


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
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    request = TextAreaField("Prayer Request", validators=[DataRequired(), Length(min=10)])
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
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    amount = FloatField("Amount", validators=[DataRequired(), NumberRange(min=1)])
    gateway = SelectField("Gateway", choices=[('paystack', 'Paystack'), ('flutterwave', 'Flutterwave')], default='paystack', validators=[DataRequired()])
    submit = SubmitField("Proceed to Payment")


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
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    role = StringField("Role", validators=[DataRequired(), Length(max=120)])
    title = StringField("Title", validators=[Length(max=200)])
    bio = TextAreaField("Bio", validators=[DataRequired(), Length(min=10)])
    photo = FileField("Photo")
    is_founder = SelectField(
        "Founder",
        choices=[("0", "No"), ("1", "Yes")],
        default="0",
        validators=[DataRequired()],
    )
    display_order = StringField("Display Order", default="0")
    submit = SubmitField("Save Leader")


class GalleryImageForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description")
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
    image = FileField("Image")
    is_featured = SelectField(
        "Featured",
        choices=[("0", "No"), ("1", "Yes")],
        default="0",
        validators=[DataRequired()],
    )
    submit = SubmitField("Upload Image")


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

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
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange


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


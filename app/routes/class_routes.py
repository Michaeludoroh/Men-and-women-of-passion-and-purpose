from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models import Course, Assignment, Submission, CourseEnrollment
from ..forms import CourseForm, AssignmentForm, SubmissionForm, SchoolRegistrationForm
from ..extensions import db

classes_bp = Blueprint("classes", __name__)

SCHOOL_CATALOG = [
    ("School of Purpose", "Mondays by 7:00 PM"),
    ("School of Healing", "Tuesdays by 7:00 PM"),
    ("School of the Word", "Wednesdays by 7:00 PM"),
    ("School of the Spirit", "Saturdays by 7:00 PM"),
]


def ensure_school_catalog():
    catalog_titles = [title for title, _ in SCHOOL_CATALOG]
    for title, schedule in SCHOOL_CATALOG:
        course = Course.query.filter_by(title=title).first()
        if not course:
            course = Course(title=title, description=schedule, tutor="")
            db.session.add(course)
        else:
            course.description = schedule
            course.tutor = ""
    db.session.commit()
    order_map = {title: index for index, title in enumerate(catalog_titles)}
    courses = Course.query.filter(Course.title.in_(catalog_titles)).all()
    courses.sort(key=lambda course: order_map.get(course.title, 999))
    return courses


@classes_bp.route("/", methods=["GET", "POST"])
@login_required
def classes_home():
    form = CourseForm()
    if current_user.role == "admin" and form.validate_on_submit():
        course = Course(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            tutor=form.tutor.data.strip(),
        )
        db.session.add(course)
        db.session.commit()
        flash("Course created successfully.", "success")
        return redirect(url_for("classes.classes_home"))

    courses = ensure_school_catalog()
    reg_form = SchoolRegistrationForm()

    return render_template("classes.html", courses=courses, form=form, reg_form=reg_form)


@classes_bp.route("/<int:course_id>", methods=["GET", "POST"])
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    form = SchoolRegistrationForm()
    if form.validate_on_submit():
        if current_user.is_enrolled(course.id):
            flash("You are already enrolled in this course.", "warning")
        else:
            enrollment = CourseEnrollment(user_id=current_user.id, course_id=course.id)
            db.session.add(enrollment)
            db.session.commit()
            flash("Successfully enrolled in {}!".format(course.title), "success")
        return redirect(url_for("classes.course_detail", course_id=course_id))

    enrolled = current_user.is_enrolled(course.id) if current_user.is_authenticated else False
    return render_template("course_detail.html", course=course, form=form, enrolled=enrolled)


@classes_bp.route("/<int:course_id>/assignment", methods=["GET", "POST"])
@login_required
def add_assignment(course_id):
    course = Course.query.get_or_404(course_id)
    if current_user.role != "admin":
        flash("Only admins/tutors can upload assignments.", "danger")
        return redirect(url_for("classes.classes_home"))

    form = AssignmentForm()
    if form.validate_on_submit():
        assignment = Assignment(
            course_id=course.id,
            title=form.title.data.strip(),
            file=form.file.data.filename if form.file.data else None,
        )
        db.session.add(assignment)
        db.session.commit()
        flash("Assignment uploaded successfully.", "success")
        return redirect(url_for("classes.classes_home"))

    return render_template("classes.html", courses=Course.query.all(), form=CourseForm(), assignment_form=form)


@classes_bp.route("/assignment/<int:assignment_id>/submit", methods=["POST"])
@login_required
def submit_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    form = SubmissionForm()
    if form.validate_on_submit():
        submission = Submission(
            student_id=current_user.id,
            assignment_id=assignment.id,
            answer_file=form.answer_file.data.filename if form.answer_file.data else None,
        )
        db.session.add(submission)
        db.session.commit()
        flash("Assignment submitted successfully.", "success")
    else:
        flash("Submission failed. Please upload a file and try again.", "danger")

    return redirect(url_for("classes.classes_home"))


@classes_bp.route("/register_school/<int:course_id>", methods=["POST"])
@login_required
def register_school(course_id):
    form = SchoolRegistrationForm()
    if form.validate_on_submit():
        course = Course.query.get_or_404(course_id)
        if current_user.is_enrolled(course.id):
            flash("Already enrolled.", "warning")
        else:
            enrollment = CourseEnrollment(user_id=current_user.id, course_id=course.id)
            db.session.add(enrollment)
            db.session.commit()
            flash(f"Enrolled in {course.title}!", "success")
        return redirect(url_for("classes.classes_home"))
    flash("Enrollment failed.", "danger")
    return redirect(url_for("classes.classes_home"))


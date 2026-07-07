from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user
from ..forms import RegisterForm, LoginForm
from ..models import User
from ..extensions import db
from ..utils.security import is_safe_redirect_url

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower()).first()
        if existing:
            current_app.logger.warning(
                "Registration attempt with existing email=%s ip=%s ua=%s",
                form.email.data.lower().strip(),
                request.remote_addr,
                request.headers.get("User-Agent", "unknown"),
            )
            flash("Email already exists. Please login.", "warning")
            return redirect(url_for("auth.login"))

        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            role="member",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        current_app.logger.info(
            "Registration success user_id=%s email=%s ip=%s ua=%s",
            user.id,
            user.email,
            request.remote_addr,
            request.headers.get("User-Agent", "unknown"),
        )
        flash("Registration successful. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        next_page = request.args.get("next")
        if next_page and is_safe_redirect_url(next_page):
            return redirect(next_page)
        if current_user.role == "admin":
            return redirect(url_for("admin.admin_dashboard"))
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            session.permanent = True
            login_user(user)
            current_app.logger.info(
                "Login success user_id=%s email=%s ip=%s ua=%s",
                user.id,
                user.email,
                request.remote_addr,
                request.headers.get("User-Agent", "unknown"),
            )
            next_page = request.args.get("next")
            flash("Welcome back!", "success")
            if next_page and is_safe_redirect_url(next_page):
                return redirect(next_page)
            if user.role == "admin":
                return redirect(url_for("admin.admin_dashboard"))
            return redirect(url_for("main.dashboard"))

        current_app.logger.warning(
            "Login failed email=%s ip=%s ua=%s",
            form.email.data.lower().strip(),
            request.remote_addr,
            request.headers.get("User-Agent", "unknown"),
        )
        flash("Invalid email or password.", "danger")

    return render_template("login.html", form=form)


@auth.route("/logout")
def logout():
    if current_user.is_authenticated:
        current_app.logger.info(
            "Logout user_id=%s email=%s ip=%s ua=%s",
            current_user.id,
            current_user.email,
            request.remote_addr,
            request.headers.get("User-Agent", "unknown"),
        )
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))

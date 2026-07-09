from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from flask_login import current_user
from ..extensions import db
from ..forms import PrayerRequestForm
from ..models import PrayerRequest
from ..services.notifications import notify_ministry_prayer_request, send_prayer_confirmation

prayer = Blueprint("prayer", __name__)


@prayer.route("/prayer_request", methods=["GET", "POST"])
@prayer.route("/", methods=["GET", "POST"])
def prayer_request():
    form = PrayerRequestForm()
    if form.validate_on_submit():
        prayer_req = PrayerRequest(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            phone=(form.phone.data or "").strip() or None,
            category=form.category.data,
            request=form.request.data.strip(),
            consent_follow_up=form.consent_follow_up.data,
        )
        db.session.add(prayer_req)
        db.session.commit()

        notify_ministry_prayer_request(prayer_req)
        send_prayer_confirmation(prayer_req)

        current_app.logger.info(
            "New prayer request from %s (name: %s, category: %s)",
            prayer_req.email,
            prayer_req.name,
            prayer_req.category,
        )
        flash(
            "Your prayer request has been received! Our prayer team will stand with you in faith.",
            "success",
        )
        return redirect(url_for("prayer.prayer_request"))

    return render_template("prayer.html", form=form)

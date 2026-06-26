from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from ..extensions import db
from ..forms import PrayerRequestForm
from ..models import PrayerRequest

prayer = Blueprint("prayer", __name__)


@prayer.route("/prayer_request", methods=["GET", "POST"])
def prayer_request():
    form = PrayerRequestForm()
    if form.validate_on_submit():
        prayer_req = PrayerRequest(
            name=form.name.data.strip(),
            email=form.email.data.strip(),
            request=form.request.data.strip(),
        )
        db.session.add(prayer_req)
        db.session.commit()

        current_app.logger.info(
            "New prayer request from %s (name: %s)",
            prayer_req.email,
            prayer_req.name,
        )
        flash(
            "Your prayer request has been received! Our prayer team will stand with you in faith.",
            "success",
        )
        return redirect(url_for("prayer.prayer_request"))

    return render_template("prayer.html", form=form)

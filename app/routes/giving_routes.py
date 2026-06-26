import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request
from ..forms import DonationForm
from ..models import Donation
from ..extensions import db
from ..services.payment import initialize_paystack_payment, initialize_flutterwave_payment, verify_payment

giving = Blueprint("giving", __name__)


@giving.route("/", methods=["GET", "POST"])
def giving_page():
    form = DonationForm()
    if form.validate_on_submit():
        reference = f"mwp-{uuid.uuid4().hex[:12]}"
        gateway = form.gateway.data
        if gateway == 'paystack':
            result = initialize_paystack_payment(
                email=form.email.data.strip().lower(),
                amount=form.amount.data,
                reference=reference,
            )
        else:
            result = initialize_flutterwave_payment(
                email=form.email.data.strip().lower(),
                amount=form.amount.data,
                reference=reference,
            )

        if result.get("status"):
            auth_url = result.get("data", {}).get("authorization_url")
            donation = Donation(
                name=form.name.data.strip(),
                email=form.email.data.strip().lower(),
                amount=form.amount.data,
                payment_reference=reference,
                gateway=gateway,
            )
            db.session.add(donation)
            db.session.commit()

            if auth_url:
                return redirect(auth_url)

            flash("Payment initialized, but no authorization URL returned.", "warning")
            return redirect(url_for("giving.giving_page"))

        flash(result.get("message", "Unable to initialize payment."), "danger")

    return render_template("giving.html", form=form)


@giving.route("/success")
def payment_success():
    reference = request.args.get("reference", "") or request.args.get("tx_ref", "")
    donation = Donation.query.filter_by(payment_reference=reference).first()
    if donation:
        is_verified = verify_payment(donation.gateway, reference)
        if is_verified:
            flash("Payment successfully verified!", "success")
        else:
            flash("Payment not verified. Contact support.", "warning")
    return render_template("giving_success.html", donation=donation, reference=reference)


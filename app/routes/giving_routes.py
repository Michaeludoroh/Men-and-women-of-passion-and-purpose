import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from ..forms import DonationForm
from ..models import Donation
from ..extensions import db
from ..constants import GIVING_CATEGORIES, CURRENCY_SYMBOLS, PAYMENT_STATUS_VERIFIED, PAYMENT_STATUS_MANUAL, PAYMENT_STATUS_PENDING
from ..services.payment import (
    initialize_paystack_payment,
    initialize_flutterwave_payment,
    initialize_paypal_payment,
    verify_payment,
    get_manual_payment_instructions,
)
from ..services.notifications import send_donation_receipt

giving = Blueprint("giving", __name__)


def _init_payment(gateway, email, amount, reference, currency):
    if gateway == "paystack":
        return initialize_paystack_payment(email, amount, reference, currency)
    if gateway == "flutterwave":
        return initialize_flutterwave_payment(email, amount, reference, currency)
    if gateway == "paypal":
        return initialize_paypal_payment(email, amount, reference, currency)
    return {"status": False, "message": "Unsupported payment method."}


@giving.route("/", methods=["GET", "POST"])
def giving_page():
    form = DonationForm()
    selected_category = request.args.get("category", form.category.data or "offering")

    if request.method == "GET" and selected_category in GIVING_CATEGORIES:
        form.category.data = selected_category

    if form.validate_on_submit():
        reference = f"mwp-{uuid.uuid4().hex[:12]}"
        gateway = form.gateway.data
        currency = form.currency.data
        email = form.email.data.strip().lower()

        if gateway in ("zelle", "cashapp"):
            donation = Donation(
                user_id=current_user.id if current_user.is_authenticated else None,
                name=form.name.data.strip(),
                email=email,
                amount=form.amount.data,
                currency=currency,
                category=form.category.data,
                payment_reference=reference,
                gateway=gateway,
                payment_status=PAYMENT_STATUS_MANUAL,
            )
            db.session.add(donation)
            db.session.commit()
            flash("Your giving pledge has been recorded. Please complete the transfer using the instructions below.", "success")
            return redirect(url_for("giving.manual_payment", reference=reference))

        result = _init_payment(gateway, email, form.amount.data, reference, currency)

        if result.get("status"):
            auth_url = result.get("data", {}).get("authorization_url")
            donation = Donation(
                user_id=current_user.id if current_user.is_authenticated else None,
                name=form.name.data.strip(),
                email=email,
                amount=form.amount.data,
                currency=currency,
                category=form.category.data,
                payment_reference=reference,
                gateway=gateway,
                payment_status=PAYMENT_STATUS_PENDING,
            )
            db.session.add(donation)
            db.session.commit()

            if auth_url:
                return redirect(auth_url)

            flash("Payment initialized, but no authorization URL returned.", "warning")
            return redirect(url_for("giving.giving_page"))

        flash(result.get("message", "Unable to initialize payment."), "danger")

    donation_history = []
    if current_user.is_authenticated:
        donation_history = (
            Donation.query.filter_by(email=current_user.email)
            .order_by(Donation.created_at.desc())
            .limit(20)
            .all()
        )

    return render_template(
        "giving.html",
        form=form,
        categories=GIVING_CATEGORIES,
        currency_symbols=CURRENCY_SYMBOLS,
        donation_history=donation_history,
        selected_category=selected_category,
    )


@giving.route("/manual/<reference>")
def manual_payment(reference):
    donation = Donation.query.filter_by(payment_reference=reference).first_or_404()
    instructions = get_manual_payment_instructions(donation.gateway)
    return render_template(
        "giving_manual.html",
        donation=donation,
        instructions=instructions,
        currency_symbols=CURRENCY_SYMBOLS,
    )


@giving.route("/success")
def payment_success():
    reference = request.args.get("reference", "") or request.args.get("tx_ref", "")
    donation = Donation.query.filter_by(payment_reference=reference).first()
    if donation:
        is_verified = verify_payment(donation.gateway, reference)
        if is_verified:
            donation.payment_status = PAYMENT_STATUS_VERIFIED
            donation.verified_at = datetime.utcnow()
            db.session.commit()
            send_donation_receipt(donation)
            flash("Payment successfully verified! Thank you for your gift.", "success")
        else:
            flash("Payment not verified. Contact support if you completed payment.", "warning")
    return render_template("giving_success.html", donation=donation, reference=reference)


@giving.route("/history")
@login_required
def donation_history():
    donations = (
        Donation.query.filter_by(email=current_user.email)
        .order_by(Donation.created_at.desc())
        .all()
    )
    return render_template(
        "giving_history.html",
        donations=donations,
        currency_symbols=CURRENCY_SYMBOLS,
        categories=GIVING_CATEGORIES,
    )

import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from ..forms import PartnershipForm
from ..models import Partnership, PartnershipPayment
from ..extensions import db
from ..constants import (
    CURRENCY_SYMBOLS,
    PARTNERSHIP_FREQUENCIES,
    PAYMENT_METHODS,
    PARTNERSHIP_STATUS_ACTIVE,
    PARTNERSHIP_STATUS_PAUSED,
    PARTNERSHIP_STATUS_CANCELLED,
    PAYMENT_STATUS_PENDING,
    PAYMENT_STATUS_MANUAL,
)
from ..services.payment import (
    initialize_paystack_payment,
    initialize_flutterwave_payment,
    initialize_paypal_payment,
    get_manual_payment_instructions,
)
from ..services.reminders import initialize_partnership_schedule, record_partnership_payment, notify_payment_success
from ..services.notifications import notify_ministry_partnership

partnership_bp = Blueprint("partnership", __name__)


def _init_payment(gateway, email, amount, reference, currency):
    if gateway == "paystack":
        return initialize_paystack_payment(email, amount, reference, currency)
    if gateway == "flutterwave":
        return initialize_flutterwave_payment(email, amount, reference, currency, "partnership.partnership_success")
    if gateway == "paypal":
        return initialize_paypal_payment(email, amount, reference, currency, "partnership.partnership_success")
    return {"status": False, "message": "Unsupported payment method."}


@partnership_bp.route("/", methods=["GET", "POST"])
def partnership_page():
    form = PartnershipForm()
    if current_user.is_authenticated:
        form.name.data = form.name.data or current_user.name
        form.email.data = form.email.data or current_user.email

    if form.validate_on_submit():
        reference = f"mwp-p-{uuid.uuid4().hex[:12]}"
        email = form.email.data.strip().lower()
        method = form.payment_method.data

        partnership = Partnership(
            user_id=current_user.id if current_user.is_authenticated else None,
            name=form.name.data.strip(),
            email=email,
            phone=(form.phone.data or "").strip() or None,
            amount=form.amount.data,
            currency=form.currency.data,
            frequency=form.frequency.data,
            payment_method=method,
            status=PARTNERSHIP_STATUS_ACTIVE,
        )
        db.session.add(partnership)
        db.session.commit()
        initialize_partnership_schedule(partnership)
        notify_ministry_partnership(partnership)

        if method in ("zelle", "cashapp"):
            payment = PartnershipPayment(
                partnership_id=partnership.id,
                amount=partnership.amount,
                currency=partnership.currency,
                payment_reference=reference,
                gateway=method,
                status=PAYMENT_STATUS_MANUAL,
            )
            db.session.add(payment)
            db.session.commit()
            flash("Partnership registered! Complete your first payment using the instructions provided.", "success")
            return redirect(url_for("partnership.manual_payment", partnership_id=partnership.id))

        result = _init_payment(method, email, form.amount.data, reference, form.currency.data)
        if result.get("status"):
            auth_url = result.get("data", {}).get("authorization_url")
            payment = PartnershipPayment(
                partnership_id=partnership.id,
                amount=partnership.amount,
                currency=partnership.currency,
                payment_reference=reference,
                gateway=method,
                status=PAYMENT_STATUS_PENDING,
            )
            db.session.add(payment)
            db.session.commit()
            if auth_url:
                return redirect(auth_url)
            flash("Payment initialized but no redirect URL returned.", "warning")
            return redirect(url_for("partnership.manage"))

        flash(result.get("message", "Unable to initialize payment."), "danger")

    user_partnerships = []
    if current_user.is_authenticated:
        user_partnerships = (
            Partnership.query.filter_by(email=current_user.email)
            .order_by(Partnership.created_at.desc())
            .all()
        )

    return render_template(
        "partnership.html",
        form=form,
        currency_symbols=CURRENCY_SYMBOLS,
        frequencies=PARTNERSHIP_FREQUENCIES,
        payment_methods=PAYMENT_METHODS,
        user_partnerships=user_partnerships,
    )


@partnership_bp.route("/manual/<int:partnership_id>")
def manual_payment(partnership_id):
    partnership = Partnership.query.get_or_404(partnership_id)
    instructions = get_manual_payment_instructions(partnership.payment_method)
    return render_template(
        "partnership_manual.html",
        partnership=partnership,
        instructions=instructions,
        currency_symbols=CURRENCY_SYMBOLS,
    )


@partnership_bp.route("/success")
def partnership_success():
    reference = request.args.get("reference", "") or request.args.get("tx_ref", "")
    payment = PartnershipPayment.query.filter_by(payment_reference=reference).first()
    if payment:
        from datetime import datetime
        from ..constants import PAYMENT_STATUS_VERIFIED
        from ..services.payment import verify_payment

        if verify_payment(payment.gateway, reference):
            payment.status = PAYMENT_STATUS_VERIFIED
            payment.paid_at = datetime.utcnow()
            partnership = payment.partnership
            partnership.last_payment_date = datetime.utcnow()
            db.session.commit()
            notify_payment_success(partnership, payment)
            flash("Partnership payment verified! Thank you for your faithfulness.", "success")
        else:
            flash("Payment not verified. Contact support if you completed payment.", "warning")
    return render_template("partnership_success.html", payment=payment, reference=reference)


@partnership_bp.route("/manage")
@login_required
def manage():
    partnerships = (
        Partnership.query.filter_by(email=current_user.email)
        .order_by(Partnership.created_at.desc())
        .all()
    )
    return render_template(
        "partnership_manage.html",
        partnerships=partnerships,
        currency_symbols=CURRENCY_SYMBOLS,
        frequencies=dict(PARTNERSHIP_FREQUENCIES),
    )


@partnership_bp.route("/<int:partnership_id>/pause", methods=["POST"])
@login_required
def pause_partnership(partnership_id):
    partnership = Partnership.query.filter_by(id=partnership_id, email=current_user.email).first_or_404()
    partnership.status = PARTNERSHIP_STATUS_PAUSED
    db.session.commit()
    flash("Partnership paused.", "info")
    return redirect(url_for("partnership.manage"))


@partnership_bp.route("/<int:partnership_id>/resume", methods=["POST"])
@login_required
def resume_partnership(partnership_id):
    partnership = Partnership.query.filter_by(id=partnership_id, email=current_user.email).first_or_404()
    partnership.status = PARTNERSHIP_STATUS_ACTIVE
    db.session.commit()
    flash("Partnership resumed.", "success")
    return redirect(url_for("partnership.manage"))


@partnership_bp.route("/<int:partnership_id>/cancel", methods=["POST"])
@login_required
def cancel_partnership(partnership_id):
    partnership = Partnership.query.filter_by(id=partnership_id, email=current_user.email).first_or_404()
    partnership.status = PARTNERSHIP_STATUS_CANCELLED
    db.session.commit()
    flash("Partnership cancelled.", "info")
    return redirect(url_for("partnership.manage"))

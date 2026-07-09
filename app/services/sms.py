"""SMS notification service (Twilio-compatible)."""

import requests
from flask import current_app


def _can_send_sms():
    return all([
        current_app.config.get("TWILIO_ACCOUNT_SID"),
        current_app.config.get("TWILIO_AUTH_TOKEN"),
        current_app.config.get("TWILIO_PHONE_NUMBER"),
    ])


def send_sms(to, message):
    if not _can_send_sms():
        current_app.logger.warning("SMS not configured; skipping SMS to %s", to)
        return False
    if not to:
        return False
    try:
        sid = current_app.config["TWILIO_ACCOUNT_SID"]
        token = current_app.config["TWILIO_AUTH_TOKEN"]
        from_number = current_app.config["TWILIO_PHONE_NUMBER"]
        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        response = requests.post(
            url,
            auth=(sid, token),
            data={"To": to, "From": from_number, "Body": message},
            timeout=20,
        )
        if response.status_code in (200, 201):
            return True
        current_app.logger.error("SMS failed: %s", response.text)
        return False
    except Exception as exc:
        current_app.logger.error("SMS error to %s: %s", to, exc)
        return False


def send_partnership_reminder_sms(partnership):
    message = (
        f"WOPP Ministry: Reminder — your {partnership.frequency} partnership "
        f"of {partnership.currency} {partnership.amount:,.2f} is due soon. "
        f"Thank you for your faithfulness!"
    )
    return send_sms(partnership.phone, message)


def send_partnership_success_sms(partnership, payment):
    message = (
        f"WOPP Ministry: Payment received — {payment.currency} {payment.amount:,.2f}. "
        f"Thank you, {partnership.name}!"
    )
    return send_sms(partnership.phone, message)


def send_partnership_missed_sms(partnership):
    message = (
        f"WOPP Ministry: We missed your scheduled {partnership.frequency} partnership "
        f"payment. Please contact us if you need assistance."
    )
    return send_sms(partnership.phone, message)

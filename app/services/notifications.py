"""Email notification service using Flask-Mail."""

from flask import current_app
from flask_mail import Message
from ..extensions import mail


def _can_send():
    return bool(current_app.config.get("MAIL_USERNAME"))


def send_email(to, subject, body, html=None):
    if not _can_send():
        current_app.logger.warning("Mail not configured; skipping email to %s: %s", to, subject)
        return False
    try:
        msg = Message(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            body=body,
            html=html,
        )
        mail.send(msg)
        return True
    except Exception as exc:
        current_app.logger.error("Failed to send email to %s: %s", to, exc)
        return False


def notify_ministry_prayer_request(prayer):
    ministry_email = current_app.config.get("MINISTRY_EMAIL", "")
    if not ministry_email:
        return False
    subject = f"New Prayer Request from {prayer.name}"
    body = (
        f"A new prayer request has been submitted.\n\n"
        f"Name: {prayer.name}\n"
        f"Email: {prayer.email}\n"
        f"Phone: {prayer.phone or 'Not provided'}\n"
        f"Category: {prayer.category}\n"
        f"Follow-up consent: {'Yes' if prayer.consent_follow_up else 'No'}\n\n"
        f"Request:\n{prayer.request}\n"
    )
    return send_email(ministry_email, subject, body)


def send_prayer_confirmation(prayer):
    subject = "Your Prayer Request Has Been Received — WOPP Ministry"
    body = (
        f"Dear {prayer.name},\n\n"
        f"Thank you for sharing your prayer need with us. Our intercessors are "
        f"standing with you in faith.\n\n"
        f"\"The effective, fervent prayer of a righteous man avails much.\" — James 5:16\n\n"
        f"Blessings,\nMen and Women of Passion and Purpose"
    )
    return send_email(prayer.email, subject, body)


def send_donation_receipt(donation):
    subject = "Thank You for Your Gift — WOPP Ministry"
    body = (
        f"Dear {donation.name},\n\n"
        f"Thank you for your generous gift of {donation.currency} {donation.amount:,.2f} "
        f"({donation.category.replace('_', ' ').title()}).\n\n"
        f"Reference: {donation.payment_reference}\n\n"
        f"Your seed is making a kingdom impact. May God bless you abundantly!\n\n"
        f"Blessings,\nMen and Women of Passion and Purpose"
    )
    return send_email(donation.email, subject, body)


def send_partnership_reminder(partnership):
    subject = "Partnership Reminder — WOPP Ministry"
    body = (
        f"Dear {partnership.name},\n\n"
        f"This is a friendly reminder that your partnership gift of "
        f"{partnership.currency} {partnership.amount:,.2f} ({partnership.frequency}) "
        f"is due soon.\n\n"
        f"Thank you for your faithful partnership in advancing the kingdom.\n\n"
        f"Blessings,\nMen and Women of Passion and Purpose"
    )
    return send_email(partnership.email, subject, body)


def send_partnership_payment_success(partnership, payment):
    subject = "Partnership Payment Received — WOPP Ministry"
    body = (
        f"Dear {partnership.name},\n\n"
        f"We have received your partnership payment of "
        f"{payment.currency} {payment.amount:,.2f}.\n\n"
        f"Reference: {payment.payment_reference or 'N/A'}\n\n"
        f"Thank you for your continued faithfulness!\n\n"
        f"Blessings,\nMen and Women of Passion and Purpose"
    )
    return send_email(partnership.email, subject, body)


def send_partnership_missed_payment(partnership):
    subject = "Missed Partnership Payment — WOPP Ministry"
    body = (
        f"Dear {partnership.name},\n\n"
        f"We noticed your scheduled partnership payment of "
        f"{partnership.currency} {partnership.amount:,.2f} ({partnership.frequency}) "
        f"was not received.\n\n"
        f"If you need assistance or wish to update your partnership, please contact us.\n\n"
        f"Blessings,\nMen and Women of Passion and Purpose"
    )
    return send_email(partnership.email, subject, body)


def notify_ministry_partnership(partnership):
    ministry_email = current_app.config.get("MINISTRY_EMAIL", "")
    if not ministry_email:
        return False
    subject = f"New Ministry Partner: {partnership.name}"
    body = (
        f"A new ministry partnership has been registered.\n\n"
        f"Name: {partnership.name}\n"
        f"Email: {partnership.email}\n"
        f"Phone: {partnership.phone or 'Not provided'}\n"
        f"Amount: {partnership.currency} {partnership.amount:,.2f}\n"
        f"Frequency: {partnership.frequency}\n"
        f"Payment Method: {partnership.payment_method}\n"
    )
    return send_email(ministry_email, subject, body)

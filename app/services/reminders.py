"""Partnership reminder scheduling and due-date calculations."""

from datetime import datetime, timedelta
from calendar import monthrange
from flask import current_app
from ..extensions import db
from ..models import Partnership, PartnershipPayment, ReminderSettings
from ..constants import PARTNERSHIP_STATUS_ACTIVE, PAYMENT_STATUS_VERIFIED
from .notifications import (
    send_partnership_reminder,
    send_partnership_payment_success,
    send_partnership_missed_payment,
)
from .sms import (
    send_partnership_reminder_sms,
    send_partnership_success_sms,
    send_partnership_missed_sms,
)


def _add_months(dt, months):
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    max_day = monthrange(year, month)[1]
    day = min(dt.day, max_day)
    return dt.replace(year=year, month=month, day=day)


def calculate_next_due_date(from_date, frequency):
    """Return the next due date based on partnership frequency."""
    if frequency == "daily":
        return from_date + timedelta(days=1)
    if frequency == "weekly":
        return from_date + timedelta(weeks=1)
    if frequency == "biweekly":
        return from_date + timedelta(weeks=2)
    if frequency == "monthly":
        return _add_months(from_date, 1)
    if frequency == "semi_monthly":
        return from_date + timedelta(days=15)
    if frequency == "quarterly":
        return _add_months(from_date, 3)
    if frequency == "annually":
        return _add_months(from_date, 12)
    return _add_months(from_date, 1)


def initialize_partnership_schedule(partnership):
    """Set initial next due date for a new partnership."""
    partnership.next_due_date = calculate_next_due_date(datetime.utcnow(), partnership.frequency)
    db.session.commit()


def record_partnership_payment(partnership, amount, currency, reference, gateway, status="verified"):
    """Record a partnership payment and advance the schedule."""
    payment = PartnershipPayment(
        partnership_id=partnership.id,
        amount=amount,
        currency=currency,
        payment_reference=reference,
        gateway=gateway,
        status=status,
        paid_at=datetime.utcnow() if status == PAYMENT_STATUS_VERIFIED else None,
    )
    db.session.add(payment)
    partnership.last_payment_date = datetime.utcnow()
    partnership.next_due_date = calculate_next_due_date(datetime.utcnow(), partnership.frequency)
    db.session.commit()
    return payment


def process_partnership_reminders():
    """Send due-date reminders, success confirmations, and missed payment notices."""
    settings = ReminderSettings.get_singleton()
    now = datetime.utcnow()
    sent_count = 0

    active_partnerships = Partnership.query.filter_by(status=PARTNERSHIP_STATUS_ACTIVE).all()

    for partnership in active_partnerships:
        if not partnership.next_due_date:
            initialize_partnership_schedule(partnership)
            continue

        days_until_due = (partnership.next_due_date - now).days
        days_overdue = -days_until_due

        # Upcoming reminder
        if 0 <= days_until_due <= settings.reminder_days_before:
            already_sent = (
                partnership.last_reminder_sent
                and partnership.last_reminder_sent.date() >= (now - timedelta(days=settings.reminder_days_before)).date()
            )
            if not already_sent:
                if settings.email_reminders_enabled:
                    send_partnership_reminder(partnership)
                if settings.sms_reminders_enabled and partnership.phone:
                    send_partnership_reminder_sms(partnership)
                partnership.last_reminder_sent = now
                db.session.commit()
                sent_count += 1
                current_app.logger.info("Reminder sent to partnership %s", partnership.email)

        # Missed payment (1 day overdue)
        elif days_overdue >= 1:
            recent_payment = (
                PartnershipPayment.query.filter_by(partnership_id=partnership.id)
                .filter(PartnershipPayment.paid_at >= partnership.next_due_date - timedelta(days=1))
                .first()
            )
            if not recent_payment:
                already_notified = (
                    partnership.last_reminder_sent
                    and partnership.last_reminder_sent >= partnership.next_due_date
                )
                if not already_notified:
                    if settings.email_reminders_enabled:
                        send_partnership_missed_payment(partnership)
                    if settings.sms_reminders_enabled and partnership.phone:
                        send_partnership_missed_sms(partnership)
                    partnership.last_reminder_sent = now
                    db.session.commit()
                    sent_count += 1
                    current_app.logger.info("Missed payment notice sent to %s", partnership.email)

    return sent_count


def notify_payment_success(partnership, payment):
    """Notify partner after successful payment."""
    settings = ReminderSettings.get_singleton()
    if settings.email_reminders_enabled:
        send_partnership_payment_success(partnership, payment)
    if settings.sms_reminders_enabled and partnership.phone:
        send_partnership_success_sms(partnership, payment)

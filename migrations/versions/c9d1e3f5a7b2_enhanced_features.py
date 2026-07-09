"""Enhanced features: prayer, giving, partnerships, org chart

Revision ID: c9d1e3f5a7b2
Revises: b7c2d4e6f8a0
Create Date: 2026-07-08 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c9d1e3f5a7b2"
down_revision = "b7c2d4e6f8a0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("prayer_request", schema=None) as batch_op:
        batch_op.add_column(sa.Column("phone", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("category", sa.String(length=50), server_default="other", nullable=False))
        batch_op.add_column(sa.Column("consent_follow_up", sa.Boolean(), server_default=sa.false(), nullable=True))
        batch_op.add_column(sa.Column("is_prayed_for", sa.Boolean(), server_default=sa.false(), nullable=True))
        batch_op.add_column(sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=True))

    with op.batch_alter_table("donation", schema=None) as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("currency", sa.String(length=10), server_default="NGN", nullable=False))
        batch_op.add_column(sa.Column("category", sa.String(length=50), server_default="offering", nullable=False))
        batch_op.add_column(sa.Column("payment_status", sa.String(length=20), server_default="pending", nullable=True))
        batch_op.add_column(sa.Column("verified_at", sa.DateTime(), nullable=True))
        batch_op.create_foreign_key("fk_donation_user_id", "user", ["user_id"], ["id"])

    with op.batch_alter_table("leader", schema=None) as batch_op:
        batch_op.add_column(sa.Column("org_level", sa.String(length=50), server_default="coordinator", nullable=True))

    op.create_table(
        "partnership",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), server_default="NGN", nullable=False),
        sa.Column("frequency", sa.String(length=30), server_default="monthly", nullable=False),
        sa.Column("payment_method", sa.String(length=30), server_default="flutterwave", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=True),
        sa.Column("next_due_date", sa.DateTime(), nullable=True),
        sa.Column("last_payment_date", sa.DateTime(), nullable=True),
        sa.Column("last_reminder_sent", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "partnership_payment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("partnership_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), server_default="NGN", nullable=False),
        sa.Column("payment_reference", sa.String(length=200), nullable=True),
        sa.Column("gateway", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["partnership_id"], ["partnership.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reminder_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email_reminders_enabled", sa.Boolean(), server_default=sa.true(), nullable=True),
        sa.Column("sms_reminders_enabled", sa.Boolean(), server_default=sa.false(), nullable=True),
        sa.Column("reminder_days_before", sa.Integer(), server_default="1", nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("reminder_settings")
    op.drop_table("partnership_payment")
    op.drop_table("partnership")

    with op.batch_alter_table("leader", schema=None) as batch_op:
        batch_op.drop_column("org_level")

    with op.batch_alter_table("donation", schema=None) as batch_op:
        batch_op.drop_constraint("fk_donation_user_id", type_="foreignkey")
        batch_op.drop_column("verified_at")
        batch_op.drop_column("payment_status")
        batch_op.drop_column("category")
        batch_op.drop_column("currency")
        batch_op.drop_column("user_id")

    with op.batch_alter_table("prayer_request", schema=None) as batch_op:
        batch_op.drop_column("is_archived")
        batch_op.drop_column("is_prayed_for")
        batch_op.drop_column("consent_follow_up")
        batch_op.drop_column("category")
        batch_op.drop_column("phone")

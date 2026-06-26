"""Initial schema baseline

Revision ID: f3a8b2c1d4e5
Revises:
Create Date: 2026-06-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f3a8b2c1d4e5"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_user_email"), ["email"], unique=True)

    op.create_table(
        "sermon",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("video_url", sa.String(length=500), nullable=True),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "prayer_request",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("request", sa.Text(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "contact_message",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "donation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("payment_reference", sa.String(length=200), nullable=False),
        sa.Column("gateway", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_reference"),
    )

    op.create_table(
        "application",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("program_type", sa.String(length=120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "leader",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("bio", sa.Text(), nullable=False),
        sa.Column("photo", sa.String(length=300), nullable=True),
        sa.Column("is_founder", sa.Boolean(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "gallery_image",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("image_path", sa.String(length=300), nullable=False),
        sa.Column("is_featured", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "course",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("tutor", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "assignment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("file", sa.String(length=300), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "course_enrollment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "course_id", name="unique_enrollment"),
    )

    op.create_table(
        "submission",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("answer_file", sa.String(length=300), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignment.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("venue", sa.String(length=200), nullable=True),
        sa.Column("location", sa.String(length=300), nullable=True),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("banner_image", sa.String(length=300), nullable=True),
        sa.Column("registration_link", sa.String(length=500), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_event_slug"), ["slug"], unique=True)


def downgrade():
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_event_slug"))
    op.drop_table("event")
    op.drop_table("submission")
    op.drop_table("course_enrollment")
    op.drop_table("assignment")
    op.drop_table("course")
    op.drop_table("gallery_image")
    op.drop_table("leader")
    op.drop_table("application")
    op.drop_table("donation")
    op.drop_table("contact_message")
    op.drop_table("prayer_request")
    op.drop_table("sermon")
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_email"))
    op.drop_table("user")

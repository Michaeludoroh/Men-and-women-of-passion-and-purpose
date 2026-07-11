"""Gallery external video + metadata fields

Revision ID: g4b7c9d1e3f6
Revises: f3a6b8c0d2e5
Create Date: 2026-07-11 06:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "g4b7c9d1e3f6"
down_revision = "f3a6b8c0d2e5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("gallery_image", schema=None) as batch_op:
        batch_op.alter_column(
            "image_path",
            existing_type=sa.String(length=300),
            nullable=True,
        )
        batch_op.add_column(sa.Column("event_name", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("external_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("embed_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("provider", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("provider_video_id", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("thumbnail_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("duration_seconds", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("mime_type", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("file_size", sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table("gallery_image", schema=None) as batch_op:
        batch_op.drop_column("file_size")
        batch_op.drop_column("mime_type")
        batch_op.drop_column("duration_seconds")
        batch_op.drop_column("thumbnail_url")
        batch_op.drop_column("provider_video_id")
        batch_op.drop_column("provider")
        batch_op.drop_column("embed_url")
        batch_op.drop_column("external_url")
        batch_op.drop_column("event_name")
        # Leave image_path nullable=True on downgrade for safety with external rows

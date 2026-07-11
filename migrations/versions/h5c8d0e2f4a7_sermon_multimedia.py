"""Sermon multimedia fields — independent from Gallery.

Revision ID: h5c8d0e2f4a7
Revises: g4b7c9d1e3f6
Create Date: 2026-07-11 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "h5c8d0e2f4a7"
down_revision = "g4b7c9d1e3f6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sermon", schema=None) as batch_op:
        batch_op.add_column(sa.Column("media_type", sa.String(length=20), nullable=False, server_default="image"))
        batch_op.add_column(sa.Column("media_path", sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column("poster_path", sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column("external_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("embed_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("provider", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("provider_video_id", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("thumbnail_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("duration_seconds", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("mime_type", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("file_size", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("sermon", schema=None) as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("file_size")
        batch_op.drop_column("mime_type")
        batch_op.drop_column("duration_seconds")
        batch_op.drop_column("thumbnail_url")
        batch_op.drop_column("provider_video_id")
        batch_op.drop_column("provider")
        batch_op.drop_column("embed_url")
        batch_op.drop_column("external_url")
        batch_op.drop_column("poster_path")
        batch_op.drop_column("media_path")
        batch_op.drop_column("media_type")

"""Add leader contact, social, and status fields

Revision ID: e2f5a7b9c1d4
Revises: d1e4f6a8b0c3
Create Date: 2026-07-10 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e2f5a7b9c1d4"
down_revision = "d1e4f6a8b0c3"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("leader", schema=None) as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("phone", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("department", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("facebook_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("instagram_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("youtube_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("twitter_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("leader", schema=None) as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("is_active")
        batch_op.drop_column("twitter_url")
        batch_op.drop_column("youtube_url")
        batch_op.drop_column("instagram_url")
        batch_op.drop_column("facebook_url")
        batch_op.drop_column("department")
        batch_op.drop_column("phone")
        batch_op.drop_column("email")

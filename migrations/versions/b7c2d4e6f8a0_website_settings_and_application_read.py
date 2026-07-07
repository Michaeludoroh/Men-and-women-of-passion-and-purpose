"""Website settings table and application read flag

Revision ID: b7c2d4e6f8a0
Revises: f3a8b2c1d4e5
Create Date: 2026-07-07 19:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b7c2d4e6f8a0"
down_revision = "f3a8b2c1d4e5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "website_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("about_intro", sa.Text(), nullable=True),
        sa.Column("mission", sa.Text(), nullable=True),
        sa.Column("vision", sa.Text(), nullable=True),
        sa.Column("tagline", sa.Text(), nullable=True),
        sa.Column("ministry_email", sa.String(length=255), nullable=True),
        sa.Column("ministry_phone", sa.String(length=50), nullable=True),
        sa.Column("ministry_address", sa.Text(), nullable=True),
        sa.Column("app_store_url", sa.String(length=500), nullable=True),
        sa.Column("play_store_url", sa.String(length=500), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("application", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_read", sa.Boolean(), nullable=True, server_default=sa.false()))


def downgrade():
    with op.batch_alter_table("application", schema=None) as batch_op:
        batch_op.drop_column("is_read")

    op.drop_table("website_settings")

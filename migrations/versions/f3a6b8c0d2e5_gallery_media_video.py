"""Gallery media type, poster, display order, and visibility

Revision ID: f3a6b8c0d2e5
Revises: e2f5a7b9c1d4
Create Date: 2026-07-10 00:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f3a6b8c0d2e5"
down_revision = "e2f5a7b9c1d4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("gallery_image", schema=None) as batch_op:
        batch_op.add_column(sa.Column("media_type", sa.String(length=20), server_default="image", nullable=False))
        batch_op.add_column(sa.Column("poster_path", sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column("display_order", sa.Integer(), server_default="0", nullable=True))
        batch_op.add_column(sa.Column("is_published", sa.Boolean(), server_default=sa.true(), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("gallery_image", schema=None) as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("is_published")
        batch_op.drop_column("display_order")
        batch_op.drop_column("poster_path")
        batch_op.drop_column("media_type")

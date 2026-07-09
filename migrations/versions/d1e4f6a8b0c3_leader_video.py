"""Add leader video column

Revision ID: d1e4f6a8b0c3
Revises: c9d1e3f5a7b2
Create Date: 2026-07-09 23:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "d1e4f6a8b0c3"
down_revision = "c9d1e3f5a7b2"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("leader", schema=None) as batch_op:
        batch_op.add_column(sa.Column("video", sa.String(length=300), nullable=True))


def downgrade():
    with op.batch_alter_table("leader", schema=None) as batch_op:
        batch_op.drop_column("video")

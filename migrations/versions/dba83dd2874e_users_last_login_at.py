"""users last_login_at

Revision ID: dba83dd2874e
Revises: 2223765f89a7
Create Date: 2026-11-24 10:43:06.348411

Issue #32. Waktu login berhasil terakhir (diisi routes/auth.py); NULL untuk user yang belum login.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dba83dd2874e'
down_revision = '2223765f89a7'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("users", "last_login_at")

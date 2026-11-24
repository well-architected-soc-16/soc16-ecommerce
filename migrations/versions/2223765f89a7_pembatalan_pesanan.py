"""pembatalan pesanan

Revision ID: 2223765f89a7
Revises: 7937be7831c9
Create Date: 2026-11-24 10:43:05.624824

Issue #32. Pembatalan pesanan: waktu dan alasan (NULL untuk pesanan yang tidak dibatalkan).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2223765f89a7'
down_revision = '7937be7831c9'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("orders", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("orders", sa.Column("cancel_reason", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("orders", "cancel_reason")
    op.drop_column("orders", "cancelled_at")

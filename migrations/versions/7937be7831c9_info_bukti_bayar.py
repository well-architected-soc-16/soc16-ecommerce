"""info bukti bayar

Revision ID: 7937be7831c9
Revises: 7d41337a36aa
Create Date: 2026-11-24 10:43:04.832353

Issue #32. Info file bukti bayar untuk tampilan admin: nama asli (sudah disanitasi, tidak dipakai
sebagai path), MIME hasil deteksi, ukuran byte (CHECK > 0). Semua NULL untuk baris lama.
CHECK ditambahkan manual (autogenerate tidak mendeteksinya).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7937be7831c9'
down_revision = '7d41337a36aa'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("payments", sa.Column("proof_original_name", sa.String(length=255), nullable=True))
    op.add_column("payments", sa.Column("proof_mime", sa.String(length=50), nullable=True))
    op.add_column("payments", sa.Column("proof_size", sa.Integer(), nullable=True))
    op.create_check_constraint(op.f("ck_payments_proof_size"), "payments", "proof_size > 0")


def downgrade():
    op.drop_constraint(op.f("ck_payments_proof_size"), "payments", type_="check")
    op.drop_column("payments", "proof_size")
    op.drop_column("payments", "proof_mime")
    op.drop_column("payments", "proof_original_name")

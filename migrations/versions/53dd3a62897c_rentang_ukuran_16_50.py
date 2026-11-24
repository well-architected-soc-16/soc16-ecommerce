"""rentang ukuran 16-50

Revision ID: 53dd3a62897c
Revises: e11f2068a0a1
Create Date: 2026-11-24 10:43:03.237408

Issue #32. Rentang ukuran EU diperluas 30-50 -> 16-50 (sepatu anak), tetap bulat atau .5.
CHECK ck_product_sizes_size di-drop lalu dibuat ulang (autogenerate tidak mendeteksi CHECK).
Rentang baru mencakup yang lama, jadi upgrade tidak perlu mengubah data.

Downgrade gagal jelas (tanpa menghapus apa pun) bila sudah ada ukuran di bawah 30.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '53dd3a62897c'
down_revision = 'e11f2068a0a1'
branch_labels = None
depends_on = None

SIZE_REGEX_NEW = r"^(1[6-9]|[2-4][0-9])(\.5)?$|^50$"
SIZE_REGEX_OLD = r"^(3[0-9]|4[0-9])(\.5)?$|^50$"


def upgrade():
    op.drop_constraint(op.f("ck_product_sizes_size"), "product_sizes", type_="check")
    op.create_check_constraint(op.f("ck_product_sizes_size"), "product_sizes", f"size ~ '{SIZE_REGEX_NEW}'")


def downgrade():
    bind = op.get_bind()
    invalid = bind.execute(
        sa.text("SELECT id, size FROM product_sizes WHERE size !~ :pola ORDER BY id"),
        {"pola": SIZE_REGEX_OLD},
    ).all()
    if invalid:
        raise RuntimeError(
            "Ada ukuran di luar rentang lama 30-50, downgrade dibatalkan (ubah/hapus manual dulu): "
            + ", ".join(f"id={row.id} size={row.size!r}" for row in invalid)
        )
    op.drop_constraint(op.f("ck_product_sizes_size"), "product_sizes", type_="check")
    op.create_check_constraint(op.f("ck_product_sizes_size"), "product_sizes", f"size ~ '{SIZE_REGEX_OLD}'")

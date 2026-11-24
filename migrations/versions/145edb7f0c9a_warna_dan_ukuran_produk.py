"""warna dan ukuran produk

Revision ID: 145edb7f0c9a
Revises: 6ad27dc047f6
Create Date: 2026-11-23 20:10:26.057807

Issue #30.
- products.color: nilai lama (label bebas, mis. "Putih") diubah ke kunci whitelist bahasa Inggris
  ("white"); yang tidak dikenali -> NULL. Baru setelah itu CHECK ditambahkan.
- order_items.color (snapshot): diubah dengan peta yang sama, tetapi nilai tak dikenal dibiarkan
  (snapshot tidak boleh hilang) dan tanpa CHECK.
- product_sizes.size: CHECK format EU bulat atau .5, rentang 30-50.

Autogenerate Alembic tidak mendeteksi CHECK constraint, jadi file ini ditulis manual.
Konstanta sengaja disalin (tidak import dari models) supaya migrasi tetap sama walau model berubah.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '145edb7f0c9a'
down_revision = '6ad27dc047f6'
branch_labels = None
depends_on = None


# Kunci whitelist (urutan sesuai Figma) -> label Indonesia
COLORS = {
    "black": "Hitam", "white": "Putih", "grey": "Abu-abu", "cream": "Krem", "brown": "Cokelat",
    "red": "Merah", "maroon": "Maroon", "pink": "Pink", "orange": "Oranye", "yellow": "Kuning",
    "green": "Hijau", "blue": "Biru", "light_blue": "Biru muda", "navy": "Navy", "purple": "Ungu",
    "silver": "Perak", "gold": "Emas",
}

# Teks lama (huruf kecil, tanpa spasi tepi) -> kunci baru. Mencakup label Indonesia, kunci Inggris,
# dan beberapa ejaan umum.
ALIASES = {
    **{label.lower(): key for key, label in COLORS.items()},
    **{key: key for key in COLORS},
    **{key.replace("_", " "): key for key in COLORS},
    "abu": "grey", "gray": "grey", "coklat": "brown", "jingga": "orange", "silver": "silver",
    "putih tulang": "cream", "biru tua": "navy", "biru dongker": "navy",
}

SIZE_REGEX = r"^(3[0-9]|4[0-9])(\.5)?$|^50$"


def _case(column, else_sql):
    whens = " ".join(f"WHEN '{old}' THEN '{new}'" for old, new in ALIASES.items())
    return f"CASE lower(trim({column})) {whens} ELSE {else_sql} END"


def upgrade():
    # 1. Data lama dulu, baru CHECK (kalau dibalik, CHECK gagal dibuat)
    op.execute(f"UPDATE products SET color = {_case('color', 'NULL')} WHERE color IS NOT NULL")
    op.execute(f"UPDATE order_items SET color = {_case('color', 'color')} WHERE color IS NOT NULL")

    # 2. Rapikan penulisan ukuran yang umum ("40,5" -> "40.5", "40.0" -> "40", spasi)
    op.execute("UPDATE product_sizes SET size = replace(trim(size), ',', '.') WHERE size <> replace(trim(size), ',', '.')")
    op.execute(r"UPDATE product_sizes SET size = regexp_replace(size, '\.0$', '') WHERE size ~ '^\d+\.0$'")

    # Ukuran yang masih tidak valid tidak dihapus diam-diam (ada stoknya): hentikan migrasi.
    bind = op.get_bind()
    invalid = bind.execute(
        sa.text("SELECT id, size FROM product_sizes WHERE size !~ :pola"), {"pola": SIZE_REGEX}
    ).all()
    if invalid:
        raise RuntimeError(
            "Ukuran tidak valid di product_sizes (perbaiki manual dulu, format EU 30-50 bulat/.5): "
            + ", ".join(f"id={row.id} size={row.size!r}" for row in invalid)
        )

    # 3. CHECK constraint
    keys = ", ".join(f"'{k}'" for k in COLORS)
    op.create_check_constraint(op.f("ck_products_color"), "products", f"color IN ({keys})")
    op.create_check_constraint(op.f("ck_product_sizes_size"), "product_sizes", f"size ~ '{SIZE_REGEX}'")


def downgrade():
    op.drop_constraint(op.f("ck_product_sizes_size"), "product_sizes", type_="check")
    op.drop_constraint(op.f("ck_products_color"), "products", type_="check")

    # Kembalikan ke label Indonesia seperti sebelum migrasi ini
    whens = " ".join(f"WHEN '{key}' THEN '{label}'" for key, label in COLORS.items())
    for table in ("products", "order_items"):
        op.execute(f"UPDATE {table} SET color = CASE color {whens} ELSE color END WHERE color IS NOT NULL")

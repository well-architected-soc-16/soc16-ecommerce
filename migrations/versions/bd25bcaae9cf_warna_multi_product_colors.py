"""warna multi product_colors

Revision ID: bd25bcaae9cf
Revises: 8b941dcf18fd
Create Date: 2026-11-24 10:43:01.736608

Issue #32. Satu produk bisa punya 1-3 warna (maks. 3 dicek di form, bukan DB).
- Tabel baru product_colors (UNIQUE product_id+color, CHECK 17 kunci COLORS, CASCADE ke products).
- Data lama: products.color yang tidak NULL disalin ke product_colors, BARU kemudian kolom
  products.color + CHECK ck_products_color di-drop.
- order_items.color diperpanjang 30 -> 60 (snapshot label gabungan, mis. "Hitam / Kuning / Putih").

Downgrade: products.color diisi warna PERTAMA (id terkecil); warna ke-2/ke-3 hilang. Gagal jelas
bila ada order_items.color lebih dari 30 karakter (snapshot nota tidak dipotong diam-diam).
Ditulis manual (autogenerate tidak memindahkan data). Konstanta disalin, tidak import dari models.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bd25bcaae9cf'
down_revision = '8b941dcf18fd'
branch_labels = None
depends_on = None

COLORS = (
    "black", "white", "grey", "cream", "brown", "red", "maroon", "pink", "orange", "yellow",
    "green", "blue", "light_blue", "navy", "purple", "silver", "gold",
)
COLOR_CHECK = "color IN (" + ", ".join(f"'{c}'" for c in COLORS) + ")"


def upgrade():
    op.create_table(
        "product_colors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(length=20), nullable=False),
        sa.CheckConstraint(COLOR_CHECK, name=op.f("ck_product_colors_color")),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"],
            name=op.f("fk_product_colors_product_id_products"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_colors")),
        sa.UniqueConstraint("product_id", "color", name="uq_product_colors_product_id_color"),
    )
    op.create_index(op.f("ix_product_colors_product_id"), "product_colors", ["product_id"], unique=False)

    # 1. Pindahkan data dulu (nilai sudah tervalidasi CHECK ck_products_color dari #30)
    op.execute(
        "INSERT INTO product_colors (product_id, color) "
        "SELECT id, color FROM products WHERE color IS NOT NULL ORDER BY id"
    )

    # 2. Baru hapus kolom lama
    op.drop_constraint(op.f("ck_products_color"), "products", type_="check")
    op.drop_column("products", "color")

    op.alter_column(
        "order_items", "color",
        existing_type=sa.String(length=30), type_=sa.String(length=60), existing_nullable=True,
    )


def downgrade():
    bind = op.get_bind()
    long_rows = bind.execute(
        sa.text("SELECT id FROM order_items WHERE length(color) > 30 ORDER BY id")
    ).scalars().all()
    if long_rows:
        raise RuntimeError(
            "order_items.color lebih dari 30 karakter (snapshot multi-warna), downgrade dibatalkan "
            "supaya nota tidak terpotong. id: " + ", ".join(map(str, long_rows))
        )
    op.alter_column(
        "order_items", "color",
        existing_type=sa.String(length=60), type_=sa.String(length=30), existing_nullable=True,
    )

    op.add_column("products", sa.Column("color", sa.String(length=30), nullable=True))
    # Warna pertama (id terkecil) jadi warna tunggal
    op.execute(
        "UPDATE products p SET color = ("
        "SELECT pc.color FROM product_colors pc WHERE pc.product_id = p.id ORDER BY pc.id LIMIT 1)"
    )
    op.create_check_constraint(op.f("ck_products_color"), "products", COLOR_CHECK)

    op.drop_index(op.f("ix_product_colors_product_id"), table_name="product_colors")
    op.drop_table("product_colors")

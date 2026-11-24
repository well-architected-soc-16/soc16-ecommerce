"""spesifikasi produk

Revision ID: e11f2068a0a1
Revises: bd25bcaae9cf
Create Date: 2026-11-24 10:43:02.493592

Issue #32. Spesifikasi produk (Figma 3.01 / 2.03): material, fit, sku (UNIQUE, NULL boleh banyak),
is_limited (NOT NULL, server_default false supaya baris lama otomatis terisi false).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e11f2068a0a1'
down_revision = 'bd25bcaae9cf'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("products", sa.Column("material", sa.String(length=100), nullable=True))
    op.add_column("products", sa.Column("fit", sa.String(length=50), nullable=True))
    op.add_column("products", sa.Column("sku", sa.String(length=50), nullable=True))
    op.add_column(
        "products",
        sa.Column("is_limited", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_unique_constraint(op.f("uq_products_sku"), "products", ["sku"])


def downgrade():
    op.drop_constraint(op.f("uq_products_sku"), "products", type_="unique")
    op.drop_column("products", "is_limited")
    op.drop_column("products", "sku")
    op.drop_column("products", "fit")
    op.drop_column("products", "material")

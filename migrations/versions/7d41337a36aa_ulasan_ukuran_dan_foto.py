"""ulasan ukuran dan foto

Revision ID: 7d41337a36aa
Revises: 53dd3a62897c
Create Date: 2026-11-24 10:43:04.025549

Issue #32. Ulasan (Figma 3.01):
- reviews.size: snapshot ukuran yang dibeli (NULL untuk ulasan lama).
- Tabel baru review_photos (maks. 3 per ulasan dicek di form); filename UNIQUE (nama acak),
  CASCADE ke reviews.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d41337a36aa'
down_revision = '53dd3a62897c'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("reviews", sa.Column("size", sa.String(length=10), nullable=True))

    op.create_table(
        "review_photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("review_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["review_id"], ["reviews.id"],
            name=op.f("fk_review_photos_review_id_reviews"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_review_photos")),
        sa.UniqueConstraint("filename", name=op.f("uq_review_photos_filename")),
    )
    op.create_index(op.f("ix_review_photos_review_id"), "review_photos", ["review_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_review_photos_review_id"), table_name="review_photos")
    op.drop_table("review_photos")
    op.drop_column("reviews", "size")

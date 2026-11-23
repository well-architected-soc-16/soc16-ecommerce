from extensions import db
from models._base import now_utc


class WishlistItem(db.Model):
    """Produk yang disimpan customer ke wishlist. Satu baris per (user, produk).

    Route & template menyusul (fitur Wishlist, lihat docs/fitur.md).
    """
    __tablename__ = "wishlist_items"
    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_wishlist_items_user_id_product_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)

    # Relasi satu arah saja: hapus produk/user ditangani DB (CASCADE), bukan ORM
    user = db.relationship("User")
    product = db.relationship("Product")

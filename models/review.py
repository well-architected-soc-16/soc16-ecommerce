from extensions import db
from models._base import now_utc


class Review(db.Model):
    """Ulasan produk oleh customer. Satu user satu ulasan per produk.

    Route & template menyusul (fitur Ulasan, lihat docs/fitur.md). Panjang comment maks. 1000
    karakter divalidasi di form.
    """
    __tablename__ = "reviews"
    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_reviews_user_id_product_id"),
        db.CheckConstraint("rating BETWEEN 1 AND 5", name="rating"),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Pesanan asal pembelian (bukti "pembeli terverifikasi"); tetap ada walau pesanan dihapus
    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)

    # Relasi satu arah saja: hapus produk/user ditangani DB (CASCADE), bukan ORM
    product = db.relationship("Product")
    user = db.relationship("User")
    order = db.relationship("Order")

from datetime import datetime, timezone
from extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)

    products = db.relationship("Product", back_populates="category")


class Product(db.Model):
    __tablename__ = "products"
    __table_args__ = (
        db.CheckConstraint("harga >= 0", name="ck_products_harga_positif"),
        db.CheckConstraint("stock >= 0", name="ck_products_stock_positif"),
    )

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nama = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    deskripsi = db.Column(db.Text, nullable=False, default="")
    harga = db.Column(db.Numeric(12, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    image_filename = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    category = db.relationship("Category", back_populates="products")
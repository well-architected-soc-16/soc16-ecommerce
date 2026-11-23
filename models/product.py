from extensions import db
from models._base import now_utc, sql_in

# Whitelist nilai: dipakai di form, filter katalog, dan CHECK constraint
AUDIENCES = ("men", "women", "unisex", "kids")
PRODUCT_TYPES = ("sneakers", "running", "basketball", "casual", "sandals")


class Brand(db.Model):
    __tablename__ = "brands"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    logo_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)

    # passive_deletes="all": biar DB yang menolak hapus brand yang masih punya produk (RESTRICT)
    products = db.relationship("Product", back_populates="brand", passive_deletes="all")


class ProductGroup(db.Model):
    """Satu model sepatu milik satu brand; produk dengan group_id sama = varian warna."""
    __tablename__ = "product_groups"

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(
        db.Integer, db.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)

    brand = db.relationship("Brand")
    products = db.relationship("Product", back_populates="group")


class Product(db.Model):
    __tablename__ = "products"
    __table_args__ = (
        db.CheckConstraint("price >= 0", name="price"),
        db.CheckConstraint(sql_in("audience", AUDIENCES), name="audience"),
        db.CheckConstraint(sql_in("product_type", PRODUCT_TYPES), name="product_type"),
        db.Index("ix_products_active_created", "is_active", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(
        db.Integer, db.ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    group_id = db.Column(
        db.Integer, db.ForeignKey("product_groups.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    color = db.Column(db.String(30), nullable=True)
    audience = db.Column(db.String(10), nullable=False, default="unisex")
    product_type = db.Column(db.String(20), nullable=False, default="sneakers")
    price = db.Column(db.Numeric(12, 2), nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)

    brand = db.relationship("Brand", back_populates="products")
    group = db.relationship("ProductGroup", back_populates="products")
    sizes = db.relationship(
        "ProductSize",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductSize.size",  # aman untuk ukuran EU 36-46 (sama-sama 2 digit)
    )

    @property
    def total_stock(self):
        # Stok total dihitung dari ukuran, tidak disimpan
        return sum(s.stock for s in self.sizes)


class ProductSize(db.Model):
    __tablename__ = "product_sizes"
    __table_args__ = (
        db.UniqueConstraint("product_id", "size", name="uq_product_sizes_product_id_size"),
        db.CheckConstraint("stock >= 0", name="stock"),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    size = db.Column(db.String(10), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)

    product = db.relationship("Product", back_populates="sizes")
from extensions import db
from models._base import now_utc, sql_in

# Whitelist nilai: dipakai di form, filter katalog, dan CHECK constraint
AUDIENCES = ("men", "women", "unisex", "kids")
PRODUCT_TYPES = ("sneakers", "running", "basketball", "casual", "sandals")

# Warna produk sesuai Figma, urutan tetap (dipakai untuk pilihan form & filter katalog).
# Nilai DB (Inggris) -> (label Indonesia, hex untuk bulatan warna)
COLORS = {
    "black": ("Hitam", "#111111"),
    "white": ("Putih", "#FFFFFF"),
    "grey": ("Abu-abu", "#9CA3AF"),
    "cream": ("Krem", "#EDE3CF"),
    "brown": ("Cokelat", "#7C4A2D"),
    "red": ("Merah", "#DC2626"),
    "maroon": ("Maroon", "#7F1D1D"),
    "pink": ("Pink", "#F9A8D4"),
    "orange": ("Oranye", "#F97316"),
    "yellow": ("Kuning", "#FACC15"),
    "green": ("Hijau", "#16A34A"),
    "blue": ("Biru", "#2563EB"),
    "light_blue": ("Biru muda", "#7DD3FC"),
    "navy": ("Navy", "#1E3A8A"),
    "purple": ("Ungu", "#7C3AED"),
    "silver": ("Perak", "#C0C0C0"),
    "gold": ("Emas", "#D4AF37"),
}


def color_label(value):
    """Label Indonesia untuk nilai warna DB; nilai tak dikenal dikembalikan apa adanya."""
    return COLORS[value][0] if value in COLORS else (value or "")


def color_hex(value):
    return COLORS[value][1] if value in COLORS else None


# Ukuran EU: bilangan bulat atau .5, rentang 16–50 (termasuk anak; "28.5", "40"; 50.5 tidak).
SIZE_MIN, SIZE_MAX = 16, 50
SIZE_PATTERN = r"^(1[6-9]|[2-4][0-9])(\.5)?$|^50$"

MAX_COLORS = 3  # maks. warna per produk, dicek di form (bukan DB)

# Perkiraan konversi EU -> (US, UK) untuk sepatu pria/unisex. Hanya acuan tampilan,
# bukan tabel resmi brand; ukuran anak (< 35) tidak dikonversi.
SIZE_CONVERSION = {
    "35": ("3.5", "3"), "35.5": ("3.5", "3"), "36": ("4", "3.5"), "36.5": ("4.5", "4"),
    "37": ("5", "4.5"), "37.5": ("5", "4.5"), "38": ("5.5", "5"), "38.5": ("6", "5.5"),
    "39": ("6.5", "6"), "39.5": ("6.5", "6"), "40": ("7", "6.5"), "40.5": ("7.5", "7"),
    "41": ("8", "7.5"), "41.5": ("8", "7.5"), "42": ("8.5", "8"), "42.5": ("9", "8.5"),
    "43": ("9.5", "9"), "43.5": ("9.5", "9"), "44": ("10", "9.5"), "44.5": ("10.5", "10"),
    "45": ("11", "10.5"), "45.5": ("11", "10.5"), "46": ("11.5", "11"), "46.5": ("12", "11.5"),
    "47": ("12.5", "12"), "47.5": ("12.5", "12"), "48": ("13", "12.5"), "48.5": ("13.5", "13"),
    "49": ("14", "13.5"), "49.5": ("14", "13.5"), "50": ("14.5", "14"),
}


def convert_size(eu):
    """Perkiraan ukuran US/UK dari ukuran EU, mis. "40" -> {"us": "7", "uk": "6.5"}; None jika di luar tabel."""
    pair = SIZE_CONVERSION.get(str(eu))
    return {"us": pair[0], "uk": pair[1]} if pair else None


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
    audience = db.Column(db.String(10), nullable=False, default="unisex")
    product_type = db.Column(db.String(20), nullable=False, default="sneakers")
    price = db.Column(db.Numeric(12, 2), nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    # Spesifikasi (Figma 3.01 / 2.03)
    material = db.Column(db.String(100), nullable=True)
    fit = db.Column(db.String(50), nullable=True)
    sku = db.Column(db.String(50), unique=True, nullable=True)  # NULL boleh banyak
    is_limited = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
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
        # Urut menurut angka ("40" < "40.5" < "41"), bukan string
        order_by=lambda: db.cast(ProductSize.size, db.Numeric),
    )

    # Warna produk (1–3), urut sesuai urutan disimpan
    colors = db.relationship(
        "ProductColor",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by=lambda: ProductColor.id,
    )

    @property
    def color_keys(self):
        """Kunci warna, mis. ["black", "white"]."""
        return [c.color for c in self.colors]

    @property
    def total_stock(self):
        # Stok total dihitung dari ukuran, tidak disimpan
        return sum(s.stock for s in self.sizes)


class ProductColor(db.Model):
    """Satu warna milik satu produk (maks. MAX_COLORS per produk, dicek di form)."""
    __tablename__ = "product_colors"
    __table_args__ = (
        db.UniqueConstraint("product_id", "color", name="uq_product_colors_product_id_color"),
        db.CheckConstraint(sql_in("color", tuple(COLORS)), name="color"),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    color = db.Column(db.String(20), nullable=False)  # salah satu kunci COLORS

    product = db.relationship("Product", back_populates="colors")


class ProductSize(db.Model):
    __tablename__ = "product_sizes"
    __table_args__ = (
        db.UniqueConstraint("product_id", "size", name="uq_product_sizes_product_id_size"),
        db.CheckConstraint("stock >= 0", name="stock"),
        # Format ukuran EU (regex PostgreSQL); dilewati di dialek lain (mis. SQLite untuk uji)
        db.CheckConstraint(f"size ~ '{SIZE_PATTERN}'", name="size").ddl_if(dialect="postgresql"),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    size = db.Column(db.String(10), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)

    product = db.relationship("Product", back_populates="sizes")
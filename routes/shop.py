import os
from datetime import timedelta

from flask import Blueprint, render_template, request, redirect, url_for, current_app
from sqlalchemy.orm import selectinload

from extensions import db
from models import Brand, Product, ProductSize, Order, OrderItem, now_utc

shop_bp = Blueprint("shop", __name__)

# Hero beranda. "link" = (endpoint, parameter url_for, anchor); gambar opsional di static/img/banner/.
# Teks hanya menjanjikan hal yang memang sudah ada atau sedang dibangun di fitur.md.
SLIDES = [
    {
        "image": "adidas-1.jpg",
        "label": "Baru",
        "title": "Koleksi terbaru",
        "text": "Sneakers, lari, dan kasual dari brand pilihan.",
        "button": "Belanja sekarang",
        "link": ("shop.catalog", {}, ""),
    },
    {
        "image": "nb.jpg",
        "label": "Belanja aman",
        "title": "Pembayaran dicek admin",
        "text": "Pesanan diproses setelah bukti bayar diverifikasi.",
        "button": "Lihat produk",
        "link": ("shop.catalog", {}, ""),
    },
    {
        "image": "nike-2.jpg",
        "label": "Pilihan",
        "title": "Pilihan minggu ini",
        "text": "Dikurasi admin Pururuna.",
        "button": "Lihat pilihan",
        "link": ("shop.index", {}, "#pilihan"),
    },
    {
        "image": "banner-4.jpg",
        "label": "Akun aman",
        "title": "Akun terlindungi",
        "text": "Terkunci otomatis setelah beberapa kali salah password.",
        "button": "Daftar sekarang",
        "link": ("auth.register", {}, ""),
    },
    {
        "image": "banner-5.jpg",
        "label": "Semua brand",
        "title": "Temukan pasanganmu",
        "text": "Cari sepatu dari brand favoritmu.",
        "button": "Lihat katalog",
        "link": ("shop.catalog", {}, ""),
    },
]

# Kotak "Jelajahi koleksi". Parameter filternya baru diproses di issue Katalog (1.04);
# untuk sekarang /produk mengabaikannya dan menampilkan semua produk (urut terbaru).
COLLECTIONS = [
    {"title": "Top 50 sepatu", "text": "Paling dicari minggu ini", "params": {"urut": "terlaris"}, "image": "top-50.jpg"},
    {"title": "Sepatu lari", "text": "Ringan untuk latihan harian", "params": {"jenis": "running"}, "image": "lari.jpg"},
    {"title": "Di bawah Rp 1 juta", "text": "Hemat tanpa kompromi", "params": {"harga_maks": 1000000}, "image": "hemat.jpg"},
    {"title": "Edisi terbatas", "text": "Stok sedikit, cepat habis", "params": {"stok": "terbatas"}, "image": "terbatas.jpg"},
]

SHELF_LIMIT = 10          # maks. kartu per rak geser
TOP_BRANDS_LIMIT = 7      # kotak "Belanja per brand"
BESTSELLER_DAYS = 30
SOLD_STATUSES = ("paid", "shipped", "completed")  # pesanan yang dihitung sebagai terjual
PER_PAGE = 12


def _with_card_data(query):
    # Kartu produk butuh brand + ukuran (total_stock): muat sekaligus, tanpa N+1
    return query.options(selectinload(Product.sizes), selectinload(Product.brand))


def _static_exists(*parts):
    return os.path.isfile(os.path.join(current_app.static_folder, *parts))


def catalog_data():
    q = (request.args.get("q") or "").strip()[:100]
    brand_slug = (request.args.get("brand") or "").strip()[:120]
    page = request.args.get("page", 1, type=int)

    query = _with_card_data(db.select(Product).where(Product.is_active.is_(True)))

    active_brand = None
    if brand_slug:
        active_brand = db.session.execute(
            db.select(Brand).filter_by(slug=brand_slug)
        ).scalar_one_or_none()
        if active_brand:
            query = query.where(Product.brand_id == active_brand.id)

    if q:
        query = query.where(Product.name.icontains(q, autoescape=True))

    query = query.order_by(Product.created_at.desc(), Product.id.desc())
    pagination = db.paginate(query, page=page, per_page=PER_PAGE, error_out=False)

    brands = db.session.execute(db.select(Brand).order_by(Brand.name)).scalars().all()

    return {"pagination": pagination, "q": q, "active_brand": active_brand, "brands": brands}


def home_data():
    slides = [
        {
            **slide,
            "href": url_for(slide["link"][0], **slide["link"][1]) + slide["link"][2],
            "has_image": _static_exists("img", "banner", slide["image"]),
        }
        for slide in SLIDES
    ]

    collections = [
        {
            **c,
            "href": url_for("shop.catalog", **c["params"]),
            "has_image": _static_exists("img", "koleksi", c["image"]),
        }
        for c in COLLECTIONS
    ]

    active = Product.is_active.is_(True)

    top_brands = db.session.execute(
        db.select(Brand)
        .join(Product, Product.brand_id == Brand.id)
        .where(active)
        .group_by(Brand.id)
        .order_by(db.func.count(Product.id).desc(), Brand.name)
        .limit(TOP_BRANDS_LIMIT)
    ).scalars().all()

    newest = db.session.execute(
        _with_card_data(db.select(Product).where(active))
        .order_by(Product.created_at.desc(), Product.id.desc())
        .limit(SHELF_LIMIT)
    ).scalars().all()

    sold = (
        db.select(ProductSize.product_id, db.func.sum(OrderItem.quantity).label("qty"))
        .join(OrderItem, OrderItem.product_size_id == ProductSize.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.status.in_(SOLD_STATUSES),
            Order.created_at >= now_utc() - timedelta(days=BESTSELLER_DAYS),
        )
        .group_by(ProductSize.product_id)
        .subquery()
    )
    bestsellers = db.session.execute(
        _with_card_data(db.select(Product).join(sold, sold.c.product_id == Product.id).where(active))
        .order_by(sold.c.qty.desc(), Product.id.desc())
        .limit(SHELF_LIMIT)
    ).scalars().all()

    featured = db.session.execute(
        _with_card_data(db.select(Product).where(active, Product.is_featured.is_(True)))
        .order_by(Product.created_at.desc(), Product.id.desc())
        .limit(SHELF_LIMIT)
    ).scalars().all()

    return {
        "slides": slides,
        "collections": collections,
        "top_brands": top_brands,
        "newest": newest,
        "bestsellers": bestsellers,
        "featured": featured,
    }


@shop_bp.app_context_processor
def inject_brand_menu():
    """Daftar brand untuk dropdown Brand di header toko.

    Berupa fungsi supaya query hanya jalan di halaman yang benar-benar memanggilnya
    (header toko), bukan di setiap render template (mis. halaman admin).
    """
    def brand_menu():
        return db.session.execute(db.select(Brand).order_by(Brand.name)).scalars().all()
    return {"brand_menu": brand_menu}


@shop_bp.route("/")
def index():
    # Tautan lama (sebelum katalog pindah ke /produk) tetap jalan
    if any(request.args.get(k) for k in ("q", "brand", "page")):
        return redirect(url_for("shop.catalog", **request.args.to_dict()))
    return render_template("index.html", **home_data())


@shop_bp.route("/produk")
def catalog():
    return render_template("shop/catalog.html", **catalog_data())


@shop_bp.route("/produk/<slug>")
def detail(slug):
    product = db.first_or_404(
        _with_card_data(db.select(Product).filter_by(slug=slug, is_active=True))
    )

    # Varian warna lain dari model yang sama
    variants = []
    if product.group_id:
        variants = db.session.execute(
            db.select(Product)
            .where(
                Product.group_id == product.group_id,
                Product.id != product.id,
                Product.is_active.is_(True),
            )
            .order_by(Product.color)
        ).scalars().all()

    return render_template("shop/detail.html", product=product, variants=variants)

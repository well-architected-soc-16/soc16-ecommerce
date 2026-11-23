import os

from flask import Blueprint, render_template, request, redirect, url_for, current_app
from sqlalchemy.orm import selectinload

from extensions import db
from models import Brand, Product, ProductSize

shop_bp = Blueprint("shop", __name__)

SLIDES = [
    {
        "image": "adidas-1.jpg",
        "label": "Baru",
        "title": "Koleksi terbaru",
        "text": "Harga jelas, pembayaran terverifikasi.",
        "button": "Belanja sekarang",
        "link": "#produk",
    },
    {
        "image": "nb.jpg",
        "label": "Belanja aman",
        "title": "Pembayaran dicek admin",
        "text": "Pesanan diproses setelah bukti bayar diverifikasi.",
        "button": "Lihat produk",
        "link": "#produk",
    },
    {
        "image": "nike-2.jpg",
        "label": "Segera habis",
        "title": "Stok terbatas",
        "text": "Ambil sebelum kehabisan.",
        "button": "Lihat stok terbatas",
        "link": "#stok-terbatas",
    },
]
LOW_STOCK_LIMIT = 5
PER_PAGE = 12


def _stock_subquery():
    return (
        db.select(ProductSize.product_id, db.func.sum(ProductSize.stock).label("total"))
        .group_by(ProductSize.product_id)
        .subquery()
    )


def catalog_data():
    q = (request.args.get("q") or "").strip()[:100]
    brand_slug = (request.args.get("brand") or "").strip()[:120]
    page = request.args.get("page", 1, type=int)

    query = (
        db.select(Product)
        .where(Product.is_active.is_(True))
        .options(selectinload(Product.sizes), selectinload(Product.brand))
    )

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
    folder = os.path.join(current_app.static_folder, "img", "banner")
    slides = [
        {**slide, "has_image": os.path.isfile(os.path.join(folder, slide["image"]))}
        for slide in SLIDES
    ]

    stock = _stock_subquery()
    low_stock = db.session.execute(
        db.select(Product)
        .join(stock, stock.c.product_id == Product.id)
        .where(Product.is_active.is_(True), stock.c.total > 0, stock.c.total <= LOW_STOCK_LIMIT)
        .options(selectinload(Product.sizes), selectinload(Product.brand))
        .order_by(stock.c.total)
        .limit(4)
    ).scalars().all()

    return {"slides": slides, "low_stock": low_stock}


@shop_bp.route("/")
def index():
    data = catalog_data()
    is_home = not data["q"] and not data["active_brand"] and data["pagination"].page == 1
    if is_home:
        data.update(home_data())
    return render_template("index.html", is_home=is_home, **data)


@shop_bp.route("/produk")
def catalog():
    return redirect(url_for("shop.index", **request.args.to_dict()))


@shop_bp.route("/produk/<slug>")
def detail(slug):
    product = db.first_or_404(
        db.select(Product)
        .filter_by(slug=slug, is_active=True)
        .options(selectinload(Product.sizes), selectinload(Product.brand))
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

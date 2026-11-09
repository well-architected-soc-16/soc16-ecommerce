import os

from flask import Blueprint, render_template, request, redirect, url_for, current_app

from extensions import db
from models import Category, Product

shop_bp = Blueprint("shop", __name__)

SLIDES = [
    {
        "gambar": "adidas-1.jpg",
        "label": "Baru",
        "judul": "Koleksi terbaru",
        "teks": "Harga jelas, pembayaran terverifikasi.",
        "tombol": "Belanja sekarang",
        "tautan": "#produk",
    },
    {
        "gambar": "nb.jpg",
        "label": "Belanja aman",
        "judul": "Pembayaran dicek admin",
        "teks": "Pesanan diproses setelah bukti bayar diverifikasi.",
        "tombol": "Lihat produk",
        "tautan": "#produk",
    },
    {
        "gambar": "nike-2.jpg",
        "label": "Segera habis",
        "judul": "Stok terbatas",
        "teks": "Ambil sebelum kehabisan.",
        "tombol": "Lihat stok terbatas",
        "tautan": "#stok-terbatas",
    },
]
BATAS_STOK_SEDIKIT = 5


def data_katalog():
    q = (request.args.get("q") or "").strip()[:100]
    kategori_slug = request.args.get("kategori") or ""
    page = request.args.get("page", 1, type=int)

    query = db.select(Product).where(Product.is_active.is_(True))

    kategori_aktif = None
    if kategori_slug:
        kategori_aktif = db.session.execute(
            db.select(Category).filter_by(slug=kategori_slug)
        ).scalar_one_or_none()
        if kategori_aktif:
            query = query.where(Product.category_id == kategori_aktif.id)

    if q:
        query = query.where(Product.nama.icontains(q, autoescape=True))

    query = query.order_by(Product.created_at.desc())
    halaman = db.paginate(query, page=page, per_page=12, error_out=False)

    daftar_kategori = db.session.execute(
        db.select(Category).order_by(Category.nama)
    ).scalars().all()

    return {
        "halaman": halaman,
        "q": q,
        "kategori_aktif": kategori_aktif,
        "daftar_kategori": daftar_kategori,
    }


def data_beranda():
    folder = os.path.join(current_app.static_folder, "img", "banner")
    slides = [
        {**slide, "ada_gambar": os.path.isfile(os.path.join(folder, slide["gambar"]))}
        for slide in SLIDES
    ]

    stok_terbatas = db.session.execute(
        db.select(Product)
        .where(
            Product.is_active.is_(True),
            Product.stock > 0,
            Product.stock <= BATAS_STOK_SEDIKIT,
        )
        .order_by(Product.stock)
        .limit(4)
    ).scalars().all()

    return {"slides": slides, "stok_terbatas": stok_terbatas}


@shop_bp.route("/produk")
def katalog():
    return redirect(url_for("index", **request.args.to_dict()))


@shop_bp.route("/produk/<slug>")
def detail(slug):
    produk = db.first_or_404(
        db.select(Product).filter_by(slug=slug, is_active=True)
    )
    return render_template("shop/detail.html", produk=produk)
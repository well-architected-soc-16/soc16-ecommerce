from flask import Blueprint, render_template, request, redirect, url_for

from extensions import db
from models import Category, Product

shop_bp = Blueprint("shop", __name__)


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


@shop_bp.route("/produk")
def katalog():
    return redirect(url_for("index", **request.args.to_dict()))


@shop_bp.route("/produk/<slug>")
def detail(slug):
    produk = db.first_or_404(
        db.select(Product).filter_by(slug=slug, is_active=True)
    )
    return render_template("shop/detail.html", produk=produk)
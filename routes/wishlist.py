"""Wishlist customer (docs/desain-detail-wishlist.md, Figma 3.16/3.17).

Aturan: hanya user login dengan role customer; semua query difilter user_id == g.user.id (IDOR);
produk tersembunyi tidak bisa disimpan (404) dan tidak ditampilkan. Tidak dicatat ke audit log
(bukan aksi sensitif), kecuali admin yang mencoba (access_denied).
"""
from flask import Blueprint, render_template, redirect, url_for, flash, g, abort, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import contains_eager, selectinload

from audit import catat
from extensions import db
from models import Product, WishlistItem
from routes.auth import login_required
from utils import safe_next

wishlist_bp = Blueprint("wishlist", __name__)

# ?urut= -> urutan daftar (whitelist)
SORTS = {
    "terbaru": ("Terakhir disimpan", (WishlistItem.created_at.desc(), WishlistItem.id.desc())),
    "termurah": ("Harga termurah", (Product.price.asc(), WishlistItem.id.desc())),
    "termahal": ("Harga termahal", (Product.price.desc(), WishlistItem.id.desc())),
}
LIST_LIMIT = 200  # batas aman; wishlist normal jauh di bawah ini


def wishlist_ids():
    """ID produk di wishlist user sekarang (set). Dipanggil kartu produk di template;
    hasilnya disimpan di g, jadi satu request cukup satu query."""
    if g.get("user") is None or g.user.is_admin:
        return frozenset()
    if "_wishlist_ids" not in g:
        g._wishlist_ids = frozenset(
            db.session.execute(
                db.select(WishlistItem.product_id).where(WishlistItem.user_id == g.user.id)
            ).scalars()
        )
    return g._wishlist_ids


def _customer_only():
    if g.user.is_admin:
        catat("access_denied", user=g.user, path=request.path)
        abort(403)


@wishlist_bp.route("/wishlist/<int:product_id>", methods=["POST"])
def toggle(product_id):
    back = safe_next(request.form.get("next"))

    if g.user is None:
        flash("Masuk dulu untuk menyimpan produk ke wishlist.", "error")
        return redirect(url_for("auth.login", next=back or url_for("wishlist.index")))
    _customer_only()

    # Produk tersembunyi / tidak ada -> 404 (tidak bisa disimpan)
    product = db.first_or_404(db.select(Product).filter_by(id=product_id, is_active=True))

    # Aksi eksplisit dari tombol (bukan "balik keadaan"), jadi klik ganda tidak membatalkan dirinya
    action = request.form.get("aksi")
    if action not in ("simpan", "hapus"):
        abort(400)

    item = db.session.execute(
        db.select(WishlistItem).filter_by(user_id=g.user.id, product_id=product.id)
    ).scalar_one_or_none()

    if action == "simpan":
        if item is None:
            db.session.add(WishlistItem(user_id=g.user.id, product_id=product.id))
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()  # baris sudah dibuat request lain (UNIQUE): hasilnya sama
        flash("Disimpan ke wishlist.", "success")
    else:
        if item is not None:
            db.session.delete(item)
            db.session.commit()
        flash("Dihapus dari wishlist.", "success")

    return redirect(back or url_for("shop.detail", slug=product.slug))


@wishlist_bp.route("/wishlist")
@login_required
def index():
    _customer_only()

    sort = request.args.get("urut", "terbaru")
    if sort not in SORTS:
        sort = "terbaru"

    items = db.session.execute(
        db.select(WishlistItem)
        .join(WishlistItem.product)
        .where(WishlistItem.user_id == g.user.id, Product.is_active.is_(True))
        .options(
            contains_eager(WishlistItem.product).selectinload(Product.sizes),
            contains_eager(WishlistItem.product).selectinload(Product.brand),
        )
        .order_by(*SORTS[sort][1])
        .limit(LIST_LIMIT)
    ).scalars().all()

    return render_template(
        "shop/wishlist.html",
        products=[item.product for item in items],
        sort=sort,
        sorts={key: label for key, (label, _order) in SORTS.items()},
    )

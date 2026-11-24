"""Keranjang belanja (docs/desain-keranjang.md, Figma 3.02/3.03, issue #35).

Aturan: hanya user login dengan role customer (admin membuka /keranjang -> dashboard admin + pesan;
admin mengirim POST -> 403 + access_denied); semua query difilter Cart.user_id == g.user.id
(item milik orang lain -> 404, cegah IDOR). Harga tidak disimpan di keranjang dan tidak pernah
diambil dari form: selalu products.price saat ini. Stok tidak dikurangi di sini (baru saat checkout).
Tidak dicatat ke audit log, kecuali admin yang mencoba (access_denied).
"""
import re

from flask import Blueprint, render_template, redirect, url_for, flash, g, abort, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from audit import catat
from extensions import db
from models import Cart, CartItem, Product, ProductSize, now_utc
from utils import safe_next

cart_bp = Blueprint("cart", __name__)

QUANTITY_PATTERN = re.compile(r"\d{1,4}")  # bilangan bulat positif; "abc", "-1", "1e9" ditolak


def cart_count():
    """Jumlah baris produk di keranjang user sekarang (badge header), tanpa produk yang disembunyikan
    admin (sama dengan "N produk" di judul halaman keranjang). Satu query per request (disimpan di g)."""
    if g.get("user") is None or g.user.is_admin:
        return 0
    if "_cart_count" not in g:
        g._cart_count = db.session.scalar(
            db.select(db.func.count(CartItem.id))
            .join(Cart, Cart.id == CartItem.cart_id)
            .join(ProductSize, ProductSize.id == CartItem.product_size_id)
            .join(Product, Product.id == ProductSize.product_id)
            .where(Cart.user_id == g.user.id, Product.is_active.is_(True))
        ) or 0
    return g._cart_count


def _parse_quantity(raw):
    raw = (raw or "").strip()
    if not QUANTITY_PATTERN.fullmatch(raw):
        return None
    value = int(raw)
    return value if value >= 1 else None


def _require_customer(back_to):
    """None kalau boleh lanjut; selain itu response redirect atau abort.

    Tamu -> Masuk. Admin membuka halaman (GET) -> dashboard admin dengan pesan, bukan 403;
    admin yang mengirim aksi (POST) -> 403 + audit access_denied.
    """
    if g.user is None:
        flash("Masuk dulu untuk memakai keranjang.", "error")
        return redirect(url_for("auth.login", next=back_to))
    if g.user.is_admin:
        if request.method == "GET":
            flash("Akun admin tidak memakai keranjang.", "info")
            return redirect(url_for("admin.dashboard"))
        catat("access_denied", user=g.user, path=request.path)
        abort(403)
    return None


def _get_or_create_cart():
    cart = db.session.execute(db.select(Cart).filter_by(user_id=g.user.id)).scalar_one_or_none()
    if cart is not None:
        return cart
    try:
        with db.session.begin_nested():  # savepoint: request lain bisa membuat keranjang bersamaan
            cart = Cart(user_id=g.user.id)
            db.session.add(cart)
    except IntegrityError:
        cart = db.session.execute(db.select(Cart).filter_by(user_id=g.user.id)).scalar_one()
    return cart


def _own_item(item_id):
    """Item keranjang milik user sekarang, atau 404 (termasuk item milik orang lain)."""
    return db.first_or_404(
        db.select(CartItem)
        .join(Cart, Cart.id == CartItem.cart_id)
        .where(CartItem.id == item_id, Cart.user_id == g.user.id)
        .options(selectinload(CartItem.product_size).selectinload(ProductSize.product))
    )


@cart_bp.route("/keranjang/tambah", methods=["POST"])
def add():
    back = safe_next(request.form.get("next"))
    denied = _require_customer(back or url_for("cart.index"))
    if denied:
        return denied
    fallback = back or url_for("shop.catalog")

    raw_size = (request.form.get("product_size_id") or "").strip()
    if not raw_size:
        flash("Pilih ukuran dulu.", "error")
        return redirect(fallback)
    if not raw_size.isdigit() or len(raw_size) > 9:
        abort(400)

    # Ukuran harus ada dan produknya aktif
    size = db.first_or_404(
        db.select(ProductSize)
        .join(Product, Product.id == ProductSize.product_id)
        .where(ProductSize.id == int(raw_size), Product.is_active.is_(True))
        .options(selectinload(ProductSize.product))
    )
    product = size.product
    back = back or url_for("shop.detail", slug=product.slug)

    quantity = _parse_quantity(request.form.get("quantity"))
    if quantity is None:
        flash("Jumlah tidak valid. Isi angka mulai dari 1.", "error")
        return redirect(back)
    if size.stock <= 0:
        flash(f"Stok ukuran EU {size.size} habis.", "error")
        return redirect(back)
    if quantity > size.stock:
        flash(f"Jumlah melebihi stok (tersisa {size.stock}).", "error")
        return redirect(back)

    cart = _get_or_create_cart()
    item = db.session.execute(
        db.select(CartItem).filter_by(cart_id=cart.id, product_size_id=size.id)
    ).scalar_one_or_none()

    capped = False
    if item is None:
        item = CartItem(cart_id=cart.id, product_size_id=size.id, quantity=quantity)
        db.session.add(item)
    else:
        # Ukuran yang sama ditambah lagi: jumlahkan, dibatasi stok
        total = item.quantity + quantity
        capped = total > size.stock
        item.quantity = min(total, size.stock)
    cart.updated_at = now_utc()

    try:
        db.session.commit()
    except IntegrityError:
        # Dua request bersamaan menambah ukuran yang sama (UNIQUE cart_id + product_size_id)
        db.session.rollback()
        item = db.session.execute(
            db.select(CartItem).filter_by(cart_id=cart.id, product_size_id=size.id)
        ).scalar_one()
        total = item.quantity + quantity
        capped = total > size.stock
        item.quantity = min(total, size.stock)
        db.session.commit()

    if capped:
        flash(f"Jumlah disesuaikan dengan stok (tersisa {size.stock}).", "error")
    flash(f"'{product.name}' masuk ke keranjang.", "success")
    return redirect(back)


@cart_bp.route("/keranjang")
def index():
    denied = _require_customer(url_for("cart.index"))
    if denied:
        return denied

    cart = db.session.execute(
        db.select(Cart)
        .filter_by(user_id=g.user.id)
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.product_size)
            .selectinload(ProductSize.product)
            .selectinload(Product.brand)
        )
    ).scalar_one_or_none()

    rows = []
    for item in sorted(cart.items, key=lambda i: i.id) if cart else []:
        size = item.product_size
        product = size.product
        if not product.is_active:
            problem = "Produk tidak tersedia lagi. Hapus dari keranjang."
        elif size.stock <= 0:
            problem = "Stok habis"
        elif item.quantity > size.stock:
            problem = f"Stok tersisa {size.stock}"
        else:
            problem = None
        rows.append({
            "item": item, "size": size, "product": product,
            "subtotal": product.price * item.quantity,  # harga saat ini, bukan dari form
            "problem": problem, "available": product.is_active,
        })

    # Produk yang disembunyikan admin tetap tampil (supaya bisa dihapus) tapi tidak dihitung:
    # judul "N produk" (= badge header), jumlah barang, dan subtotal.
    counted = [r for r in rows if r["available"]]
    return render_template(
        "shop/cart.html",
        rows=rows,
        product_count=len(counted),
        total_pairs=sum(r["item"].quantity for r in counted),
        subtotal=sum((r["subtotal"] for r in counted), 0),
        has_problem=any(r["problem"] for r in rows),
    )


@cart_bp.route("/keranjang/<int:item_id>/ubah", methods=["POST"])
def update(item_id):
    denied = _require_customer(url_for("cart.index"))
    if denied:
        return denied
    item = _own_item(item_id)
    size = item.product_size
    back = url_for("cart.index") + f"#item-{item.id}"

    if not size.product.is_active:
        flash("Produk tidak tersedia lagi. Hapus dari keranjang.", "error")
        return redirect(back)

    action = request.form.get("aksi", "set")
    if action == "kurang":
        new_quantity = item.quantity - 1
    elif action == "tambah":
        new_quantity = item.quantity + 1
    elif action == "set":
        new_quantity = _parse_quantity(request.form.get("quantity"))
        if new_quantity is None:
            flash("Jumlah tidak valid. Isi angka mulai dari 1, atau pakai Hapus.", "error")
            return redirect(back)
    else:
        abort(400)

    if new_quantity < 1:
        flash("Jumlah minimal 1. Pakai Hapus untuk membuang item.", "error")
        return redirect(back)
    # Melebihi stok hanya ditolak kalau jumlah bertambah; mengurangi item bermasalah tetap boleh
    if new_quantity > size.stock and new_quantity > item.quantity:
        flash(f"Stok tersisa {size.stock}.", "error")
        return redirect(back)

    item.quantity = new_quantity
    item.cart.updated_at = now_utc()
    db.session.commit()
    return redirect(back)


@cart_bp.route("/keranjang/<int:item_id>/hapus", methods=["POST"])
def remove(item_id):
    denied = _require_customer(url_for("cart.index"))
    if denied:
        return denied
    item = _own_item(item_id)
    name = item.product_size.product.name
    item.cart.updated_at = now_utc()
    db.session.delete(item)
    db.session.commit()
    flash(f"'{name}' dihapus dari keranjang.", "success")
    return redirect(url_for("cart.index"))

from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, g, abort, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from audit import catat, WIB
from extensions import db
from forms.admin import BrandForm, ProductForm, DeleteProductForm
from models import (
    Brand, Product, ProductColor, ProductGroup, ProductSize, OrderItem, User, AuditLog, now_utc,
)
from utils import slug_unik

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
def require_admin():
    # Satu-satunya pemeriksaan hak akses admin: berlaku untuk semua route di blueprint ini
    if g.user is None:
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("auth.login"))
    if not g.user.is_admin:
        catat("access_denied", user=g.user, path=request.path)
        abort(403)


@admin_bp.route("/")
def dashboard():
    def count(query):
        return db.session.scalar(query) or 0

    stock_per_product = (
        db.select(ProductSize.product_id, db.func.sum(ProductSize.stock).label("total"))
        .group_by(ProductSize.product_id)
        .subquery()
    )
    stat = {
        "customers": count(db.select(db.func.count(User.id)).where(User.role == "customer")),
        "brands": count(db.select(db.func.count(Brand.id))),
        "active_products": count(
            db.select(db.func.count(Product.id)).where(Product.is_active.is_(True))
        ),
        "out_of_stock": count(
            db.select(db.func.count(Product.id))
            .join(stock_per_product, stock_per_product.c.product_id == Product.id)
            .where(Product.is_active.is_(True), stock_per_product.c.total == 0)
        ),
        "failed_logins_24h": count(
            db.select(db.func.count(AuditLog.id)).where(
                AuditLog.event == "login_failed",
                AuditLog.created_at >= now_utc() - timedelta(hours=24),
            )
        ),
    }
    return render_template("admin/dashboard.html", stat=stat)


# ---------- Brand ----------

@admin_bp.route("/brand")
def brand_list():
    brands = db.session.execute(
        db.select(Brand).options(selectinload(Brand.products)).order_by(Brand.name)
    ).scalars().all()
    return render_template("admin/brand_list.html", brands=brands)


def _brand_name_taken(name, ignore_id=None):
    query = db.select(Brand.id).where(db.func.lower(Brand.name) == name.lower())
    if ignore_id:
        query = query.where(Brand.id != ignore_id)
    return db.session.execute(query).first() is not None


def _commit_brand(form):
    """Commit perubahan brand. False kalau ditolak UNIQUE (mis. dua admin menyimpan bersamaan)."""
    try:
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        form.name.errors.append("Brand dengan nama ini sudah ada.")
        return False


@admin_bp.route("/brand/baru", methods=["GET", "POST"])
def brand_create():
    form = BrandForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        if _brand_name_taken(name):
            form.name.errors.append("Brand dengan nama ini sudah ada.")
        else:
            brand = Brand(name=name, slug=slug_unik(Brand, name))
            db.session.add(brand)
            if _commit_brand(form):
                catat("brand_created", user=g.user, brand_id=brand.id, name=name)
                flash(f"Brand '{name}' ditambahkan.", "success")
                return redirect(url_for("admin.brand_list"))
    return render_template("admin/brand_form.html", form=form, title="Tambah Brand")


@admin_bp.route("/brand/<int:id>/edit", methods=["GET", "POST"])
def brand_edit(id):
    brand = db.get_or_404(Brand, id)
    form = BrandForm(obj=brand)
    if form.validate_on_submit():
        name = form.name.data.strip()
        if _brand_name_taken(name, ignore_id=brand.id):
            form.name.errors.append("Brand dengan nama ini sudah ada.")
        else:
            brand.name = name
            brand.slug = slug_unik(Brand, name, abaikan_id=brand.id)
            if _commit_brand(form):
                catat("brand_updated", user=g.user, brand_id=brand.id, name=name)
                flash("Brand diperbarui.", "success")
                return redirect(url_for("admin.brand_list"))
    return render_template("admin/brand_form.html", form=form, title="Edit Brand")


@admin_bp.route("/brand/<int:id>/hapus", methods=["POST"])
def brand_delete(id):
    brand = db.get_or_404(Brand, id)
    brand_id, name = brand.id, brand.name

    db.session.delete(brand)
    try:
        db.session.commit()  # ditolak DB (RESTRICT) kalau masih ada produk
    except IntegrityError:
        db.session.rollback()
        flash("Brand masih dipakai produk, tidak bisa dihapus.", "error")
        return redirect(url_for("admin.brand_list"))

    catat("brand_deleted", user=g.user, brand_id=brand_id, name=name)
    flash("Brand dihapus.", "success")
    return redirect(url_for("admin.brand_list"))


# ---------- Produk ----------

def _fill_brand_choices(form):
    brands = db.session.execute(db.select(Brand).order_by(Brand.name)).scalars().all()
    form.brand_id.choices = [(b.id, b.name) for b in brands]
    return brands


def _get_or_create_group(brand_id, name):
    """Grup varian dicari per brand: model "Classic" milik dua brand berbeda tidak tercampur."""
    name = (name or "").strip()
    if not name:
        return None
    group = db.session.execute(
        db.select(ProductGroup).where(
            ProductGroup.brand_id == brand_id,
            db.func.lower(ProductGroup.name) == name.lower(),
        )
    ).scalars().first()
    if group is None:
        group = ProductGroup(brand_id=brand_id, name=name)
        db.session.add(group)
    return group


def _apply_sizes(product, parsed):
    """Samakan baris product_sizes dengan isi form: ubah stok, tambah ukuran baru, hapus yang hilang."""
    existing = {s.size: s for s in product.sizes}
    for size, stock in parsed.items():
        if size in existing:
            existing[size].stock = stock
        else:
            product.sizes.append(ProductSize(size=size, stock=stock))
    for size, row in existing.items():
        if size not in parsed:
            product.sizes.remove(row)


def _apply_colors(product, keys):
    """Samakan baris product_colors dengan pilihan form; warna yang tetap dipilih tidak dibuat ulang."""
    for row in [c for c in product.colors if c.color not in keys]:
        product.colors.remove(row)
    existing = set(product.color_keys)
    for key in keys:
        if key not in existing:
            product.colors.append(ProductColor(color=key))


def _sizes_to_text(product):
    return ", ".join(f"{s.size}:{s.stock}" for s in product.sizes)


def _fill_product(product, form):
    product.name = form.name.data.strip()
    product.brand_id = form.brand_id.data
    product.group = _get_or_create_group(form.brand_id.data, form.group_name.data)
    product.material = form.material.data
    product.fit = form.fit.data
    product.sku = form.sku.data
    product.audience = form.audience.data
    product.product_type = form.product_type.data
    product.description = (form.description.data or "").strip()
    product.price = form.price.data
    product.is_limited = form.is_limited.data
    product.is_featured = form.is_featured.data
    product.is_active = form.is_active.data
    _apply_sizes(product, form.parsed_sizes)
    _apply_colors(product, form.color_keys.data)  # sudah divalidasi whitelist COLORS + 1–3 di form


SKU_TAKEN = "Kode (SKU) sudah dipakai produk lain."


def _sku_taken(sku, ignore_id=None):
    if not sku:
        return False
    query = db.select(Product.id).where(Product.sku == sku)
    if ignore_id:
        query = query.where(Product.id != ignore_id)
    return db.session.execute(query).first() is not None


def _commit_product(form):
    """Commit produk. False kalau ditolak UNIQUE sku (mis. dua admin menyimpan bersamaan)."""
    try:
        db.session.commit()
        return True
    except IntegrityError as e:
        db.session.rollback()
        constraint = getattr(getattr(e.orig, "diag", None), "constraint_name", "") or ""
        if "sku" in constraint or "sku" in str(e.orig):
            form.sku.errors.append(SKU_TAKEN)
        else:
            flash("Data gagal disimpan karena bentrok dengan data lain. Coba lagi.", "error")
        return False


@admin_bp.route("/produk")
def product_list():
    products = db.session.execute(
        db.select(Product)
        .options(
            selectinload(Product.sizes), selectinload(Product.brand), selectinload(Product.colors)
        )
        .order_by(Product.created_at.desc())
    ).scalars().all()
    return render_template("admin/product_list.html", products=products)


@admin_bp.route("/produk/baru", methods=["GET", "POST"])
def product_create():
    form = ProductForm()
    if not _fill_brand_choices(form):
        flash("Buat brand terlebih dahulu.", "error")
        return redirect(url_for("admin.brand_create"))

    if form.validate_on_submit():
        if _sku_taken(form.sku.data):
            form.sku.errors.append(SKU_TAKEN)
        else:
            # slug dibuat sebelum _fill_product supaya query cek slug tidak memicu autoflush
            product = Product(slug=slug_unik(Product, form.name.data.strip()))
            _fill_product(product, form)
            db.session.add(product)
            if _commit_product(form):
                catat("product_created", user=g.user, product_id=product.id, name=product.name)
                flash(f"Produk '{product.name}' ditambahkan.", "success")
                return redirect(url_for("admin.product_list"))

    return render_template("admin/product_form.html", form=form, title="Tambah Produk")


@admin_bp.route("/produk/<int:id>/edit", methods=["GET", "POST"])
def product_edit(id):
    product = db.get_or_404(Product, id)
    form = ProductForm(obj=product)
    _fill_brand_choices(form)

    if request.method == "GET":
        form.group_name.data = product.group.name if product.group else ""
        form.sizes.data = _sizes_to_text(product)

    if form.validate_on_submit():
        if _sku_taken(form.sku.data, ignore_id=product.id):
            form.sku.errors.append(SKU_TAKEN)
        else:
            # slug dihitung sebelum _fill_product (query slug tidak memicu autoflush data form)
            slug = slug_unik(Product, form.name.data.strip(), abaikan_id=product.id)
            _fill_product(product, form)
            product.slug = slug
            if _commit_product(form):
                catat("product_updated", user=g.user, product_id=product.id, name=product.name)
                flash("Produk diperbarui.", "success")
                return redirect(url_for("admin.product_list"))

    return render_template("admin/product_form.html", form=form, title="Edit Produk")


@admin_bp.route("/produk/<int:id>/status", methods=["POST"])
def product_toggle(id):
    product = db.get_or_404(Product, id)
    product.is_active = not product.is_active
    db.session.commit()
    catat(
        "product_shown" if product.is_active else "product_hidden",
        user=g.user, product_id=product.id, name=product.name,
    )
    state = "ditampilkan" if product.is_active else "disembunyikan"
    flash(f"Produk '{product.name}' {state}.", "success")
    return redirect(url_for("admin.product_list"))


@admin_bp.route("/produk/<int:id>/hapus", methods=["GET", "POST"])
def product_delete(id):
    product = db.get_or_404(Product, id)

    if product.is_active:
        flash("Sembunyikan produk terlebih dahulu sebelum menghapus permanen.", "error")
        return redirect(url_for("admin.product_list"))

    # Pesanan lama tetap aman (snapshot), ini hanya informasi untuk admin
    order_count = db.session.scalar(
        db.select(db.func.count(OrderItem.id))
        .join(ProductSize, ProductSize.id == OrderItem.product_size_id)
        .where(ProductSize.product_id == product.id)
    ) or 0

    form = DeleteProductForm()
    if form.validate_on_submit():
        if form.confirm.data.strip() != product.name:
            form.confirm.errors.append("Nama produk tidak cocok.")
        else:
            name = product.name
            db.session.delete(product)
            db.session.commit()
            catat("product_deleted", user=g.user, product_id=id, name=name)
            flash(f"Produk '{name}' dihapus permanen.", "success")
            return redirect(url_for("admin.product_list"))

    return render_template(
        "admin/product_delete.html", product=product, form=form, order_count=order_count
    )


# ---------- Audit log ----------

@admin_bp.route("/audit-log")
def audit_log():
    event = (request.args.get("event") or "").strip()[:50]
    date = (request.args.get("tanggal") or "").strip()
    page = request.args.get("page", 1, type=int)

    query = db.select(AuditLog).order_by(AuditLog.created_at.desc())

    if event:
        query = query.where(AuditLog.event == event)

    if date:
        try:
            start = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=WIB)
            query = query.where(
                AuditLog.created_at >= start,
                AuditLog.created_at < start + timedelta(days=1),
            )
        except ValueError:
            flash("Format tanggal tidak valid.", "error")
            date = ""

    pagination = db.paginate(query, page=page, per_page=50, error_out=False)

    events = db.session.execute(
        db.select(AuditLog.event).distinct().order_by(AuditLog.event)
    ).scalars().all()

    return render_template(
        "admin/audit_log.html",
        pagination=pagination,
        event=event,
        date=date,
        events=events,
    )

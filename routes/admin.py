from flask import Blueprint, render_template, redirect, url_for, flash, g, abort, current_app
from sqlalchemy.exc import IntegrityError

from extensions import db
from forms.admin import CategoryForm, ProductForm, HapusProdukForm
from models import Category, Product, User
from utils import slug_unik

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
def wajib_admin():
    if g.user is None:
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("auth.login"))
    if g.user.role != "admin":
        abort(403)


@admin_bp.route("/")
def dashboard():
    def hitung(query):
        return db.session.scalar(query) or 0

    stat = {
        "customer": hitung(db.select(db.func.count(User.id)).where(User.role == "customer")),
        "kategori": hitung(db.select(db.func.count(Category.id))),
        "produk_aktif": hitung(db.select(db.func.count(Product.id)).where(Product.is_active.is_(True))),
        "stok_habis": hitung(
            db.select(db.func.count(Product.id)).where(Product.is_active.is_(True), Product.stock == 0)
        ),
    }
    return render_template("admin/dashboard.html", stat=stat)


# ---------- Kategori ----------

@admin_bp.route("/kategori")
def kategori_list():
    daftar = db.session.execute(
        db.select(Category).order_by(Category.nama)
    ).scalars().all()
    return render_template("admin/kategori_list.html", daftar=daftar)


@admin_bp.route("/kategori/baru", methods=["GET", "POST"])
def kategori_baru():
    form = CategoryForm()
    if form.validate_on_submit():
        nama = form.nama.data.strip()
        kategori = Category(nama=nama, slug=slug_unik(Category, nama))
        db.session.add(kategori)
        db.session.commit()
        flash(f"Kategori '{nama}' ditambahkan.", "success")
        return redirect(url_for("admin.kategori_list"))
    return render_template("admin/kategori_form.html", form=form, judul="Tambah Kategori")


@admin_bp.route("/kategori/<int:id>/edit", methods=["GET", "POST"])
def kategori_edit(id):
    kategori = db.get_or_404(Category, id)
    form = CategoryForm(obj=kategori)
    if form.validate_on_submit():
        nama = form.nama.data.strip()
        kategori.nama = nama
        kategori.slug = slug_unik(Category, nama, abaikan_id=kategori.id)
        db.session.commit()
        flash("Kategori diperbarui.", "success")
        return redirect(url_for("admin.kategori_list"))
    return render_template("admin/kategori_form.html", form=form, judul="Edit Kategori")


@admin_bp.route("/kategori/<int:id>/hapus", methods=["POST"])
def kategori_hapus(id):
    kategori = db.get_or_404(Category, id)

    if kategori.products:
        flash("Kategori masih dipakai produk, tidak bisa dihapus.", "error")
        return redirect(url_for("admin.kategori_list"))

    db.session.delete(kategori)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Kategori masih dipakai produk, tidak bisa dihapus.", "error")
        return redirect(url_for("admin.kategori_list"))

    flash("Kategori dihapus.", "success")
    return redirect(url_for("admin.kategori_list"))


# ---------- Produk ----------

def _isi_pilihan_kategori(form):
    daftar = db.session.execute(
        db.select(Category).order_by(Category.nama)
    ).scalars().all()
    form.category_id.choices = [(k.id, k.nama) for k in daftar]
    return daftar


@admin_bp.route("/produk")
def produk_list():
    daftar = db.session.execute(
        db.select(Product).order_by(Product.created_at.desc())
    ).scalars().all()
    return render_template("admin/produk_list.html", daftar=daftar)


@admin_bp.route("/produk/baru", methods=["GET", "POST"])
def produk_baru():
    form = ProductForm()
    if not _isi_pilihan_kategori(form):
        flash("Buat kategori terlebih dahulu.", "error")
        return redirect(url_for("admin.kategori_baru"))

    if form.validate_on_submit():
        nama = form.nama.data.strip()
        produk = Product(
            nama=nama,
            slug=slug_unik(Product, nama),
            category_id=form.category_id.data,
            deskripsi=(form.deskripsi.data or "").strip(),
            harga=form.harga.data,
            stock=form.stock.data,
            is_active=form.is_active.data,
        )
        db.session.add(produk)
        db.session.commit()
        flash(f"Produk '{nama}' ditambahkan.", "success")
        return redirect(url_for("admin.produk_list"))

    return render_template("admin/produk_form.html", form=form, judul="Tambah Produk")


@admin_bp.route("/produk/<int:id>/edit", methods=["GET", "POST"])
def produk_edit(id):
    produk = db.get_or_404(Product, id)
    form = ProductForm(obj=produk)
    _isi_pilihan_kategori(form)

    if form.validate_on_submit():
        nama = form.nama.data.strip()
        produk.nama = nama
        produk.slug = slug_unik(Product, nama, abaikan_id=produk.id)
        produk.category_id = form.category_id.data
        produk.deskripsi = (form.deskripsi.data or "").strip()
        produk.harga = form.harga.data
        produk.stock = form.stock.data
        produk.is_active = form.is_active.data
        db.session.commit()
        flash("Produk diperbarui.", "success")
        return redirect(url_for("admin.produk_list"))

    return render_template("admin/produk_form.html", form=form, judul="Edit Produk")


@admin_bp.route("/produk/<int:id>/status", methods=["POST"])
def produk_status(id):
    produk = db.get_or_404(Product, id)
    produk.is_active = not produk.is_active
    db.session.commit()
    keadaan = "ditampilkan" if produk.is_active else "disembunyikan"
    flash(f"Produk '{produk.nama}' {keadaan}.", "success")
    return redirect(url_for("admin.produk_list"))


@admin_bp.route("/produk/<int:id>/hapus", methods=["GET", "POST"])
def produk_hapus(id):
    produk = db.get_or_404(Product, id)

    if produk.is_active:
        flash("Sembunyikan produk terlebih dahulu sebelum menghapus permanen.", "error")
        return redirect(url_for("admin.produk_list"))

    # Diisi setelah tabel order_items tersedia (fitur checkout)
    jumlah_pesanan = 0

    form = HapusProdukForm()
    if form.validate_on_submit():
        if form.konfirmasi.data.strip() != produk.nama:
            form.konfirmasi.errors.append("Nama produk tidak cocok.")
        else:
            nama = produk.nama
            db.session.delete(produk)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Produk tidak bisa dihapus karena masih dirujuk data lain.", "error")
                return redirect(url_for("admin.produk_list"))

            # Sementara ke log aplikasi; nanti diganti catat("product_deleted", ...)
            current_app.logger.warning(
                "product_deleted id=%s nama=%r oleh=%s", id, nama, g.user.email
            )
            flash(f"Produk '{nama}' dihapus permanen.", "success")
            return redirect(url_for("admin.produk_list"))

    return render_template(
        "admin/produk_hapus.html",
        produk=produk,
        form=form,
        jumlah_pesanan=jumlah_pesanan,
    )
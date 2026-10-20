from flask import Blueprint, render_template, redirect, url_for, flash, g, abort
from sqlalchemy.exc import IntegrityError

from extensions import db
from forms.admin import CategoryForm
from models import Category
from utils import slug_unik

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
def wajib_admin():
    if g.user is None:
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("auth.login"))
    if g.user.role != "admin":
        abort(403)


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
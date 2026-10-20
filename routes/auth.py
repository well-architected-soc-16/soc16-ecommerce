from flask import Blueprint, render_template, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError
from extensions import db
from forms.auth import RegisterForm
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        sudah_ada = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()
        if sudah_ada:
            flash("Email sudah terdaftar.", "error")
            return render_template("auth/register.html", form=form)

        user = User(nama=form.nama.data.strip(), email=email)
        user.set_password(form.password.data)
        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Email sudah terdaftar.", "error")
            return render_template("auth/register.html", form=form)

        flash("Pendaftaran berhasil. Silakan login.", "success")
        return redirect(url_for("index"))

    return render_template("auth/register.html", form=form)
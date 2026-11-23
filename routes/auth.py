from datetime import timedelta
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, session, g
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from audit import catat
from extensions import db
from forms.auth import RegisterForm, LoginForm
from models import User, now_utc

auth_bp = Blueprint("auth", __name__)

MAX_FAILED = 5
LOCK_DURATION = timedelta(minutes=15)
DUMMY_HASH = generate_password_hash("dummy-password-penyeimbang-waktu")


@auth_bp.before_app_request
def load_user():
    user_id = session.get("user_id")
    g.user = db.session.get(User, user_id) if user_id else None
    if g.user is not None and not g.user.is_active:
        session.clear()
        g.user = None


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if g.user is None:
            flash("Silakan login terlebih dahulu.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapper


def _home_for(user):
    return url_for("admin.dashboard") if user.is_admin else url_for("shop.index")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        exists = db.session.execute(
            db.select(User.id).filter_by(email=email)
        ).scalar_one_or_none()
        if exists:
            catat("register_failed", email=email, reason="email_taken")
            flash("Email sudah terdaftar.", "error")
            return render_template("auth/register.html", form=form)

        user = User(name=form.name.data.strip(), email=email)
        user.set_password(form.password.data)
        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            catat("register_failed", email=email, reason="email_taken")
            flash("Email sudah terdaftar.", "error")
            return render_template("auth/register.html", form=form)

        catat("register", user=user)
        flash("Pendaftaran berhasil. Silakan login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(_home_for(g.user))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if user is not None and user.is_locked():
            catat("login_failed", user=user, reason="account_locked")
            flash("Terlalu banyak percobaan gagal. Coba lagi beberapa menit lagi.", "error")
            return render_template("auth/login.html", form=form)

        if user is None:
            # Tetap hitung hash supaya waktu respons sama (cegah enumerasi email)
            check_password_hash(DUMMY_HASH, form.password.data)
            catat("login_failed", email=email, reason="unknown_email")
            flash("Email atau password salah.", "error")
            return render_template("auth/login.html", form=form)

        if not user.check_password(form.password.data):
            user.failed_login_count += 1
            locked = user.failed_login_count >= MAX_FAILED
            if locked:
                user.locked_until = now_utc() + LOCK_DURATION
                user.failed_login_count = 0
            db.session.commit()
            catat("login_failed", user=user, reason="wrong_password")
            if locked:
                catat("account_locked", user=user, minutes=int(LOCK_DURATION.total_seconds() // 60))
            flash("Email atau password salah.", "error")
            return render_template("auth/login.html", form=form)

        if not user.is_active:
            # Password benar tapi akun nonaktif: tidak menambah hitungan gagal
            catat("login_failed", user=user, reason="account_inactive")
            flash("Email atau password salah.", "error")
            return render_template("auth/login.html", form=form)

        user.failed_login_count = 0
        user.locked_until = None
        db.session.commit()

        session.clear()
        session["user_id"] = user.id
        catat("login_success", user=user)
        flash(f"Selamat datang, {user.name}.", "success")
        return redirect(_home_for(user))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    if g.user is not None:
        catat("logout", user=g.user)
    session.clear()
    flash("Anda sudah keluar.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profil")
@login_required
def profile():
    # Lewat template supaya nama di-escape otomatis (sebelumnya f-string → XSS)
    return render_template("auth/profile.html", user=g.user)

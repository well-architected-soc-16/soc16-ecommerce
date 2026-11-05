from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, session, g, abort
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from audit import catat
from extensions import db
from forms.auth import RegisterForm, LoginForm
from models import User

auth_bp = Blueprint("auth", __name__)

MAX_GAGAL = 5
LAMA_KUNCI = timedelta(minutes=15)
DUMMY_HASH = generate_password_hash("dummy-password-penyeimbang-waktu")


@auth_bp.before_app_request
def muat_user():
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


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if g.user is None:
            flash("Silakan login terlebih dahulu.", "error")
            return redirect(url_for("auth.login"))
        if g.user.role != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapper


def _halaman_awal(user):
    if user.role == "admin":
        return url_for("admin.dashboard")
    return url_for("index")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        sudah_ada = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()
        if sudah_ada:
            catat("register_failed", email=email, reason="email_terdaftar")
            flash("Email sudah terdaftar.", "error")
            return render_template("auth/register.html", form=form)

        user = User(nama=form.nama.data.strip(), email=email)
        user.set_password(form.password.data)
        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            catat("register_failed", email=email, reason="email_terdaftar")
            flash("Email sudah terdaftar.", "error")
            return render_template("auth/register.html", form=form)

        catat("register", user=user)
        flash("Pendaftaran berhasil. Silakan login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(_halaman_awal(g.user))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if user is not None and user.is_locked():
            catat("login_failed", user=user, reason="akun_terkunci")
            flash("Terlalu banyak percobaan gagal. Coba lagi beberapa menit lagi.", "error")
            return render_template("auth/login.html", form=form)

        if user is None:
            check_password_hash(DUMMY_HASH, form.password.data)
            password_benar = False
        else:
            password_benar = user.check_password(form.password.data)

        if not password_benar or not user.is_active:
            if user is None:
                catat("login_failed", email=email, reason="email_tidak_terdaftar")
            else:
                alasan = "akun_nonaktif" if password_benar else "password_salah"
                user.failed_login_count += 1
                terkunci = user.failed_login_count >= MAX_GAGAL
                if terkunci:
                    user.locked_until = datetime.now(timezone.utc) + LAMA_KUNCI
                    user.failed_login_count = 0
                db.session.commit()
                catat("login_failed", user=user, reason=alasan)
                if terkunci:
                    catat("account_locked", user=user, menit=int(LAMA_KUNCI.total_seconds() // 60))
            flash("Email atau password salah.", "error")
            return render_template("auth/login.html", form=form)

        user.failed_login_count = 0
        user.locked_until = None
        db.session.commit()

        session.clear()
        session["user_id"] = user.id
        catat("login_success", user=user)
        flash(f"Selamat datang, {user.nama}.", "success")
        return redirect(_halaman_awal(user))

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
def profil():
    return f"Halo {g.user.nama} ({g.user.email}) — role: {g.user.role}"
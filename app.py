from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from audit import init_audit, WIB
from config import Config
from extensions import db, migrate, csrf


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if app.config["TRUST_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    init_audit(app)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    import models  # noqa: F401  (daftarkan semua tabel untuk Flask-Migrate)

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.shop import shop_bp
    from routes.wishlist import wishlist_bp, wishlist_ids
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(wishlist_bp)

    # Global (bukan context processor) supaya terbaca juga di macro yang di-import, mis. product_card
    from utils import current_path, url_with
    app.jinja_env.globals.update(wishlist_ids=wishlist_ids, current_path=current_path, url_with=url_with)

    from commands import create_admin, seed, seed_reviews_command
    app.cli.add_command(create_admin)
    app.cli.add_command(seed)
    app.cli.add_command(seed_reviews_command)

    @app.template_filter("rupiah")
    def format_rupiah(value):
        return "Rp " + f"{value:,.0f}".replace(",", ".")

    from models import color_label, color_hex, convert_size
    app.add_template_filter(color_label, "color_label")   # convert eng ke ind
    app.add_template_filter(color_hex, "color_hex")       # convert eng ke #??????
    app.add_template_filter(convert_size, "size_us_uk")   # convert size ke uk,us

    @app.template_filter("wib")
    def format_wib(dt):
        return dt.astimezone(WIB).strftime("%d-%m-%Y %H:%M:%S") if dt else "-"

    MONTHS = ("Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des")

    @app.template_filter("tanggal")
    def format_tanggal(dt):
        """12 Nov 2026 (WIB)."""
        if not dt:
            return "-"
        dt = dt.astimezone(WIB)
        return f"{dt.day} {MONTHS[dt.month - 1]} {dt.year}"

    @app.template_filter("desimal")
    def format_desimal(value, places=1):
        """4.6 -> "4,6" (koma desimal Indonesia)."""
        return f"{value:.{places}f}".replace(".", ",")

    @app.template_filter("nama_singkat")
    def short_name(name):
        """Privasi ulasan: "Rina Putri Sari" -> "Rina S."; satu kata tetap utuh."""
        words = (name or "").split()
        if not words:
            return "Pembeli"
        return words[0] if len(words) == 1 else f"{words[0]} {words[-1][0].upper()}."

    @app.template_filter("inisial")
    def initials(name):
        words = (name or "").split()
        return "".join(w[0] for w in (words[:1] + words[1:][-1:])).upper() or "?"

    return app

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
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(shop_bp)

    from commands import create_admin, seed
    app.cli.add_command(create_admin)
    app.cli.add_command(seed)

    @app.template_filter("rupiah")
    def format_rupiah(value):
        return "Rp " + f"{value:,.0f}".replace(",", ".")

    @app.template_filter("wib")
    def format_wib(dt):
        return dt.astimezone(WIB).strftime("%d-%m-%Y %H:%M:%S") if dt else "-"

    return app

from flask import Flask, render_template

from config import Config
from extensions import db, migrate, csrf


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    import models  # noqa: F401
    from models import Product

    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from routes.admin import admin_bp
    app.register_blueprint(admin_bp)

    from routes.shop import shop_bp
    app.register_blueprint(shop_bp)

    from commands import buat_admin
    app.cli.add_command(buat_admin)

    @app.template_filter("rupiah")
    def format_rupiah(nilai):
        return "Rp " + f"{nilai:,.0f}".replace(",", ".")

    @app.route("/")
    def index():
        from routes.shop import data_katalog
        return render_template("index.html", **data_katalog())

    return app
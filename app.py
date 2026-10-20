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

    from commands import buat_admin
    app.cli.add_command(buat_admin)

    @app.template_filter("rupiah")
    def format_rupiah(nilai):
        return "Rp " + f"{nilai:,.0f}".replace(",", ".")

    @app.route("/")
    def index():
        produk = db.session.execute(
            db.select(Product)
            .where(Product.is_active.is_(True))
            .order_by(Product.created_at.desc())
            .limit(8)
        ).scalars().all()
        return render_template("index.html", produk=produk)

    return app
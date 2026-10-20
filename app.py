from flask import Flask
from config import Config
from extensions import db, migrate, csrf

#Def
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)       

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    import models
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)
#Route
    @app.route("/")                          
    def index():
        return "Dimas Kontol"              

    return app
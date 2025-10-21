from flask import Flask
from config.settings import Config
from extensions import db, migrate, login_manager, mail, cache
from config.mail_config import init_mail
import os

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cache.init_app(app)
    init_mail(app, mail)

    # Auto-register blueprints
    from blueprints import register_all_blueprints
    register_all_blueprints(app)

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))

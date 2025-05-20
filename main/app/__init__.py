from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config.from_object("config")

    from .routes.home import home_bp
    from .routes.test import test_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(test_bp)

    return app

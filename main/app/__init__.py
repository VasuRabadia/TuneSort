from flask import Flask
import os
from flask_session import Session


def create_app():
    app = Flask(__name__)
    app.config.from_object("config")
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-dev-key")
    app.config["SESSION_TYPE"] = "filesystem"
    Session(app)

    from .routes.add_tracks import add_tracks_bp
    from .routes.create_playlist import create_playlist_bp
    from .routes.home import home_bp
    from .routes.index import index_bp
    from .routes.playlists import playlists_bp
    from .routes.sort import sort_bp

    # from .routes.test import test_bp
    from .routes.tracks import tracks_bp
    from .routes.user import user_bp

    app.register_blueprint(add_tracks_bp)
    app.register_blueprint(create_playlist_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(index_bp)
    app.register_blueprint(playlists_bp)
    app.register_blueprint(sort_bp)
    # app.register_blueprint(test_bp)
    app.register_blueprint(tracks_bp)
    app.register_blueprint(user_bp)

    return app

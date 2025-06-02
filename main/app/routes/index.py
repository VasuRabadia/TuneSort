from flask import Blueprint, redirect
from dotenv import load_dotenv
import os

load_dotenv()

index_bp = Blueprint("index", __name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")


@index_bp.route("/")
def index():
    auth_url = (
        "https://accounts.spotify.com/authorize"
        "?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&scope=playlist-read-private%20playlist-modify-private%20playlist-modify-public%20playlist-read-collaborative%20user-read-private%20user-library-read"
        f"&redirect_uri={REDIRECT_URI}"
    )
    return redirect(auth_url)

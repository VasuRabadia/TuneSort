from flask import Blueprint, request, session, jsonify, redirect
from dotenv import load_dotenv
import requests
import os

load_dotenv()

home_bp = Blueprint("home", __name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")


@home_bp.route("/home")
def callback():
    code = request.args.get("code")

    # Exchange code for access token
    token_response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )

    if token_response.status_code != 200:
        return jsonify({"error": "Failed to get access token"}), 400

    tokens = token_response.json()

    # Store access token in session
    session["access_token"] = tokens.get("access_token")

    return redirect("/playlists")

from flask import Blueprint, session, jsonify
from dotenv import load_dotenv
import requests
import os
import json

load_dotenv()

playlists_bp = Blueprint("playlists", __name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")


@playlists_bp.route("/playlists")
def get_playlists():
    access_token = session.get("access_token")
    if not access_token:
        return (
            jsonify({"error": "Access token not found. Authorize first via /home"}),
            401,
        )

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get("https://api.spotify.com/v1/me/playlists", headers=headers)

    if response.status_code != 200:
        return (
            jsonify({"error": "Failed to fetch playlists", "details": response.json()}),
            response.status_code,
        )

    playlists_data = response.json()
    with open("main/data/playlists.json", "w", encoding="utf-8") as f:
        json.dump(playlists_data, f, ensure_ascii=False, indent=2)

    return jsonify(playlists_data)

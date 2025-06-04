from flask import Blueprint, session, jsonify
import requests

user_bp = Blueprint("user", __name__)


@user_bp.route("/user", methods=["GET"])
def user():
    access_token = session.get("access_token")
    if not access_token:
        return (
            jsonify({"error": "Access token not found. Authorize first via /home"}),
            401,
        )

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get("https://api.spotify.com/v1/me", headers=headers)

    if response.status_code != 200:
        return (
            jsonify({"error": "Failed to fetch playlists", "details": response.json()}),
            response.status_code,
        )

    return jsonify(response.json())

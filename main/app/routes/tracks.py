from flask import Blueprint, session, jsonify
import requests

tracks_bp = Blueprint("tracks", __name__)


@tracks_bp.route("/tracks")
def get_tracks():
    access_token = session.get("access_token")
    if not access_token:
        return (
            jsonify({"error": "Access token not found. Authorize first via /home"}),
            401,
        )

    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://api.spotify.com/v1/me/tracks?limit=50&offset=0"

    all_tracks = []
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return (
                jsonify(
                    {
                        "error": "Failed to fetch tracks songs",
                        "details": response.json(),
                    }
                ),
                response.status_code,
            )

        data = response.json()
        all_tracks.extend(data.get("items", []))
        url = data.get("next")  # URL for next page or None if done

    return jsonify({"items": all_tracks})

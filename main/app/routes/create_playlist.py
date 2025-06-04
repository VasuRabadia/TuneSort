from flask import Blueprint, request, session, jsonify, redirect
from dotenv import load_dotenv
import requests
import os

load_dotenv()

create_playlist_bp = Blueprint("create_playlist", __name__)


@create_playlist_bp.route(
    "/create_playlist/<user_id>/<playlist_name>", methods=["POST"]
)
def create_playlist(user_id, playlist_name):
    access_token = session.get("access_token")
    if not access_token:
        return (
            jsonify({"error": "Access token not found. Authorize first via /home"}),
            401,
        )

    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "name": playlist_name,
        "description": "Playlist created via TuneSort",
        "public": False,
    }

    response = requests.post(
        f"https://api.spotify.com/v1/users/{user_id}/playlists",
        headers=headers,
        json=data,
    )
    if response.status_code != 201:
        return (
            jsonify({"error": "Failed to create playlist", "details": response.json()}),
            response.status_code,
        )
    playlist_info = {
        "playlist_id": response["id"],
        "playlist_name": response["name"],
        "status_code": response.status_code,
    }
    return jsonify(playlist_info)

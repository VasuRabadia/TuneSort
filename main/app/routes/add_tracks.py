from flask import Blueprint, session, jsonify, request
import requests


add_tracks_bp = Blueprint("add_tracks", __name__)


@add_tracks_bp.route("/add_tracks/<playlist_id>", methods=["POST"])
def add_tracks(playlist_id):
    access_token = session.get("access_token")
    if not access_token:
        return (
            jsonify({"error": "Access token not found. Authorize first via /home"}),
            401,
        )

    headers = {"Authorization": f"Bearer {access_token}"}

    data = request.get_json()
    track_ids = data.get("track_ids", [])
    tracks_url = request.host_url + f"playlist/{playlist_id}/tracks"
    tracks_info = requests.get(tracks_url, cookies=request.cookies).json()
    # print(f"TRACK_INFO: {tracks_info}")
    # return jsonify(tracks_info)
    ids_to_add = []

    if tracks_info:
        for id in track_ids:
            if id not in [track["id"] for track in tracks_info]:
                ids_to_add.append(id)
            if len(ids_to_add) == 100 or id == track_ids[-1]:
                url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
                response = requests.post(
                    url,
                    headers=headers,
                    json={
                        "uris": [
                            f"spotify:track:{ids_to_add[i]}"
                            for i in range(len(ids_to_add))
                        ]
                    },
                )
                ids_to_add.clear()
    else:
        ids_to_add = track_ids
        for i in range(0, len(ids_to_add), 100):
            url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
            response = requests.post(
                url,
                headers=headers,
                json={
                    "uris": [
                        f"spotify:track:{ids_to_add[j]}"
                        for j in range(i, min(i + 100, len(ids_to_add)))
                    ]
                },
            )

    return jsonify(response.json())

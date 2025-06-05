from flask import Blueprint, session, jsonify, render_template, request, redirect
from dotenv import load_dotenv
import requests
import os
import json

load_dotenv()

playlists_bp = Blueprint("playlists", __name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")


@playlists_bp.route("/playlists", methods=["GET", "POST"])
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
    # return jsonify(response_spotify.json())
    playlists = [
        {
            "id": "1",
            "name": "Liked Songs",
            "image": (f"liked_songs_no_bg.png"),
            "is_empty": False,
        }
    ]
    for item in playlists_data["items"]:
        if item.get("type") == "playlist":
            playlists.append(
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "image": (
                        item["images"][0]["url"]
                        if item.get("images")
                        else f"empty_playlist_no_bg.png"
                    ),
                    "is_empty": not bool(item.get("images")),
                }
            )
    playlist_map = {item["id"]: item["name"] for item in playlists}
    session["playlist_map"] = playlist_map

    if request.method == "POST":
        selected_data_raw = request.form.get("selected_data")
        new_output_playlists_raw = request.form.get("new_output_playlists")
        try:
            selected_data = json.loads(selected_data_raw)
        except Exception as e:
            return jsonify({"error": "Invalid data format", "details": str(e)}, 400)

        input_playlists = []
        output_playlists = []
        for pl in selected_data:
            playlist = {
                "type": pl["id"].split("_")[0],
                "id": pl["id"].split("_")[1],
                "name": pl["name"],
            }
            if playlist["type"] == "input":
                input_playlists.append(playlist)
            else:
                output_playlists.append(playlist)

        try:
            new_output_playlists = [
                " ".join(word.capitalize() for word in pl.strip().split())
                for pl in new_output_playlists_raw.split(",")
                if pl.strip()
            ]
        except Exception as e:
            new_output_playlists = []
            print(f"ERROR: {e}")

        user_url = request.host_url + f"/user"
        response = requests.get(user_url, cookies=request.cookies).json()
        if not response:
            return jsonify(
                {"error": "Failed to fetch user", "details": response},
                500,
            )
        user_id = response.get("id")

        playlist_map = session.get("playlist_map", {})
        name_to_id_map = {name: pid for pid, name in playlist_map.items()}

        for pl in new_output_playlists:
            if pl not in name_to_id_map:
                create_playlist_url = (
                    request.host_url + f"create_playlist/{user_id}/{pl}"
                )
                response = requests.post(
                    create_playlist_url, cookies=request.cookies
                ).json()
                if response["status_code"] != 201:
                    return (
                        jsonify(
                            {"error": "Failed to create playlist", "details": response}
                        ),
                        response["status_code"],
                    )
                playlist_id = response["playlist_id"]
                playlist_name = response["playlist_name"]
                output_playlists.append(
                    {
                        "type": "output",
                        "id": playlist_id,
                        "name": playlist_name,
                    }
                )
                playlist_map[playlist_id] = playlist_name
                name_to_id_map[playlist_name] = playlist_id
            else:
                output_playlists.append(
                    {
                        "type": "output",
                        "id": name_to_id_map[pl],
                        "name": pl,
                    }
                )

        session["output_playlists"] = output_playlists

        tracks = []
        for pl in input_playlists:
            playlist_url = request.host_url + f"playlist/{pl["id"]}/tracks"
            tracks.append(requests.get(playlist_url, cookies=request.cookies).json())

        seen_ids = set()
        unique_tracks = []
        for track_list in tracks:
            for track in track_list.get("tracks", []):
                track_id = track.get("id")
                track_name = track.get("name")
                if track_name and track_id not in seen_ids:
                    seen_ids.add(track_id)
                    unique_tracks.append(track)

        session["unique_tracks"] = unique_tracks
        # return jsonify({"unique_tracks": unique_tracks})
        # return jsonify({"unique_tracks": unique_tracks})
        return redirect("/sort")
        # return redirect(f"/playlist/{selected_input[0]}/tracks")
    else:
        return render_template("index.html", playlists=playlists)

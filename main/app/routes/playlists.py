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
    # with open("main/data/playlists.json", "w") as f:
    #     json.dump(playlists_data, f)
    playlists = [{"id": "1", "name": "Liked Songs"}]
    for pl in playlists_data["items"]:
        if pl.get("type") == "playlist":
            playlists.append({"id": pl.get("id"), "name": pl.get("name")})
    playlist_map = {pl["id"]: pl["name"] for pl in playlists}
    session["playlist_map"] = playlist_map

    input_options = playlists.copy()
    output_options = playlists.copy()
    output_options.remove({"id": "1", "name": "Liked Songs"})

    if request.method == "POST":
        selected_input = request.form.getlist("input[]")
        selected_output = request.form.getlist("output[]")
        user_response = requests.get("https://api.spotify.com/v1/me", headers=headers)
        if user_response.status_code != 200:
            return {"error": "Failed to fetch user info"}, user_response.status_code
        user_id = user_response.json().get("id")
        if not user_id:
            return {"error": "User ID not found in response"}, 500
        all_tracks = []
        for pid in selected_input:
            playlist_url = request.host_url + f"playlist/{pid}/tracks"
            all_tracks.append(
                requests.get(playlist_url, cookies=request.cookies).json()
            )
        session["selected_output"] = selected_output
        session["all_tracks"] = all_tracks
        # return redirect("/sort")
        return redirect(f"/playlist/{selected_input[0]}/tracks")
    else:
        selected_input = ["1"]
        selected_output = []
        return render_template(
            "index.html",
            input_options=input_options,
            output_options=output_options,
            selected_input=selected_input,
            selected_output=selected_output,
        )

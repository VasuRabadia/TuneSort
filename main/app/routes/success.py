from flask import Blueprint, session, jsonify, render_template, request, redirect
from dotenv import load_dotenv

load_dotenv()

success_bp = Blueprint("success", __name__)


@success_bp.route("/success", methods=["GET", "POST"])
def success():
    output_playlists = session.get("output_playlists")
    name_to_id_map = session.get("name_to_id_map")
    print(f"name_to_id_map: {name_to_id_map}, type: {type(name_to_id_map)}")
    playlist_urls = {}
    for pl in output_playlists:
        print(f"Processing playlist: {pl}")
        playlist_id = name_to_id_map.get(pl["name"])
        playlist_urls[pl["name"]] = f"https://open.spotify.com/playlist/{playlist_id}"

    return render_template("success.html", playlist_urls=playlist_urls)

from flask import Blueprint, session, jsonify, render_template, request, redirect
from dotenv import load_dotenv
import requests
import os
import json
import google.generativeai as genai
import time

load_dotenv()

sort_bp = Blueprint("sort", __name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# models = genai.list_models()
# for model in models:
#     print(model.name)

model = genai.GenerativeModel("gemini-2.0-flash")


@sort_bp.route("/sort", methods=["GET", "POST"])
def sort_tracks():
    all_tracks = session.get("all_tracks")
    selected_output = session.get("selected_output")
    playlist_map = session.get("playlist_map")
    # print(playlist_map)
    playlists = [playlist_map[pid] for pid in selected_output if pid in playlist_map]

    result = []
    for ls in all_tracks:
        # print("LS:", ls)
        for tr in ls["tracks"]:
            track_name = tr["name"]
            track_artists = tr["artist"]
            track = track_name + " by " + ", ".join(track_artists)
            prompt = (
                f"From the following playlists: {playlists}, provide **only** a Python-style list "
                f'of playlist names where the song "{track}" would fit best. '
                f"If it doesn't fit any, respond with an empty list: [] . "
                f"Do not add any explanation or extra text."
            )
            response = model.generate_content(prompt)
            result.append(
                {
                    "track": track,
                    "playlist": response.candidates[0].content.parts[0].text,
                }
            )
            time.sleep(4)

    # print(result)
    return jsonify(result)

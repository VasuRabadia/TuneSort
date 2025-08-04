from flask import Blueprint, session, jsonify, request, render_template
from dotenv import load_dotenv
import os
import google.generativeai as genai
import requests
import time
from threading import Thread
from collections import defaultdict
import tracemalloc


from app.db.mongo import insert_update_entry, get_entry_by_track_id
from app.utils.dummy_response import DummyResponse
from app.utils.compute_weighted_result import compute_weighted_result
from app.routes.progress import update_progress


load_dotenv()

sort_bp = Blueprint("sort", __name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model_1_5_flash = genai.GenerativeModel("gemini-1.5-flash")
model_2_0_flash_lite = genai.GenerativeModel("gemini-2.0-flash-lite")
model_2_0_flash = genai.GenerativeModel("gemini-2.0-flash")


@sort_bp.route("/sort", methods=["GET"])
def sort_page():
    session_data = {
        "access_token": session.get("access_token"),
        "unique_tracks": session.get("unique_tracks"),
        "output_playlists": session.get("output_playlists"),
        "playlist_map": session.get("playlist_map"),
        "name_to_id_map": session.get("name_to_id_map"),
    }
    Thread(
        target=run_sorting_process,
        args=(session_data, request.host_url, request.cookies),
    ).start()
    return render_template("loading.html")


def run_sorting_process(session_data, host_url, cookies):
    tracemalloc.start()
    access_token = session_data.get("access_token")
    if not access_token:
        return (
            jsonify({"error": "Access token not found. Authorize first via /home"}),
            401,
        )

    unique_tracks = session_data.get("unique_tracks")
    total_tracks = len(unique_tracks)
    output_playlists = session_data.get("output_playlists")
    playlist_map = session_data.get("playlist_map")
    name_to_id_map = session_data.get("name_to_id_map", {})

    playlists = [
        playlist_map[pid["id"]] for pid in output_playlists if pid["id"] in playlist_map
    ]

    result_1_5_flash = []
    result_2_0_flash_lite = []
    result_2_0_flash = []
    track_final = {}
    sorted_tracks = 0

    for tr in unique_tracks:
        track_name = tr["name"]

        if track_name != "":
            update_progress(
                sorted=sorted_tracks,
                total=total_tracks,
                current_track=track_name,
                phase="Sorting Tracks",
            )
            track_id = tr["id"]
            prompt_playlists = playlists.copy()

            entry = get_entry_by_track_id(track_id)
            if entry:
                # print(f"ENTRY: {entry}")
                final_playlists = []
                for pl in entry.get("f", []):
                    if pl in prompt_playlists:
                        final_playlists.append(pl)
                for pl in entry.get("p", []):
                    if pl in prompt_playlists:
                        prompt_playlists.remove(pl)
                if final_playlists:
                    track_final[track_id] = final_playlists

            # print(f"prompt_playlists: {prompt_playlists}")

            DEBUG = False
            if not DEBUG:
                if prompt_playlists != []:
                    track_artists = tr["artist"]
                    track = track_name + " by " + ", ".join(track_artists)

                    print({"track_id": track_id, "track": track})
                    print(f"prompt_playlists: {prompt_playlists}")
                    prompt = (
                        f"You are an expert music classifier.\n\n"
                        f'Task: Classify the song "{track}" into one or more of the following user-defined playlists: {prompt_playlists}.\n\n'
                        f"Instructions:\n"
                        f'1. Each playlist name may include genre (e.g., "Pop", "HipHop"), mood (e.g., "Sad", "Happy", "Emotional"), language (e.g., "English", "Hindi", "Punjabi"), or context (e.g., "Party", "Car", "Workout", "Gaming").\n'
                        f'2. Some playlists have compound names (e.g., "Hindi-Party", "Sad-Car", "English-Dance"). These mean the song must satisfy **all parts** of the name. For example:\n'
                        f'   - "Hindi-Party" means the song must be **both in Hindi** and **suitable for parties**.\n'
                        f'   - "Sad-Car" means the song must be **sad** and **appropriate to play in a car**.\n'
                        f"3. Use your best understanding of the song’s genre, mood, lyrics, language, popularity, and energy.\n"
                        f"4. For each playlist, indicate how confident the AI model is that the song is a fit for that playlist, as a score between 0 and 1 (1 means very confident, 0 means not confident at all).\n"
                        f"5. Return only a valid **JSON-style dictionary** (in plain text) with playlist names as keys and confidence levels as float values.\n"
                        f"6. If the song does not belong in any playlist, return an empty dictionary: {{}}.\n\n"
                        f"Do NOT include any explanation, markdown, code block, or extra text.\n"
                        f"Do NOT wrap the output in ```json or ```python.\n"
                        f'Just return a raw dictionary string like this: {{"Pop": 0.957135842, "Romantic": 0.774135984, "English-Dance": 1.000000000}}'
                    )

                    skip_track = False
                    start_time = time.time()  # Start timer
                    try:
                        # print("1.5-flash model")
                        response_1_5_flash = model_1_5_flash.generate_content(prompt)
                    except Exception as e:
                        print(f"Error: {e}\nTrack ID: {track_id}\nTrack: {track}")
                        response_1_5_flash = DummyResponse()
                        skip_track = True

                    try:
                        # print("2.0-flash-lite model")
                        response_2_0_flash_lite = model_2_0_flash_lite.generate_content(
                            prompt
                        )
                    except Exception as e:
                        print(f"Error: {e}\nTrack ID: {track_id}\nTrack: {track}")
                        response_2_0_flash_lite = DummyResponse()
                        skip_track = True

                    try:
                        # print("2.0-flash model")
                        response_2_0_flash = model_2_0_flash.generate_content(prompt)
                    except Exception as e:
                        print(f"Error: {e}\nTrack ID: {track_id}\nTrack: {track}")
                        response_2_0_flash = DummyResponse()
                        skip_track = True

                    if not skip_track:
                        result_1_5_flash.append(
                            {
                                "track_id": track_id,
                                "track": track,
                                "playlist": response_1_5_flash.candidates[0]
                                .content.parts[0]
                                .text,
                            }
                        )
                        result_2_0_flash_lite.append(
                            {
                                "track_id": track_id,
                                "track": track,
                                "playlist": response_2_0_flash_lite.candidates[0]
                                .content.parts[0]
                                .text,
                            }
                        )
                        result_2_0_flash.append(
                            {
                                "track_id": track_id,
                                "track": track,
                                "playlist": response_2_0_flash.candidates[0]
                                .content.parts[0]
                                .text,
                            }
                        )

                        end_time = time.time()  # End timer
                        duration = end_time - start_time
                        print(f"Duration: {duration}")
                        if duration < 4:
                            time.sleep(4 - duration)
        sorted_tracks += 1
        # print(tracemalloc.get_traced_memory())
        current, peak = tracemalloc.get_traced_memory()
        print(f"Current memory usage: {current / 1024 / 1024:.2f} MB")
        print(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")
    tracemalloc.stop()

    update_progress(
        sorted=sorted_tracks,
        total=total_tracks,
        current_track=track_name,
        phase="Evluating Results",
    )

    weighted_result = compute_weighted_result(
        result_1_5_flash, result_2_0_flash_lite, result_2_0_flash
    )

    # return jsonify({"weighted_result": weighted_result})
    playlist_to_tracks = defaultdict(list)

    for entry in weighted_result:
        db_entry = {
            "tr_id": entry["track_id"],
            "p": playlists,
            "f": entry["final_ensemble_playlists"],
        }
        insert_update_entry(db_entry)
        track_id = entry["track_id"]
        track_final_playlists = (
            track_final.get(track_id, []) + entry["final_ensemble_playlists"]
        )
        for pl in track_final_playlists:
            pl_id = name_to_id_map.get(pl)
            # print(f"pl: {pl}, pl_id: {pl_id}")
            playlist_to_tracks[pl_id].append(track_id)

    update_progress(
        sorted=sorted_tracks,
        total=total_tracks,
        current_track=track_name,
        phase="Adding Tracks to Playlists",
    )

    for pl_id, track_ids in playlist_to_tracks.items():
        payload = {"track_ids": track_ids}
        # print(f"pl_id: {pl_id}, track_ids: {track_ids}")
        response = requests.post(
            host_url + f"add_tracks/{pl_id}",
            json=payload,
            cookies=cookies,
        )
        # return jsonify(response.json())

    playlist_urls = {}
    for pl_id in playlist_to_tracks:
        playlist_name = playlist_map.get(pl_id)
        if playlist_name:
            playlist_urls[playlist_name] = f"https://open.spotify.com/playlist/{pl_id}"

    return

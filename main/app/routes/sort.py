from flask import Blueprint, session, jsonify, render_template, request, redirect
from dotenv import load_dotenv
import requests
import os
import json
import google.generativeai as genai
import time
import ast
from collections import defaultdict

load_dotenv()

sort_bp = Blueprint("sort", __name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# models = genai.list_models()
# models_json = []
# for model in models:
#     print(model.name)
#     model_info = {
#         "name": model.name,
#         "base_model_id": getattr(model, "base_model_id", None),
#         "version": getattr(model, "version", None),
#         "display_name": getattr(model, "display_name", None),
#         "description": getattr(model, "description", None),
#         "input_token_limit": getattr(model, "input_token_limit", None),
#         "output_token_limit": getattr(model, "output_token_limit", None),
#         "supported_generation_methods": getattr(
#             model, "supported_generation_methods", []
#         ),
#         "temperature": getattr(model, "temperature", None),
#         "max_temperature": getattr(model, "max_temperature", None),
#         "top_p": getattr(model, "top_p", None),
#         "top_k": getattr(model, "top_k", None),
#     }
#     models_json.append(model_info)
# with open("main/data/models.json", "w") as f:
#     json.dump(models_json, f)

model_1_5_flash = genai.GenerativeModel("gemini-1.5-flash")
model_2_0_flash_lite = genai.GenerativeModel("gemini-2.0-flash-lite")
model_2_0_flash = genai.GenerativeModel("gemini-2.0-flash")


@sort_bp.route("/sort", methods=["GET", "POST"])
def sort_tracks():
    all_tracks = session.get("all_tracks")
    selected_output = session.get("selected_output")
    playlist_map = session.get("playlist_map")
    # print(playlist_map)
    playlists = [playlist_map[pid] for pid in selected_output if pid in playlist_map]

    result_1_5_flash = []
    result_2_0_flash_lite = []
    result_2_0_flash = []
    for ls in all_tracks:
        # print("LS:", ls)
        for tr in ls["tracks"]:
            # print("TR:", tr)
            start_time = time.time()  # Start timer

            track_id = tr["id"]
            track_name = tr["name"]
            track_artists = tr["artist"]

            if track_name != "":

                track = track_name + " by " + ", ".join(track_artists)

                print({"track_id": track_id, "track": track})

                prompt = (
                    f"You are an expert music classifier.\n\n"
                    f'Task: Classify the song "{track}" into one or more of the following user-defined playlists: {playlists}.\n\n'
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

                try:
                    response_1_5_flash = model_1_5_flash.generate_content(prompt)
                except Exception as e:
                    print(f"Error: {e}\nTrack ID: {track_id}\nTrack: {track}")
                    response_1_5_flash = DummyResponse()

                try:
                    response_2_0_flash_lite = model_2_0_flash_lite.generate_content(
                        prompt
                    )
                except Exception as e:
                    print(f"Error: {e}\nTrack ID: {track_id}\nTrack: {track}")
                    response_2_0_flash_lite = DummyResponse()

                try:
                    response_2_0_flash = model_2_0_flash.generate_content(prompt)
                except Exception as e:
                    print(f"Error: {e}\nTrack ID: {track_id}\nTrack: {track}")
                    response_2_0_flash = DummyResponse()

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
                print(duration)
                if duration < 4:
                    time.sleep(4 - duration)

    # print(result)
    result = []

    for i in range(len(result_1_5_flash)):
        # Ensure you're matching the same track across the lists
        if (
            result_1_5_flash[i]["track_id"]
            == result_2_0_flash_lite[i]["track_id"]
            == result_2_0_flash[i]["track_id"]
        ):
            track_id = result_1_5_flash[i]["track_id"]
            track = result_1_5_flash[i]["track"]

            # Convert string representations of lists to actual Python lists
            playlists_1_5 = ast.literal_eval(result_1_5_flash[i]["playlist"])
            playlists_lite = ast.literal_eval(result_2_0_flash_lite[i]["playlist"])
            playlists_2_0 = ast.literal_eval(result_2_0_flash[i]["playlist"])

            # Compute intersection
            common_playlists = list(
                set(playlists_1_5) & set(playlists_lite) & set(playlists_2_0)
            )

            result.append(
                {
                    "track_id": track_id,
                    "track": track,
                    "gemini-1.5-flash-playlists": list(playlists_1_5),
                    "gemini-2.0-flash-lite-playlists": list(playlists_lite),
                    "gemini-2.0-flash-playlists": list(playlists_2_0),
                    "common_playlists": common_playlists,
                }
            )
    # return jsonify(result)
    return compute_weighted_result(
        result_1_5_flash, result_2_0_flash_lite, result_2_0_flash
    )


def compute_weighted_result(
    result_1_5_flash, result_2_0_flash_lite, result_2_0_flash, threshold=0.87
):
    WEIGHTS = {
        "gemini-1.5-flash": 0.35,
        "gemini-2.0-flash-lite": 0.25,
        "gemini-2.0-flash": 0.40,
    }

    result = []

    for i in range(len(result_1_5_flash)):
        if (
            result_1_5_flash[i]["track_id"]
            == result_2_0_flash_lite[i]["track_id"]
            == result_2_0_flash[i]["track_id"]
        ):
            track_id = result_1_5_flash[i]["track_id"]
            track = result_1_5_flash[i]["track"]

            # Parse stringified dicts into actual Python dicts
            playlists_1_5 = ast.literal_eval(result_1_5_flash[i]["playlist"])
            playlists_lite = ast.literal_eval(result_2_0_flash_lite[i]["playlist"])
            playlists_2_0 = ast.literal_eval(result_2_0_flash[i]["playlist"])

            # Initialize dictionary to hold weighted scores
            tag_scores = defaultdict(float)

            # Add weighted scores from each model
            for tag, score in playlists_1_5.items():
                tag_scores[tag.strip()] += score * WEIGHTS["gemini-1.5-flash"]

            for tag, score in playlists_lite.items():
                tag_scores[tag.strip()] += score * WEIGHTS["gemini-2.0-flash-lite"]

            for tag, score in playlists_2_0.items():
                tag_scores[tag.strip()] += score * WEIGHTS["gemini-2.0-flash"]

            # Sort tags by final score (optional)
            sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)

            # Select only those with final score >= threshold
            final_tags = [tag for tag, score in sorted_tags if score >= threshold]

            result.append(
                {
                    "track_id": track_id,
                    "track": track,
                    "gemini-1.5-flash-playlists": playlists_1_5,
                    "gemini-2.0-flash-lite-playlists": playlists_lite,
                    "gemini-2.0-flash-playlists": playlists_2_0,
                    "ensemble_scores": dict(tag_scores),
                    "final_ensemble_playlists": final_tags,
                }
            )

    return jsonify(result)


class DummyResponse:
    def __init__(self, text="[]"):
        self.candidates = [self._Candidate(text)]

    class _Candidate:
        def __init__(self, text):
            self.content = self._Content(text)

        class _Content:
            def __init__(self, text):
                self.parts = [self._Part(text)]

            class _Part:
                def __init__(self, text):
                    self.text = text

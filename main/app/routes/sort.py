from flask import Blueprint, session, jsonify
from dotenv import load_dotenv
import os
import google.generativeai as genai
import time
import ast
from collections import defaultdict

from app.db.mongo import insert_update_entry, get_all_entries, get_entry_by_track_id
from app.assets.hybrid_dynamic_weight import compute_hybrid_weights, normalize
from app.assets.dummy_response import DummyResponse


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
# models_name = []
# with open("main/data/models_name.json", "w") as f:
#     for model in models_json:
#         models_name.append(model["name"])
#     json.dump(models_name, f)

model_1_5_flash = genai.GenerativeModel("gemini-1.5-flash")
model_2_0_flash_lite = genai.GenerativeModel("gemini-2.0-flash-lite")
model_2_0_flash = genai.GenerativeModel("gemini-2.0-flash")


@sort_bp.route("/sort", methods=["GET", "POST"])
def sort_tracks():
    access_token = session.get("access_token")
    if not access_token:
        return (
            jsonify({"error": "Access token not found. Authorize first via /home"}),
            401,
        )

    unique_tracks = session.get("unique_tracks")
    output_playlists = session.get("output_playlists")
    playlist_map = session.get("playlist_map")
    # print(playlist_map)
    # playlists = [playlist_map[pid] for pid in output_playlists if pid in playlist_map]
    playlists = [
        playlist_map[pid["id"]] for pid in output_playlists if pid["id"] in playlist_map
    ]
    # print(f"Playlists: {playlists}")

    result_1_5_flash = []
    result_2_0_flash_lite = []
    result_2_0_flash = []
    for tr in unique_tracks:
        track_name = tr["name"]

        if track_name != "":
            track_id = tr["id"]
            prompt_playlists = playlists.copy()

            entry = get_entry_by_track_id(track_id)
            if entry:
                # print(f"ENTRY: {entry}")
                for pl in entry.get("final_playlists", []):
                    if pl in prompt_playlists:
                        prompt_playlists.remove(pl)

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

                start_time = time.time()  # Start timer
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

    weighted_result = compute_weighted_result(
        result_1_5_flash, result_2_0_flash_lite, result_2_0_flash
    )

    for entry in weighted_result:
        db_entry = {
            "track_id": entry["track_id"],
            "track": entry["track"],
            "prompted_playlists": playlists,
            "final_playlists": entry["final_ensemble_playlists"],
        }
        insert_update_entry(db_entry)

    entries_list = list(get_all_entries(limit=20))
    return jsonify(entries_list)


def compute_weighted_result(
    result_1_5_flash,
    result_2_0_flash_lite,
    result_2_0_flash,
    prompt_playlists,
    threshold=0.87,
):

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

            model_outputs = {
                "gemini-1.5-flash": normalize(list(playlists_1_5.values())),
                "gemini-2.0-flash-lite": normalize(list(playlists_lite.values())),
                "gemini-2.0-flash": normalize(list(playlists_2_0.values())),
            }

            # Optional: define accuracy if using hybrid; remove to use entropy-only
            model_accuracies = {
                "gemini-1.5-flash": 0.84,
                "gemini-2.0-flash-lite": 0.76,
                "gemini-2.0-flash": 0.91,
            }

            # Compute hybrid weights
            weights = compute_hybrid_weights(model_outputs, model_accuracies)
            # print(f"WEIGHTS: {weights}")

            # Initialize dictionary to hold weighted scores
            tag_scores = defaultdict(float)

            # Add weighted scores from each model
            for tag, score in playlists_1_5.items():
                tag_scores[tag.strip()] += score * weights["gemini-1.5-flash"]

            for tag, score in playlists_lite.items():
                tag_scores[tag.strip()] += score * weights["gemini-2.0-flash-lite"]

            for tag, score in playlists_2_0.items():
                tag_scores[tag.strip()] += score * weights["gemini-2.0-flash"]

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
                    "ensemble_weights": weights,
                    "threshold": threshold,
                }
            )

    return result

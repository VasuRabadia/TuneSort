from flask import Blueprint, jsonify

progress_bp = Blueprint("progress", __name__)


progress_data = {
    "sorted": 0,
    "total": 0,
    "current_track": "",
    "phase": "Sorting Tracks",  # default phase
}


@progress_bp.route("/progress")
def progress():
    return jsonify(progress_data)


def update_progress(sorted, total, current_track="", phase="Sorting Tracks"):
    progress_data["sorted"] = sorted
    progress_data["total"] = total
    progress_data["current_track"] = current_track
    progress_data["phase"] = phase

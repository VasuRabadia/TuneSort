import ast
from collections import defaultdict
from app.utils.hybrid_dynamic_weight import compute_hybrid_weights, normalize
from app.utils.weights import compute_agreement_weights


def compute_weighted_result(
    result_1_5_flash,
    result_2_0_flash_lite,
    result_2_0_flash,
    threshold=0.81,
    alpha=0.5,  # weight blend: 0.5 = equal mix of hybrid and agreement
):

    result = []

    # --- Precompute agreement-based weights ---
    agreement_weights = compute_agreement_weights(
        result_1_5_flash, result_2_0_flash_lite, result_2_0_flash
    )

    for i in range(len(result_1_5_flash)):
        if (
            result_1_5_flash[i]["track_id"]
            == result_2_0_flash_lite[i]["track_id"]
            == result_2_0_flash[i]["track_id"]
        ):
            track_id = result_1_5_flash[i]["track_id"]
            track = result_1_5_flash[i]["track"]

            playlists_1_5 = ast.literal_eval(result_1_5_flash[i]["playlist"])
            playlists_lite = ast.literal_eval(result_2_0_flash_lite[i]["playlist"])
            playlists_2_0 = ast.literal_eval(result_2_0_flash[i]["playlist"])

            model_outputs = {
                "gemini-1.5-flash": normalize(list(playlists_1_5.values())),
                "gemini-2.0-flash-lite": normalize(list(playlists_lite.values())),
                "gemini-2.0-flash": normalize(list(playlists_2_0.values())),
            }

            model_accuracies = {
                "gemini-1.5-flash": 0.84,
                "gemini-2.0-flash-lite": 0.76,
                "gemini-2.0-flash": 0.91,
            }

            # --- Compute hybrid weights (accuracy × 1/entropy) ---
            hybrid_weights = compute_hybrid_weights(model_outputs, model_accuracies)

            # --- Combine both: weighted average ---
            combined_weights = {
                model: round(
                    alpha * hybrid_weights[model]
                    + (1 - alpha) * agreement_weights[model],
                    4,
                )
                for model in model_outputs
            }

            # --- Apply combined weights to scores ---
            tag_scores = defaultdict(float)

            for tag, score in playlists_1_5.items():
                tag_scores[tag.strip()] += score * combined_weights["gemini-1.5-flash"]
            for tag, score in playlists_lite.items():
                tag_scores[tag.strip()] += (
                    score * combined_weights["gemini-2.0-flash-lite"]
                )
            for tag, score in playlists_2_0.items():
                tag_scores[tag.strip()] += score * combined_weights["gemini-2.0-flash"]

            sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)
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
                    "ensemble_weights": combined_weights,
                    "threshold": threshold,
                }
            )

    return result

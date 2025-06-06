import numpy as np


def parse_playlists(result):
    return [eval(r["playlist"]) for r in result]


#  Build matrix of predictions per model
def build_matrix(parsed_results, all_keys):
    return [{k: d.get(k, 0.0) for k in all_keys} for d in parsed_results]


# Calculate MSE between each model and the average of the other two
def mse(model, other1, other2, num_tracks):
    if num_tracks == 0:
        return 0
    total_mse = 0
    for i in range(num_tracks):
        pred = np.array(list(model[i].values()))
        avg_other = (
            np.array(list(other1[i].values())) + np.array(list(other2[i].values()))
        ) / 2
        total_mse += ((pred - avg_other) ** 2).mean()
    return total_mse / num_tracks


def compute_agreement_weights(results_1_5, results_lite, results_2_0):
    p1 = parse_playlists(results_1_5)
    p2 = parse_playlists(results_lite)
    p3 = parse_playlists(results_2_0)

    num_tracks = len(p1)
    all_keys = set()
    for d in p1 + p2 + p3:
        all_keys.update(d.keys())

    m1 = build_matrix(p1, all_keys)
    m2 = build_matrix(p2, all_keys)
    m3 = build_matrix(p3, all_keys)

    mse_1 = mse(m1, m2, m3, num_tracks)
    mse_2 = mse(m2, m1, m3, num_tracks)
    mse_3 = mse(m3, m1, m2, num_tracks)

    # Convert MSEs to weights: lower error -> higher weight
    errors = np.array([mse_1, mse_2, mse_3])
    inverse_errors = 1 / errors
    weights = inverse_errors / inverse_errors.sum()

    return {
        "gemini-1.5-flash": round(weights[0], 3),
        "gemini-2.0-flash-lite": round(weights[1], 3),
        "gemini-2.0-flash": round(weights[2], 3),
    }

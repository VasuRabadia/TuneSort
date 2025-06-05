import numpy as np
from scipy.stats import entropy


def compute_hybrid_weights(model_outputs, model_accuracies):
    """
    Compute dynamic hybrid weights using (accuracy × 1/entropy).

    Args:
        model_outputs (dict): {model_name: list of class probabilities}
        model_accuracies (dict): {model_name: float accuracy (0 to 1)}

    Returns:
        dict: normalized weights for each model
    """
    inverse_entropy_scores = {}
    hybrid_scores = {}

    for model, probs in model_outputs.items():
        prob_array = np.array(probs)
        ent = entropy(prob_array)
        inv_ent = 1 / (ent + 1e-6)  # Avoid divide-by-zero
        inverse_entropy_scores[model] = inv_ent

        acc = model_accuracies.get(model, 0.5)  # Default accuracy if unknown
        hybrid_scores[model] = acc * inv_ent

    total = sum(hybrid_scores.values())
    weights = {model: score / total for model, score in hybrid_scores.items()}
    return weights


def normalize(probs):
    total = sum(probs)
    return [p / total for p in probs] if total > 0 else [0 for _ in probs]

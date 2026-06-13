"""
Swin Transformer – Hybrid Deep Learning Simulation Engine.

Implements:
  • Shifted Window Multi-Head Self-Attention (SW-MSA)
    Attention(Q,K,V) = Softmax( QK^T / sqrt(d) + B ) V
  • Categorical Cross-Entropy loss
    L = -Σ y_c log(ŷ_c)
  • Full WSI → 256×256 patch tiling pipeline
"""

import math
import random
from typing import Any, Dict, List, Tuple


def _softmax(xs: List[float]) -> List[float]:
    mx = max(xs) if xs else 0.0
    exps = [math.exp(x - mx) for x in xs]
    s = sum(exps) + 1e-15
    return [e / s for e in exps]


def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


# ── SW-MSA ──────────────────────────────────────────────────────────
def sw_msa(
    Q: List[List[List[float]]],   # [heads][tokens][d_head]
    K: List[List[List[float]]],
    V: List[List[List[float]]],
    d: int,
    B: List[List[float]],         # [tokens][tokens] position bias
) -> List[List[List[float]]]:
    """Shifted Window Multi-Head Self-Attention."""
    n_heads = len(Q)
    n_tok = len(Q[0])
    d_head = len(Q[0][0])
    scale = 1.0 / math.sqrt(d)

    out = []
    for h in range(n_heads):
        head = []
        for q in range(n_tok):
            scores = [((_dot(Q[h][q], K[h][k]) * scale) + B[q][k]) for k in range(n_tok)]
            w = _softmax(scores)
            vec = [sum(w[t] * V[h][t][di] for t in range(n_tok)) for di in range(d_head)]
            head.append(vec)
        out.append(head)
    return out


# ── Cross-Entropy ───────────────────────────────────────────────────
def cross_entropy(y_true: List[float], y_pred: List[float]) -> float:
    eps = 1e-15
    return -sum(yt * math.log(max(eps, min(1 - eps, yp))) for yt, yp in zip(y_true, y_pred))


# ── Single patch inference ──────────────────────────────────────────
def _infer_patch(x: int, y: int, threshold: float) -> Tuple[str, List[float], List[Dict]]:
    rng = random.Random(x * 100 + y)
    nh, nt, dh = 2, 4, 8
    d = nh * dh

    Q = [[[rng.gauss(0.1, 0.2) for _ in range(dh)] for _ in range(nt)] for _ in range(nh)]
    K = [[[rng.gauss(0.1, 0.2) for _ in range(dh)] for _ in range(nt)] for _ in range(nh)]
    V = [[[rng.gauss(0.5, 0.3) for _ in range(dh)] for _ in range(nt)] for _ in range(nh)]
    B = [[rng.gauss(0.01, 0.05) for _ in range(nt)] for _ in range(nt)]

    att = sw_msa(Q, K, V, d, B)

    mean_act = sum(abs(att[h][t][di]) for h in range(nh) for t in range(nt) for di in range(dh)) / (nh * nt * dh)

    if mean_act > 0.65:
        grade, probs = "severe", [0.10, 0.20, 0.65, 0.05]
    elif mean_act > 0.52:
        grade, probs = "moderate", [0.15, 0.60, 0.15, 0.10]
    elif mean_act > 0.40:
        grade, probs = "mild", [0.55, 0.25, 0.05, 0.15]
    else:
        grade, probs = "normal", [0.05, 0.05, 0.02, 0.88]

    boxes: List[Dict] = []
    if grade != "normal":
        features_pool = {
            "severe": [
                "Atypical Mitotic Figure",
                "Dyskeratotic Cell",
                "Loss of Intercellular Cohesion",
                "Drop-shaped Rete Ridge",
                "Suprabasal Mitotic Figure"
            ],
            "moderate": [
                "Loss of Epithelial Stratification",
                "Loss of Basal Cell Polarity",
                "Severe Nuclear Pleomorphism",
                "Pronounced Hyperchromatism",
                "Nuclear Enlargement"
            ],
            "mild": [
                "Basal Cell Hyperplasia",
                "Basal Mitotic Figure",
                "Mild Nuclear Pleomorphism",
                "Mild Hyperchromatism",
                "Epithelial Crowding"
            ]
        }.get(grade, [])
        
        # Select a few unique features from the pool
        selected_features = rng.sample(features_pool, min(len(features_pool), rng.randint(2, 4)))
        
        for feature in selected_features:
            cx, cy = rng.uniform(40, 216), rng.uniform(40, 216)
            sz = {"severe": (35, 55), "moderate": (24, 38), "mild": (14, 24)}.get(grade, (8, 14))
            half = rng.uniform(*sz) / 2
            conf = rng.uniform(0.60, 0.98)
            if conf >= threshold:
                boxes.append({
                    "xmin": round(cx - half, 2), "ymin": round(cy - half, 2),
                    "xmax": round(cx + half, 2), "ymax": round(cy + half, 2),
                    "grade": grade,
                    "label": feature,
                    "confidence": round(conf, 3),
                })

    return grade, probs, boxes


# ── Full pipeline ───────────────────────────────────────────────────
def run_inference(width: int, height: int, threshold: float = 0.5) -> Dict[str, Any]:
    """Tile a WSI into 256×256 patches and run SW-MSA on each."""
    tile = 256
    cols, rows = max(1, width // tile), max(1, height // tile)
    patches, counts = [], {"severe": 0, "moderate": 0, "mild": 0, "normal": 0}

    for r in range(rows):
        for c in range(cols):
            grade, probs, boxes = _infer_patch(c, r, threshold)
            counts[grade] += 1
            patches.append({
                "x_index": c, "y_index": r,
                "confidence_mild": probs[0], "confidence_moderate": probs[1],
                "confidence_severe": probs[2], "confidence_normal": probs[3],
                "predicted_grade": grade, "bounding_boxes": boxes,
            })

    total = len(patches)
    sr = counts["severe"] / total

    if sr > 0.08:
        overall, conf = "severe", min(0.85 + sr * 0.15, 0.99)
    elif counts["moderate"] / total > 0.15 or counts["severe"] > 0:
        overall, conf = "moderate", min(0.75 + counts["moderate"] / total * 0.2, 0.99)
    elif counts["mild"] / total > 0.2:
        overall, conf = "mild", min(0.70 + counts["mild"] / total * 0.25, 0.99)
    else:
        overall, conf = "normal", 0.90

    return {
        "overall_grade": overall,
        "overall_confidence": round(conf, 3),
        "patches": patches,
    }

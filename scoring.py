"""Scores a simulated shot string against a target definition."""

import math


def _distance(shot):
    return math.hypot(shot["x_cm"], shot["y_cm"])


def _group_size_cm(shots):
    biggest = 0.0
    for i in range(len(shots)):
        for j in range(i + 1, len(shots)):
            dx = shots[i]["x_cm"] - shots[j]["x_cm"]
            dy = shots[i]["y_cm"] - shots[j]["y_cm"]
            biggest = max(biggest, math.hypot(dx, dy))
    return biggest


def _mpi(shots):
    n = len(shots)
    if n == 0:
        return 0.0, 0.0
    return (
        sum(s["x_cm"] for s in shots) / n,
        sum(s["y_cm"] for s in shots) / n,
    )


def _score_bullseye(shots, target_def):
    rings = target_def["rings"]  # inner-first list of (score, outer_radius_cm)
    x_radius = target_def["x_ring_radius_cm"]
    total = 0
    x_count = 0
    per_shot = []
    for shot in shots:
        d = _distance(shot)
        score = 0
        for ring_score, radius in rings:
            if d <= radius:
                score = ring_score
                break
        total += score
        is_x = d <= x_radius
        if is_x:
            x_count += 1
        per_shot.append({"shot_index": shot["shot_index"], "score": score, "x": is_x})
    mpi_x, mpi_y = _mpi(shots)
    return {
        "target": "bullseye",
        "total_score": total,
        "x_count": x_count,
        "group_size_cm": _group_size_cm(shots),
        "mpi_x_cm": mpi_x,
        "mpi_y_cm": mpi_y,
        "per_shot": per_shot,
    }


def _hits_popper(shot, target_def):
    x, y = shot["x_cm"], shot["y_cm"]
    head_r = target_def["head_radius_cm"]
    if math.hypot(x, y) <= head_r:
        return True
    half_w = target_def["body_width_cm"] / 2.0
    top = target_def["body_top_y_cm"]
    bottom = top - target_def["body_height_cm"]
    return (-half_w <= x <= half_w) and (bottom <= y <= top)


def _score_popper(shots, target_def):
    neutralized = False
    shots_to_neutralize = None
    time_to_hit = None
    for shot in shots:
        if _hits_popper(shot, target_def):
            neutralized = True
            shots_to_neutralize = shot["shot_index"] + 1
            time_to_hit = shot["time_s"]
            break
    return {
        "target": "popper",
        "neutralized": neutralized,
        "shots_to_neutralize": shots_to_neutralize,
        "time_to_hit_s": time_to_hit,
        "group_size_cm": _group_size_cm(shots),
    }


def _score_ipsc(shots, target_def, string_time_s):
    zones = target_def["zones"]  # inner-first list of (label, points, hw, hh)
    total = 0
    misses = 0
    zone_counts = {label: 0 for label, _pts, _hw, _hh in zones}
    for shot in shots:
        x, y = shot["x_cm"], shot["y_cm"]
        matched = None
        for label, points, hw, hh in zones:
            if (x / hw) ** 2 + (y / hh) ** 2 <= 1.0:
                matched = (label, points)
                break
        if matched is None:
            misses += 1
        else:
            label, points = matched
            zone_counts[label] += 1
            total += points
    hit_factor = total / string_time_s if string_time_s and string_time_s > 0 else 0.0
    return {
        "target": "ipsc_silhouette",
        "total_points": total,
        "zone_counts": zone_counts,
        "misses": misses,
        "hit_factor": hit_factor,
        "group_size_cm": _group_size_cm(shots),
    }


def score_string(shots, target_def, string_time_s=None):
    """Score `shots` against `target_def`, dispatching on its ``type``.

    `string_time_s` is the total string time used for IPSC hit-factor scoring;
    it is ignored by other target types.
    """
    target_type = target_def["type"]
    if target_type == "bullseye":
        return _score_bullseye(shots, target_def)
    if target_type == "popper":
        return _score_popper(shots, target_def)
    if target_type == "ipsc_silhouette":
        return _score_ipsc(shots, target_def, string_time_s)
    raise ValueError(
        f"Invalid target type '{target_type}'. "
        f"Valid types are: bullseye, ipsc_silhouette, popper"
    )

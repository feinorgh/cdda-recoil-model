"""Target geometry definitions and authentic SVG target rendering."""

import html

TARGET_DEFS = {
    "bullseye": {
        "type": "bullseye",
        "name": "ISSF 25 m Precision",
        "rings": [
            (10, 2.5), (9, 5.0), (8, 7.5), (7, 10.0),
            (6, 12.5), (5, 15.0), (4, 17.5), (3, 20.0),
            (2, 22.5), (1, 25.0),
        ],
        "x_ring_radius_cm": 1.25,
        "black_radius_cm": 10.0,
        "size_cm": 55.0,
    },
    "ipsc_silhouette": {
        "type": "ipsc_silhouette",
        "name": "IPSC Metric (simplified)",
        "zones": [
            ("A", 5, 7.5, 15.0),
            ("C", 3, 15.0, 23.0),
            ("D", 1, 22.5, 30.0),
        ],
        "size_cm": 70.0,
    },
    "popper": {
        "type": "popper",
        "name": "IPSC Popper",
        "head_radius_cm": 15.0,
        "body_top_y_cm": -8.0,
        "body_width_cm": 20.0,
        "body_height_cm": 60.0,
        "size_cm": 80.0,
    },
}

# Layout constants (SVG pixels).
_FACE_PX = 360       # the target face occupies a square of this size
_PANEL_PX = 220      # width of the side stats panel
_MARGIN_PX = 20


def _scale(target_def):
    """Pixels per centimetre so the target's `size_cm` fills the face square."""
    return _FACE_PX / target_def["size_cm"]


def _to_px(x_cm, y_cm, target_def):
    """Target-plane cm (y up) -> SVG pixels (y down), centred in the face."""
    scale = _scale(target_def)
    cx = _MARGIN_PX + _FACE_PX / 2.0
    cy = _MARGIN_PX + _FACE_PX / 2.0
    return cx + x_cm * scale, cy - y_cm * scale


def _shot_markers(shots, target_def):
    parts = []
    for shot in shots:
        px, py = _to_px(shot["x_cm"], shot["y_cm"], target_def)
        parts.append(
            f'<circle class="shot" cx="{px:.1f}" cy="{py:.1f}" r="4" '
            f'fill="#c0392b" stroke="#ffffff" stroke-width="0.8"/>'
        )
    return "\n".join(parts)


def _stats_panel(lines):
    x = _MARGIN_PX * 2 + _FACE_PX
    parts = [f'<line x1="{x - 8}" y1="{_MARGIN_PX}" x2="{x - 8}" '
             f'y2="{_MARGIN_PX + _FACE_PX}" stroke="#dddddd"/>']
    y = _MARGIN_PX + 18
    for label, value in lines:
        parts.append(
            f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="12" '
            f'fill="#333333">{html.escape(str(label))}: '
            f'<tspan font-weight="bold">{html.escape(str(value))}</tspan></text>'
        )
        y += 20
    return "\n".join(parts)


def _svg_open():
    width = _MARGIN_PX * 3 + _FACE_PX + _PANEL_PX
    height = _MARGIN_PX * 2 + _FACE_PX
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">'
    )


def _render_bullseye(target_def, shots, score, run_meta):
    cx = _MARGIN_PX + _FACE_PX / 2.0
    cy = _MARGIN_PX + _FACE_PX / 2.0
    scale = _scale(target_def)
    parts = [_svg_open()]
    parts.append(
        f'<rect x="{_MARGIN_PX}" y="{_MARGIN_PX}" width="{_FACE_PX}" '
        f'height="{_FACE_PX}" fill="#f4f1e8" stroke="#999999"/>'
    )
    # Rings outer-first so inner rings draw on top.
    for ring_score, radius in reversed(target_def["rings"]):
        r = radius * scale
        black = radius <= target_def["black_radius_cm"]
        fill = "#111111" if black else "none"
        stroke = "#ffffff" if black else "#222222"
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="0.8"/>'
        )
    parts.append(_shot_markers(shots, target_def))
    parts.append(_stats_panel([
        ("Scenario", run_meta["scenario"]),
        ("Gun", run_meta["gun"]),
        ("Ammo", run_meta["ammo"]),
        ("Shooter", run_meta["shooter"]),
        ("Range", f'{run_meta["range_m"]} m'),
        ("String", f'{run_meta["shot_count"]} rds / {run_meta["time_limit_s"]} s'),
        ("Score", f'{score["total_score"]} ({score["x_count"]}X)'),
        ("Group", f'{score["group_size_cm"]:.1f} cm'),
        ("MPI", f'{score["mpi_x_cm"]:.1f}, {score["mpi_y_cm"]:.1f} cm'),
    ]))
    parts.append("</svg>")
    return "\n".join(parts)


def _render_popper(target_def, shots, score, run_meta):
    scale = _scale(target_def)
    head_cx, head_cy = _to_px(0.0, 0.0, target_def)
    head_r = target_def["head_radius_cm"] * scale
    half_w = target_def["body_width_cm"] / 2.0
    body_left_px, body_top_px = _to_px(-half_w, target_def["body_top_y_cm"], target_def)
    body_w_px = target_def["body_width_cm"] * scale
    body_h_px = target_def["body_height_cm"] * scale

    parts = [_svg_open()]
    parts.append(
        f'<rect x="{_MARGIN_PX}" y="{_MARGIN_PX}" width="{_FACE_PX}" '
        f'height="{_FACE_PX}" fill="#fbfbfb" stroke="#cccccc"/>'
    )
    parts.append(
        f'<rect x="{body_left_px:.1f}" y="{body_top_px:.1f}" '
        f'width="{body_w_px:.1f}" height="{body_h_px:.1f}" '
        f'fill="#8a847a" stroke="#333333"/>'
    )
    parts.append(
        f'<circle cx="{head_cx:.1f}" cy="{head_cy:.1f}" r="{head_r:.1f}" '
        f'fill="#b8b3a8" stroke="#333333" stroke-width="1.5"/>'
    )
    parts.append(_shot_markers(shots, target_def))
    if score.get("neutralized"):
        parts.append(
            f'<text x="{head_cx:.1f}" y="{head_cy:.1f}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="22" font-weight="bold" '
            f'fill="#1e8449" transform="rotate(-12 {head_cx:.1f} {head_cy:.1f})">'
            f'NEUTRALIZED</text>'
        )
    stn = score.get("shots_to_neutralize")
    tth = score.get("time_to_hit_s")
    parts.append(_stats_panel([
        ("Scenario", run_meta["scenario"]),
        ("Gun", run_meta["gun"]),
        ("Ammo", run_meta["ammo"]),
        ("Shooter", run_meta["shooter"]),
        ("Range", f'{run_meta["range_m"]} m'),
        ("Result", "Neutralized" if score.get("neutralized") else "Standing"),
        ("Shots to hit", stn if stn is not None else "-"),
        ("Time to hit", f'{tth:.2f} s' if tth is not None else "-"),
    ]))
    parts.append("</svg>")
    return "\n".join(parts)


def render_svg(target_def, shots, score, run_meta):
    """Render an authentic SVG target with shot markers and a stats panel."""
    target_type = target_def["type"]
    if target_type == "bullseye":
       return _render_bullseye(target_def, shots, score, run_meta)
    if target_type == "popper":
       return _render_popper(target_def, shots, score, run_meta)
    raise ValueError(
       f"Invalid target type '{target_type}'. "
       f"Valid types are: bullseye, ipsc_silhouette, popper"
    )

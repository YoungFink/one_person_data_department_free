"""
Panel 3 — shots following corners (panel_spec.md).

Definition, agreed: a shot counts if it is in the same `possession` as the
corner AND occurs within 15 seconds of the corner event. Route: join
data/pl_2015_16_events.parquet on match_id + possession, filter to shots by
the corner-taking team, apply the 15-second window.

Direct vs second-phase (CLAUDE.md): direct = the shot's event id is
referenced by pass_assisted_shot_id on the corner event (the corner ball
itself created the shot, no touch in between). Second-phase = any other
qualifying shot. Every corner-derived shot is one or the other, never both.

Fixed crop x >= 70, matching Panel 2 exactly (panel_spec.md addition) — not
tightened per team, so Panel 2 and Panel 3 render the same pitch at the same
scale side by side on Sheet 2.
"""

import sys
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data
import style

EVENTS_PATH = data.DATA_DIR / "pl_2015_16_events.parquet"
SHOT_WINDOW_SECONDS = 15

CROP_X_MIN = 70.0  # matches Panel 2's crop exactly
CROP_X_MAX = 122.0

EVENT_COLS = [
    "id", "match_id", "possession", "minute", "second", "team", "type",
    "shot_statsbomb_xg", "shot_outcome", "location", "period",
]


def get_corner_shots(team: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (shots_df, team_corners_df). shots_df has one row per
    qualifying shot with is_direct/is_goal flags; team_corners_df is the
    team's corner events (needed by the caller to print the source count)."""
    corners_df = data.load_corners()
    team_corners_df = data.team_corners(corners_df, team).copy()
    team_corners_df["elapsed"] = team_corners_df["minute"] * 60 + team_corners_df["second"]

    events = pd.read_parquet(EVENTS_PATH, columns=EVENT_COLS)
    shots = events[(events["type"] == "Shot") & (events["team"] == team)].copy()
    shots["elapsed"] = shots["minute"] * 60 + shots["second"]

    direct_shot_ids = set(team_corners_df["pass_assisted_shot_id"].dropna())

    windows = []
    for _, corner in team_corners_df.iterrows():
        window = shots[
            (shots["match_id"] == corner["match_id"])
            & (shots["possession"] == corner["possession"])
            & (shots["elapsed"] >= corner["elapsed"])
            & (shots["elapsed"] <= corner["elapsed"] + SHOT_WINDOW_SECONDS)
        ]
        if not window.empty:
            windows.append(window)

    if windows:
        qualifying = pd.concat(windows).drop_duplicates(subset="id").copy()
    else:
        qualifying = shots.iloc[0:0].copy()

    qualifying["is_direct"] = qualifying["id"].isin(direct_shot_ids)
    qualifying["is_goal"] = qualifying["shot_outcome"] == "Goal"

    return qualifying, team_corners_df


def xg_marker_size(xg: float) -> float:
    """Marker area scaled by xG, following the Opta reference's small-to-large
    bubble convention. Linear in xG, with a floor so even a near-zero chance
    still renders as a visible dot."""
    return 25 + xg * 700


def build_panel3(team: str, output_path: Path) -> dict:
    shots, team_corners_df = get_corner_shots(team)

    n_total = len(shots)
    n_goals = int(shots["is_goal"].sum())
    n_direct = int(shots["is_direct"].sum())
    n_second_phase = n_total - n_direct
    total_xg = float(shots["shot_statsbomb_xg"].sum())
    xg_per_shot = total_xg / n_total if n_total else 0.0

    counts = {
        "team": team,
        "corners_taken": len(team_corners_df),
        "shots_total": n_total,
        "goals": n_goals,
        "direct": n_direct,
        "second_phase": n_second_phase,
        "total_xg": round(total_xg, 3),
        "xg_per_shot": round(xg_per_shot, 3),
    }

    width_in = style.HALF_SHEET_WIDTH_IN
    pitch_h_in = width_in * 0.60
    stats_h_in = 1.35  # matches Panel 2 exactly, so the two sit flush side by side on Sheet 2
    caveat_h_in = 0.28
    height_in = pitch_h_in + stats_h_in + caveat_h_in

    fig = plt.figure(figsize=(width_in, height_in), dpi=style.DPI)
    fig.patch.set_facecolor(style.COLOR_PANEL_SURFACE)

    gs = fig.add_gridspec(
        3, 1, height_ratios=[pitch_h_in, caveat_h_in, stats_h_in],
        hspace=0.02, top=0.99, bottom=0.02, left=0.03, right=0.97,
    )
    ax_pitch = fig.add_subplot(gs[0])
    ax_caveat = fig.add_subplot(gs[1])
    ax_stats = fig.add_subplot(gs[2])
    for ax in (ax_caveat, ax_stats):
        ax.axis("off")

    pitch = VerticalPitch(
        pitch_type="statsbomb", half=True,
        pitch_color=style.COLOR_PANEL_SURFACE, line_color=style.COLOR_TEXT_MUTED,
        linewidth=1.4,
    )
    pitch.draw(ax=ax_pitch)
    ax_pitch.set_ylim(CROP_X_MIN, CROP_X_MAX)

    body_font = style.get_font_properties(style.FONT_BODY, "regular")
    body_bold_font = style.get_font_properties(style.FONT_BODY, "bold")
    mono_font = style.get_font_properties(style.FONT_MONO, "regular")

    non_goals = shots[~shots["is_goal"]]
    goals = shots[shots["is_goal"]]

    if not non_goals.empty:
        xs = non_goals["location"].apply(lambda loc: loc[0]).to_numpy()
        ys = non_goals["location"].apply(lambda loc: loc[1]).to_numpy()
        sizes = non_goals["shot_statsbomb_xg"].apply(xg_marker_size).to_numpy()
        pitch.scatter(
            xs, ys, ax=ax_pitch, s=sizes, facecolor="none",
            edgecolors=style.COLOR_TEXT_MUTED, linewidth=1.0, alpha=0.75, zorder=3,
        )
    if not goals.empty:
        xs = goals["location"].apply(lambda loc: loc[0]).to_numpy()
        ys = goals["location"].apply(lambda loc: loc[1]).to_numpy()
        sizes = goals["shot_statsbomb_xg"].apply(xg_marker_size).to_numpy()
        pitch.scatter(
            xs, ys, ax=ax_pitch, s=sizes, facecolor=style.COLOR_ACCENT,
            edgecolors=style.COLOR_ACCENT, linewidth=1.0, alpha=0.9, zorder=4,
        )

    # xG bubble-size legend, bottom-right of the pitch, matching the Opta
    # reference's small-to-large convention
    legend_xgs = [0.02, 0.15, 0.35, 0.65]
    legend_y = CROP_X_MIN + 3
    legend_x_start = 62
    for i, xg in enumerate(legend_xgs):
        lx = legend_x_start + i * 5
        ax_pitch.scatter(
            [lx], [legend_y], s=xg_marker_size(xg), facecolor="none",
            edgecolors=style.COLOR_TEXT_MUTED, linewidth=0.9, zorder=5,
            clip_on=False,
        )
    ax_pitch.text(legend_x_start - 3, legend_y, "Low xG", ha="right", va="center",
                  fontproperties=body_font, fontsize=6, color=style.COLOR_TEXT_MUTED)
    ax_pitch.text(legend_x_start + (len(legend_xgs) - 1) * 5 + 4, legend_y, "High xG",
                  ha="left", va="center", fontproperties=body_font, fontsize=6,
                  color=style.COLOR_TEXT_MUTED)

    ax_caveat.text(
        0.5, 0.5,
        "Shots in the same possession as a corner, within 15 seconds of the corner event.",
        ha="center", va="center", fontproperties=body_font, fontsize=6.5,
        color=style.COLOR_TEXT_MUTED, style="italic",
    )

    # Headline: direct vs second-phase split, the most prominent element in
    # the stats block per the brief.
    ax_stats.text(
        0.5, 0.86,
        f"{n_direct} direct   ·   {n_second_phase} second-phase",
        ha="center", va="center", fontproperties=body_bold_font, fontsize=13,
        color=style.COLOR_TEXT,
    )
    ax_stats.text(
        0.5, 0.68, f"of {n_total} shots from {len(team_corners_df)} corners",
        ha="center", va="center", fontproperties=body_font, fontsize=7.5,
        color=style.COLOR_TEXT_MUTED,
    )
    ax_stats.axhline(0.58, color=style.COLOR_BORDER, lw=0.8, xmin=0.15, xmax=0.85)

    stat_items = [
        ("Goals", n_goals),
        ("Shots", n_total),
        ("xG", f"{total_xg:.2f}"),
        ("xG / shot", f"{xg_per_shot:.2f}"),
    ]
    n_items = len(stat_items)
    for i, (label, value) in enumerate(stat_items):
        cx = (i + 0.5) / n_items
        ax_stats.text(cx, 0.36, f"{value}", ha="center", va="center",
                       fontproperties=mono_font, fontsize=15, color=style.COLOR_TEXT)
        ax_stats.text(cx, 0.10, label, ha="center", va="center",
                       fontproperties=body_font, fontsize=7, color=style.COLOR_TEXT_MUTED)

    ax_stats.set_xlim(0, 1)
    ax_stats.set_ylim(0, 1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=style.DPI, facecolor=style.COLOR_PANEL_SURFACE)
    plt.close(fig)

    counts["figure_width_in"] = width_in
    counts["figure_height_in"] = height_in
    counts["figure_width_px"] = round(width_in * style.DPI)
    counts["figure_height_px"] = round(height_in * style.DPI)
    return counts


if __name__ == "__main__":
    team = sys.argv[1] if len(sys.argv) > 1 else "Manchester United"
    out = Path(__file__).resolve().parent.parent / "outputs" / "panel3_test.png"
    result = build_panel3(team, out)
    print(f"Panel 3 built for {team}")
    for k, v in result.items():
        print(f"  {k}: {v}")
    print(f"  saved to: {out}")

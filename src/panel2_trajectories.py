"""
Panel 2 — corner delivery trajectories (panel_spec.md, incl. additions merged
2026-08-28).

Straight line from corner location to pass_end_location for every corner —
not an arc. StatsBomb records only the two points; a curved line would imply
a flight path and a curve direction that isn't in the data.

Colour by technique_bucket (src/data.py): Inswinging, Outswinging, Straight,
Untagged (no technique value) each get their own category — untagged is never
folded into straight. Colour mapping is specified in panel_spec.md, not
inferred.

Short corners (pass_length < 20) are NOT drawn on the pitch [addition] — they
read as failed deliveries fanning to the flag when drawn, but they're
successful routines. They appear as a count in the stats block only.

Lines are a faint background wash [addition]: low opacity, thin weight. End
points are the prominent element — larger, full opacity, coloured by
technique. No legend on the pitch [addition] — technique counts with colour
swatches live in the stats block below instead.

Fixed crop x >= 70 across all teams [addition] — not tightened per team, so
Panel 2 and (eventually) Panel 3 render the same pitch at the same scale.
"""

import sys
from pathlib import Path

import matplotlib
import matplotlib.font_manager as fm

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data
import style

CROP_X_MIN = 70.0  # fixed crop, shared with Panel 3, not tightened per team
CROP_X_MAX = 122.0  # small pad above the goal line for breathing room

# Colour mapping per panel_spec.md ("Colour mapping — specify it, don't infer
# it"). Short corners are not drawn, so they need no colour.
BUCKET_COLOR = {
    "Inswinging": style.COLOR_ACCENT,
    "Outswinging": style.COLOR_SECONDARY,
    "Straight": style.COLOR_TEXT,
    "Untagged": style.COLOR_TEXT_MUTED,
}
BUCKET_ORDER = ["Untagged", "Straight", "Outswinging", "Inswinging"]

LINE_ALPHA = 0.22
LINE_WIDTH = 0.7
POINT_ALPHA = 0.9
POINT_SIZE = 20


def build_panel2(team: str, output_path: Path) -> dict:
    df = data.load_corners()
    team_df = data.team_corners(df, team)

    n_total = len(team_df)
    n_short = int(team_df["is_short"].sum())
    n_delivered = n_total - n_short
    bucket_counts = team_df["technique_bucket"].value_counts().to_dict()
    for bucket in BUCKET_COLOR:
        bucket_counts.setdefault(bucket, 0)

    counts = {
        "team": team,
        "total": n_total,
        "short": n_short,
        "delivered": n_delivered,
        **{f"technique_{k.lower()}": v for k, v in bucket_counts.items()},
    }

    width_in = style.HALF_SHEET_WIDTH_IN
    pitch_h_in = width_in * 0.60
    stats_h_in = 1.35
    caveat_h_in = 0.28
    height_in = pitch_h_in + stats_h_in + caveat_h_in

    fig = plt.figure(figsize=(width_in, height_in), dpi=style.DPI)
    fig.patch.set_facecolor(style.COLOR_PANEL_SURFACE)

    gs = fig.add_gridspec(
        3,
        1,
        height_ratios=[pitch_h_in, caveat_h_in, stats_h_in],
        hspace=0.02,
        top=0.99,
        bottom=0.02,
        left=0.03,
        right=0.97,
    )
    ax_pitch = fig.add_subplot(gs[0])
    ax_caveat = fig.add_subplot(gs[1])
    ax_stats = fig.add_subplot(gs[2])
    for ax in (ax_caveat, ax_stats):
        ax.axis("off")

    pitch = VerticalPitch(
        pitch_type="statsbomb",
        half=True,
        pitch_color=style.COLOR_PANEL_SURFACE,
        line_color=style.COLOR_BORDER,
        linewidth=1.1,
    )
    pitch.draw(ax=ax_pitch)
    ax_pitch.set_ylim(CROP_X_MIN, CROP_X_MAX)  # fixed crop, panel_spec.md addition

    # Short corners are excluded here entirely — not drawn on the pitch at
    # any opacity. They are counted in the stats block below only.
    for bucket in BUCKET_ORDER:
        sub = team_df[(team_df["technique_bucket"] == bucket) & (~team_df["is_short"])]
        if sub.empty:
            continue
        x0 = sub["location"].apply(lambda loc: loc[0]).to_numpy()
        y0 = sub["location"].apply(lambda loc: loc[1]).to_numpy()
        x1 = sub["pass_end_location"].apply(lambda loc: loc[0]).to_numpy()
        y1 = sub["pass_end_location"].apply(lambda loc: loc[1]).to_numpy()
        color = BUCKET_COLOR[bucket]
        pitch.lines(
            x0, y0, x1, y1, ax=ax_pitch, color=color, alpha=LINE_ALPHA,
            lw=LINE_WIDTH, zorder=2,
        )
        pitch.scatter(
            x1, y1, ax=ax_pitch, color=color, alpha=POINT_ALPHA,
            s=POINT_SIZE, zorder=10, edgecolors="none",
        )

    body_font = style.get_font_properties(style.FONT_BODY, "regular")
    body_bold_font = style.get_font_properties(style.FONT_BODY, "bold")
    mono_font = style.get_font_properties(style.FONT_MONO, "regular")

    # No legend on the pitch (addition) — caveat text only here.
    ax_caveat.text(
        0.5, 0.5,
        "Lines show start and end location only, not ball flight — colour encodes technique, not curve.",
        ha="center", va="center", fontproperties=body_font, fontsize=6.5,
        color=style.COLOR_TEXT_MUTED, style="italic",
    )

    # Stats block: total/short/delivered as plain numbers, technique buckets
    # as colour swatch + count + label (the legend now lives here, not on
    # the pitch).
    plain_items = [
        ("Total corners", n_total),
        ("Short", n_short),
        ("Delivered", n_delivered),
    ]
    swatch_items = [(b, bucket_counts[b]) for b in BUCKET_ORDER]

    n_plain = len(plain_items)
    n_swatch = len(swatch_items)
    n_cols = n_plain + n_swatch
    for i, (label, value) in enumerate(plain_items):
        cx = (i + 0.5) / n_cols
        ax_stats.text(cx, 0.62, f"{value}", ha="center", va="center",
                       fontproperties=mono_font, fontsize=15, color=style.COLOR_TEXT)
        ax_stats.text(cx, 0.22, label, ha="center", va="center",
                       fontproperties=body_font, fontsize=7, color=style.COLOR_TEXT_MUTED)

    for j, (bucket, value) in enumerate(swatch_items):
        cx = (n_plain + j + 0.5) / n_cols
        ax_stats.scatter([cx - 0.045], [0.66], s=60, color=BUCKET_COLOR[bucket],
                          transform=ax_stats.transAxes, zorder=5, clip_on=False)
        ax_stats.text(cx + 0.02, 0.62, f"{value}", ha="left", va="center",
                       fontproperties=mono_font, fontsize=15, color=style.COLOR_TEXT)
        ax_stats.text(cx, 0.22, bucket, ha="center", va="center",
                       fontproperties=body_font, fontsize=7, color=style.COLOR_TEXT_MUTED)

    ax_stats.set_xlim(0, 1)
    ax_stats.set_ylim(0, 1)
    ax_stats.axhline(0.95, color=style.COLOR_BORDER, lw=0.8, xmin=0.02, xmax=0.98)

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
    out = Path(__file__).resolve().parent.parent / "outputs" / "panel2_test.png"
    result = build_panel2(team, out)
    print(f"Panel 2 built for {team}")
    for k, v in result.items():
        print(f"  {k}: {v}")
    print(f"  saved to: {out}")

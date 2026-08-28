"""
Panel 1 — zone grid, by side (panel_spec.md / CLAUDE.md "Zone grid (Panel 1)").

12 cells per side, mixed resolution, NOT mirrored. Two grids side by side:
left-side corners on the left, right-side corners on the right. Delivered
corners only (pass_length >= 20) — short corners are excluded from the grid
and stated separately so the numbers reconcile against the side's total.

Depth bands (x): six-yard box (x>=114), penalty spot (108<=x<114),
18-yard box (102<=x<108), edge of the area (x<102, drawn to x=84 as a visual
crop only — the cell's count still includes everything below x=84).

Width bands (y): flank cells (0-30, 50-80) anchored to the six-yard-box width
(mplsoccer statsbomb dims: six_yard_width=20, i.e. y=30 to y=50) — reverted
here after briefly anchoring to the wider penalty-area sidelines (y=18/62)
instead. That version widened the central fine band to 44 yards and put 47%
of deliveries in a single cell, destroying resolution in front of goal, which
is the panel's whole point. The real penalty-area sideline (y=18/62) now runs
through the interior of the flank cells instead of sitting on their edge —
accepted deliberately, since those cells carry well under 1% of deliveries
each: a misaligned line there costs nothing, where it would have cost
everything in the busiest cell. Central block (30-50, the six-yard-box width)
carries a fine 3-way split for the six-yard-box and penalty-spot rows, one
merged cell for the 18-yard-box row. Edge-of-the-area row keeps its own
separate coarse 3-way split (0-30, 30-50, 50-80).
"""

import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle

matplotlib.use("Agg")
from mplsoccer import VerticalPitch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data
import style

SIX_YARD_WIDTH_LEFT = 30.0   # six-yard-box width (mplsoccer dims: six_yard_width=20, centred)
SIX_YARD_WIDTH_RIGHT = 50.0
_CENTRAL_WIDTH = SIX_YARD_WIDTH_RIGHT - SIX_YARD_WIDTH_LEFT  # 20 yards, the six-yard-box width
FINE_BAND_EDGES = [
    SIX_YARD_WIDTH_LEFT,
    SIX_YARD_WIDTH_LEFT + _CENTRAL_WIDTH / 3,
    SIX_YARD_WIDTH_LEFT + 2 * _CENTRAL_WIDTH / 3,
    SIX_YARD_WIDTH_RIGHT,
]  # 30, 36.667, 43.333, 50
EDGE_ROW_BAND_EDGES = [0, 30, 50, 80]  # unchanged — edge row's own split
DEPTH_TOP = 120.0
DEPTH_SIX = 114.0
DEPTH_PEN = 108.0
DEPTH_EIGHTEEN = 102.0
DEPTH_CROP = 84.0  # visual crop only; membership for edge row is x < 102, unbounded
# Depth constants above verified against mplsoccer's own statsbomb pitch
# dimensions (VerticalPitch(pitch_type="statsbomb").dim): six_yard_right=114,
# penalty_right (spot)=108, penalty_area_right=102, right (goal line)=120 —
# exact match, so the drawn pitch and the cell grid align by construction,
# not by coincidence.
HEADER_UNITS = 12.0  # extra data-space above the grid, in the same axes, for the
                      # side title + front/back-post header — avoids relying on
                      # matplotlib's title/pad placement or off-axes text extrapolation
VIEW_TOP = DEPTH_TOP + HEADER_UNITS

CELL_ORDER = [
    "six_fine_0", "six_fine_1", "six_fine_2",
    "pen_fine_0", "pen_fine_1", "pen_fine_2",
    "eighteen_merged",
    "flank_left", "flank_right",
    "edge_left", "edge_mid", "edge_right",
]
COUNT_EXCEPTION_CELLS = {"flank_left", "flank_right", "edge_left", "edge_mid", "edge_right"}

ROW_LABELS = [
    ("Six-yard box", DEPTH_SIX, DEPTH_TOP),
    ("Penalty spot", DEPTH_PEN, DEPTH_SIX),
    ("18-yard box", DEPTH_EIGHTEEN, DEPTH_PEN),
    ("Edge of the area", DEPTH_CROP, DEPTH_EIGHTEEN),
]


def classify_cell(x: float, y: float) -> str:
    if x < DEPTH_EIGHTEEN:
        if y < EDGE_ROW_BAND_EDGES[1]:
            return "edge_left"
        elif y < EDGE_ROW_BAND_EDGES[2]:
            return "edge_mid"
        else:
            return "edge_right"
    if y < SIX_YARD_WIDTH_LEFT:
        return "flank_left"
    if y >= SIX_YARD_WIDTH_RIGHT:
        return "flank_right"
    if x >= DEPTH_SIX:
        row = "six"
    elif x >= DEPTH_PEN:
        row = "pen"
    else:
        return "eighteen_merged"
    if y < FINE_BAND_EDGES[1]:
        idx = 0
    elif y < FINE_BAND_EDGES[2]:
        idx = 1
    else:
        idx = 2
    return f"{row}_fine_{idx}"


def cell_rect(cell: str) -> tuple[float, float, float, float]:
    """Return (y0, y1, x0, x1) pitch-coordinate bounds for a cell."""
    if cell.startswith("six_fine_"):
        idx = int(cell[-1])
        return FINE_BAND_EDGES[idx], FINE_BAND_EDGES[idx + 1], DEPTH_SIX, DEPTH_TOP
    if cell.startswith("pen_fine_"):
        idx = int(cell[-1])
        return FINE_BAND_EDGES[idx], FINE_BAND_EDGES[idx + 1], DEPTH_PEN, DEPTH_SIX
    if cell == "eighteen_merged":
        return SIX_YARD_WIDTH_LEFT, SIX_YARD_WIDTH_RIGHT, DEPTH_EIGHTEEN, DEPTH_PEN
    if cell == "flank_left":
        return 0, SIX_YARD_WIDTH_LEFT, DEPTH_EIGHTEEN, DEPTH_TOP
    if cell == "flank_right":
        return SIX_YARD_WIDTH_RIGHT, 80, DEPTH_EIGHTEEN, DEPTH_TOP
    if cell == "edge_left":
        return 0, 30, DEPTH_CROP, DEPTH_EIGHTEEN
    if cell == "edge_mid":
        return 30, 50, DEPTH_CROP, DEPTH_EIGHTEEN
    if cell == "edge_right":
        return 50, 80, DEPTH_CROP, DEPTH_EIGHTEEN
    raise ValueError(cell)


def compute_side_grid(team_df, side: str) -> dict:
    side_df = team_df[team_df["side"] == side]
    delivered = side_df[~side_df["is_short"]]
    short_n = int(side_df["is_short"].sum())
    delivered_n = len(delivered)

    counts = {c: 0 for c in CELL_ORDER}
    for loc in delivered["pass_end_location"]:
        x, y = loc[0], loc[1]
        cell = classify_cell(x, y)
        counts[cell] += 1

    pct = {c: (counts[c] / delivered_n * 100 if delivered_n else 0.0) for c in CELL_ORDER}
    return {
        "side": side,
        "delivered_n": delivered_n,
        "short_n": short_n,
        "total_n": len(side_df),
        "counts": counts,
        "pct": pct,
    }


CMAP = LinearSegmentedColormap.from_list(
    "accent_ramp", [style.COLOR_PANEL_SURFACE, style.COLOR_ACCENT]
)


# Single consistent opacity for all 12 cells — shading intensity must map to
# percentage on one scale so cells can be compared by darkness alone.
# Flank boundaries sit at the six-yard-box width (30/50), not the penalty-area
# sidelines (18/62) — the real penalty-area line therefore runs through the
# interior of the flank cells, accepted deliberately: those cells carry well
# under 1% of deliveries each, so a misaligned line there costs nothing.
# Widening the central band to anchor on the penalty area instead was tried
# and reverted — it diluted the fine cells (up to 47% of deliveries landing
# in one cell), destroying resolution in front of goal.
CELL_ALPHA = 0.75


def draw_side_grid(ax, grid_info: dict, side: str, vmax: float):
    # [Addition] Draw the pitch: goal, six-yard box, penalty area, penalty
    # spot, penalty arc — via mplsoccer, not an abstract grid. Drawn BELOW
    # the shaded cells (line_zorder=1, rects at zorder=2) with a muted-text
    # line colour and heavier weight for real contrast against the shading —
    # a border-coloured line on top read as a ghost, not a pitch.
    pitch = VerticalPitch(
        pitch_type="statsbomb", half=True,
        pitch_color=style.COLOR_PANEL_SURFACE, line_color=style.COLOR_TEXT_MUTED,
        linewidth=2.0, line_zorder=1,
    )
    pitch.draw(ax=ax)

    ax.set_xlim(0, 80)
    ax.set_ylim(DEPTH_CROP, VIEW_TOP)
    ax.set_aspect("equal")
    ax.axis("off")

    body_font = style.get_font_properties(style.FONT_BODY, "regular")
    body_bold_font = style.get_font_properties(style.FONT_BODY, "bold")
    mono_font = style.get_font_properties(style.FONT_MONO, "regular")

    pct = grid_info["pct"]
    counts = grid_info["counts"]

    for cell in CELL_ORDER:
        y0, y1, x0, x1 = cell_rect(cell)
        color = CMAP(min(pct[cell] / vmax, 1.0) if vmax else 0.0)
        rect = Rectangle(
            (y0, x0), y1 - y0, x1 - x0,
            facecolor=color, edgecolor=style.COLOR_BORDER, linewidth=0.8,
            alpha=CELL_ALPHA, zorder=2,
        )
        ax.add_patch(rect)

        cy, cx = (y0 + y1) / 2, (x0 + x1) / 2
        if cell in COUNT_EXCEPTION_CELLS:
            label = f"{pct[cell]:.0f}%\n({counts[cell]})"
        else:
            label = f"{pct[cell]:.0f}%"
        text_color = style.COLOR_TEXT if pct[cell] < vmax * 0.55 else style.COLOR_PANEL_SURFACE
        ax.text(
            cy, cx, label, ha="center", va="center",
            fontproperties=mono_font, color=text_color,
            fontsize=6.5 if cell in COUNT_EXCEPTION_CELLS else 6.5,
            linespacing=1.3, zorder=5,
        )

    # front post / back post header
    if side == "Left":
        front_x, back_x = 5, 75
    else:
        front_x, back_x = 75, 5
    ax.text(front_x, DEPTH_TOP + 3.0, "FRONT POST", ha="center", va="bottom",
             fontproperties=body_bold_font, fontsize=7.5, color=style.COLOR_TEXT_MUTED)
    ax.text(back_x, DEPTH_TOP + 3.0, "BACK POST", ha="center", va="bottom",
             fontproperties=body_bold_font, fontsize=7.5, color=style.COLOR_TEXT_MUTED)

    ax.text(
        40, DEPTH_TOP + 9.0,
        f"{side} corners  —  delivered {grid_info['delivered_n']}, short {grid_info['short_n']} "
        f"(total {grid_info['total_n']})",
        ha="center", va="bottom", fontproperties=body_bold_font, fontsize=8.5,
        color=style.COLOR_TEXT,
    )


def draw_row_labels(ax):
    ax.set_xlim(0, 1)
    ax.set_ylim(DEPTH_CROP, VIEW_TOP)
    ax.axis("off")
    body_font = style.get_font_properties(style.FONT_BODY, "regular")
    for label, x0, x1 in ROW_LABELS:
        cx = (x0 + x1) / 2
        ax.text(0.95, cx, label, ha="right", va="center",
                 fontproperties=body_font, fontsize=6.8, color=style.COLOR_TEXT)


def build_panel1(team: str, output_path: Path) -> dict:
    df = data.load_corners()
    team_df = data.team_corners(df, team)

    left = compute_side_grid(team_df, "Left")
    right = compute_side_grid(team_df, "Right")
    vmax = max(max(left["pct"].values()), max(right["pct"].values()))

    margin_in = style.PANEL1_MARGIN_IN
    gap_in = style.PANEL1_GRID_GAP_IN
    gutter_in = 0.85  # row-label gutter, left grid only, own axes (not baked
                       # into ax_left's width — doing that instead breaks
                       # matplotlib's equal-aspect centering and clips labels)

    full_width_in = style.SHEET_WIDTH_IN
    plot_area_w = full_width_in - 2 * margin_in - gap_in - gutter_in
    grid_w_in = plot_area_w / 2  # each grid's own pitch-plot width (80 yards)
    # Header (title + front/back post row) lives inside the same axes as
    # extra data-space above the grid (VIEW_TOP), not as separate figure
    # margin — keeps aspect math single-source and avoids off-axes text
    # extrapolation / matplotlib's own title-placement guesswork.
    grid_h_in = grid_w_in * (VIEW_TOP - DEPTH_CROP) / 80

    caption_in = 0.34  # two caveat/exception lines below the grid
    outer_pad_in = 0.08  # slack above/below so nothing touches the canvas edge
    panel_h_in = grid_h_in + caption_in + 2 * outer_pad_in

    fig = plt.figure(figsize=(full_width_in, panel_h_in), dpi=style.DPI)
    fig.patch.set_facecolor(style.COLOR_PANEL_SURFACE)

    label_x0 = margin_in / full_width_in
    label_w = gutter_in / full_width_in
    left_x0 = (margin_in + gutter_in) / full_width_in
    left_w = grid_w_in / full_width_in
    right_x0 = (margin_in + gutter_in + grid_w_in + gap_in) / full_width_in
    right_w = grid_w_in / full_width_in

    grid_y0 = (caption_in + outer_pad_in) / panel_h_in
    grid_h = grid_h_in / panel_h_in

    ax_labels = fig.add_axes([label_x0, grid_y0, label_w, grid_h])
    ax_left = fig.add_axes([left_x0, grid_y0, left_w, grid_h])
    ax_right = fig.add_axes([right_x0, grid_y0, right_w, grid_h])

    draw_row_labels(ax_labels)
    draw_side_grid(ax_left, left, "Left", vmax=vmax)
    draw_side_grid(ax_right, right, "Right", vmax=vmax)

    body_font = style.get_font_properties(style.FONT_BODY, "regular")
    body_italic_kwargs = dict(fontproperties=body_font, fontsize=6.3,
                               color=style.COLOR_TEXT_MUTED, style="italic")
    fig.text(0.5, (outer_pad_in + caption_in * 0.72) / panel_h_in,
              "Caveat: pass_end_location is where the ball finished, not where it was aimed — "
              "a defensive clearance can look identical to an intentional near-post ball, "
              "especially in the front-post edge cell.",
              ha="center", va="center", **body_italic_kwargs)
    fig.text(0.5, (outer_pad_in + caption_in * 0.24) / panel_h_in,
              "Delivered corners only (short corners excluded, shown separately above). "
              "Percentage only in the 7 fine/merged cells; percentage + raw count in the 5 larger cells.",
              ha="center", va="center", **body_italic_kwargs)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=style.DPI, facecolor=style.COLOR_PANEL_SURFACE)

    # measure achieved fine-cell pixel size directly from the rendered axes,
    # not assumed from the inches math above
    fig.canvas.draw()
    y0, y1, x0, x1 = cell_rect("six_fine_1")  # a representative fine cell
    disp0 = ax_left.transData.transform((y0, x0))
    disp1 = ax_left.transData.transform((y1, x1))
    fine_cell_px_w = abs(disp1[0] - disp0[0])
    fine_cell_px_h = abs(disp1[1] - disp0[1])
    px_per_yard_left = fine_cell_px_w / (y1 - y0)

    ry0, ry1, rx0, rx1 = cell_rect("six_fine_1")
    rdisp0 = ax_right.transData.transform((ry0, rx0))
    rdisp1 = ax_right.transData.transform((ry1, rx1))
    px_per_yard_right = abs(rdisp1[0] - rdisp0[0]) / (ry1 - ry0)

    plt.close(fig)

    return {
        "team": team,
        "left_total": left["total_n"], "left_delivered": left["delivered_n"], "left_short": left["short_n"],
        "right_total": right["total_n"], "right_delivered": right["delivered_n"], "right_short": right["short_n"],
        "left_cell_counts": left["counts"], "right_cell_counts": right["counts"],
        "panel_width_in": full_width_in, "panel_height_in": round(panel_h_in, 3),
        "panel_width_px": round(full_width_in * style.DPI), "panel_height_px": round(panel_h_in * style.DPI),
        "px_per_yard_left": round(px_per_yard_left, 2),
        "px_per_yard_right": round(px_per_yard_right, 2),
        "fine_cell_px": (round(fine_cell_px_w, 1), round(fine_cell_px_h, 1)),
    }


if __name__ == "__main__":
    team = sys.argv[1] if len(sys.argv) > 1 else "Manchester United"
    out = Path(__file__).resolve().parent.parent / "outputs" / "panel1_test.png"
    result = build_panel1(team, out)
    print(f"Panel 1 built for {team}")
    for k, v in result.items():
        print(f"  {k}: {v}")
    print(f"  saved to: {out}")

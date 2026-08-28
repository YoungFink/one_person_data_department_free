"""
Sheet assembly (panel_spec.md "Sheet format").

Two A4 landscape sheets, 11.69 x 8.27in, PNG at 1754 x 1240 px each. Both
carry the same header and footer so either sheet works standalone.

Sheet 1: header, Panel 1 (full width), Panel 4 (rankings strip), footer.
Sheet 2: header, Panel 2 and Panel 3 side by side, footer.

Composition strategy: each component (header, panel, footer) is rendered as
its own matplotlib figure at the exact target width in inches — this keeps
DPI-derived pixel widths consistent across components without rescaling —
then composited onto a background canvas with PIL, at pixel offsets computed
from each component's own actual rendered size (not assumed from inches
math), so rounding in any one figure can't misalign the rest.
"""

import sys
from datetime import date
from pathlib import Path

import matplotlib
import matplotlib.image as mpimg

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel1_zonegrid
import panel2_trajectories
import panel3_shots
import panel4_rankings
import style

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def build_header(team: str, width_in: float, height_in: float, output_path: Path) -> Path:
    fig = plt.figure(figsize=(width_in, height_in), dpi=style.DPI)
    fig.patch.set_facecolor(style.COLOR_BACKGROUND)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    pad_frac_y = 0.12
    badge_path = style.get_badge_path(team)
    text_x = 0.015

    if badge_path is not None:
        img = mpimg.imread(badge_path)
        crest_h_frac = 1 - 2 * pad_frac_y
        crest_h_in = crest_h_frac * height_in
        crest_w_in = crest_h_in * (img.shape[1] / img.shape[0])
        crest_w_frac = crest_w_in / width_in
        ax_crest = fig.add_axes([0.015, pad_frac_y, crest_w_frac, crest_h_frac])
        ax_crest.imshow(img)
        ax_crest.axis("off")
        text_x = 0.015 + crest_w_frac + 0.015
    # Missing badge: render team name only — the sheet must not break
    # (CLAUDE.md "Branding assets are optional").

    heading_font = style.get_font_properties(style.FONT_HEADING)
    body_font = style.get_font_properties(style.FONT_BODY, "regular")

    ax.text(text_x, 0.64, team, fontproperties=heading_font, fontsize=24,
             color=style.COLOR_TEXT, ha="left", va="center")
    ax.text(text_x, 0.26, "Corners | Premier League 2015/16",
             fontproperties=body_font, fontsize=10.5, color=style.COLOR_TEXT_MUTED,
             ha="left", va="center")
    ax.axhline(0.02, color=style.COLOR_BORDER, lw=1.0, xmin=0, xmax=1)

    fig.savefig(output_path, dpi=style.DPI, facecolor=style.COLOR_BACKGROUND)
    plt.close(fig)
    return output_path


def build_footer(width_in: float, height_in: float, output_path: Path) -> Path:
    fig = plt.figure(figsize=(width_in, height_in), dpi=style.DPI)
    fig.patch.set_facecolor(style.COLOR_BACKGROUND)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axhline(0.85, color=style.COLOR_BORDER, lw=1.0, xmin=0, xmax=1)

    body_font = style.get_font_properties(style.FONT_BODY, "regular")
    mono_font = style.get_font_properties(style.FONT_MONO, "regular")

    pad_frac_y = 0.15
    sb_logo_path = style.get_statsbomb_logo_path()
    text_x = 0.015
    if sb_logo_path is not None:
        img = mpimg.imread(sb_logo_path)
        logo_h_frac = 1 - 2.4 * pad_frac_y
        logo_h_in = logo_h_frac * height_in
        logo_w_in = logo_h_in * (img.shape[1] / img.shape[0])
        logo_w_frac = logo_w_in / width_in
        ax_logo = fig.add_axes([0.015, pad_frac_y * 0.9, logo_w_frac, logo_h_frac])
        ax_logo.imshow(img)
        ax_logo.axis("off")
        text_x = 0.015 + logo_w_frac + 0.015
        ax.text(text_x, 0.40, "Data: StatsBomb Open Data", fontproperties=body_font,
                 fontsize=8.5, color=style.COLOR_TEXT_MUTED, ha="left", va="center")
    else:
        # StatsBomb attribution is not optional — text fallback if the logo
        # file is absent (CLAUDE.md).
        ax.text(text_x, 0.40, "Data: StatsBomb Open Data (StatsBomb)",
                 fontproperties=body_font, fontsize=8.5, color=style.COLOR_TEXT_MUTED,
                 ha="left", va="center")

    personal_logo_path = style.get_personal_logo_path()
    if personal_logo_path is not None:
        img = mpimg.imread(personal_logo_path)
        logo_h_frac = 1 - 2.4 * pad_frac_y
        logo_h_in = logo_h_frac * height_in
        logo_w_in = logo_h_in * (img.shape[1] / img.shape[0])
        logo_w_frac = logo_w_in / width_in
        ax_plogo = fig.add_axes([1 - 0.015 - logo_w_frac, pad_frac_y * 0.9, logo_w_frac, logo_h_frac])
        ax_plogo.imshow(img)
        ax_plogo.axis("off")
    # Missing personal logo: render the footer without it — StatsBomb
    # attribution and the generated date still appear (CLAUDE.md). No
    # personal logo file exists in this project, so this fallback is what
    # actually renders here.

    date_str = date.today().strftime("%-d %B %Y")
    ax.text(1 - 0.015, 0.40, f"Generated {date_str}", fontproperties=mono_font,
             fontsize=8, color=style.COLOR_TEXT_MUTED, ha="right", va="center")

    fig.savefig(output_path, dpi=style.DPI, facecolor=style.COLOR_BACKGROUND)
    plt.close(fig)
    return output_path


def _paste(canvas: Image.Image, img_path: Path, x_px: int, y_px: int) -> int:
    """Paste an image onto the canvas at (x_px, y_px); return its height."""
    img = Image.open(img_path).convert("RGBA")
    canvas.paste(img, (x_px, y_px), img)
    return img.height


def assemble_sheet1(team: str, output_path: Path) -> dict:
    bg = _hex_to_rgb(style.COLOR_BACKGROUND)
    canvas = Image.new("RGB", (style.OUTPUT_WIDTH_PX, style.OUTPUT_HEIGHT_PX), bg)

    header_path = OUTPUTS_DIR / "_header.png"
    footer_path = OUTPUTS_DIR / "_footer.png"
    panel1_path = OUTPUTS_DIR / "_sheet1_panel1.png"
    panel4_path = OUTPUTS_DIR / "_sheet1_panel4.png"

    build_header(team, style.SHEET_WIDTH_IN, 0.70, header_path)
    build_footer(style.SHEET_WIDTH_IN, 0.40, footer_path)
    panel1_counts = panel1_zonegrid.build_panel1(team, panel1_path)
    panel4_counts = panel4_rankings.build_panel4(team, panel4_path)

    header_h = Image.open(header_path).height
    footer_h = Image.open(footer_path).height
    panel1_h = Image.open(panel1_path).height
    panel4_h = Image.open(panel4_path).height

    outer_margin = round(0.30 * style.DPI)
    content_h = header_h + panel1_h + panel4_h + footer_h
    remaining = style.OUTPUT_HEIGHT_PX - 2 * outer_margin - content_h
    gap = max(remaining // 3, 0)

    y = outer_margin
    # Panel 1 is built at the FULL sheet width already (its own 0.15in
    # margins are baked into the image) — paste flush at x=0. Panel 4 is
    # built narrower (sheet width minus 2x margin), so it needs the offset
    # to align its edges with Panel 1's internal content margin.
    _paste(canvas, header_path, 0, y); y += header_h + gap
    _paste(canvas, panel1_path, 0, y); y += panel1_h + gap
    panel4_x = round(style.PANEL1_MARGIN_IN * style.DPI)
    _paste(canvas, panel4_path, panel4_x, y); y += panel4_h + gap
    y = style.OUTPUT_HEIGHT_PX - outer_margin - footer_h
    _paste(canvas, footer_path, 0, y)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)

    return {
        "sheet": 1, "team": team,
        "canvas_px": (style.OUTPUT_WIDTH_PX, style.OUTPUT_HEIGHT_PX),
        "header_h_px": header_h, "panel1_h_px": panel1_h,
        "panel4_h_px": panel4_h, "footer_h_px": footer_h, "gap_px": gap,
        "panel1_counts": panel1_counts, "panel4_counts": panel4_counts,
    }


def assemble_sheet2(team: str, output_path: Path) -> dict:
    bg = _hex_to_rgb(style.COLOR_BACKGROUND)
    canvas = Image.new("RGB", (style.OUTPUT_WIDTH_PX, style.OUTPUT_HEIGHT_PX), bg)

    header_path = OUTPUTS_DIR / "_header.png"
    footer_path = OUTPUTS_DIR / "_footer.png"
    panel2_path = OUTPUTS_DIR / "_sheet2_panel2.png"
    panel3_path = OUTPUTS_DIR / "_sheet2_panel3.png"

    build_header(team, style.SHEET_WIDTH_IN, 0.70, header_path)
    build_footer(style.SHEET_WIDTH_IN, 0.40, footer_path)
    panel2_counts = panel2_trajectories.build_panel2(team, panel2_path)
    panel3_counts = panel3_shots.build_panel3(team, panel3_path)

    header_h = Image.open(header_path).height
    footer_h = Image.open(footer_path).height
    panel2_img = Image.open(panel2_path)
    panel3_img = Image.open(panel3_path)
    row_h = max(panel2_img.height, panel3_img.height)

    outer_margin = round(0.30 * style.DPI)
    content_h = header_h + row_h + footer_h
    remaining = style.OUTPUT_HEIGHT_PX - 2 * outer_margin - content_h
    gap = max(remaining // 2, 0)

    y = outer_margin
    _paste(canvas, header_path, 0, y); y += header_h + gap

    # Panel 2 + gap + Panel 3 already sum to exactly the sheet width
    # (HALF_SHEET_WIDTH_IN is defined as (SHEET_WIDTH_IN - PANEL_GAP_IN) / 2
    # for this reason) — no additional outer margin, or the row overflows
    # the canvas on the right, same class of bug as Sheet 1's Panel 1 paste.
    panel_gap_x = round(style.PANEL_GAP_IN * style.DPI)
    _paste(canvas, panel2_path, 0, y)
    panel3_x = panel2_img.width + panel_gap_x
    _paste(canvas, panel3_path, panel3_x, y)
    y += row_h + gap

    y = style.OUTPUT_HEIGHT_PX - outer_margin - footer_h
    _paste(canvas, footer_path, 0, y)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)

    return {
        "sheet": 2, "team": team,
        "canvas_px": (style.OUTPUT_WIDTH_PX, style.OUTPUT_HEIGHT_PX),
        "header_h_px": header_h, "row_h_px": row_h, "footer_h_px": footer_h,
        "panel2_w_px": panel2_img.width, "panel3_w_px": panel3_img.width, "gap_px": gap,
        "panel2_counts": panel2_counts, "panel3_counts": panel3_counts,
    }


if __name__ == "__main__":
    team = sys.argv[1] if len(sys.argv) > 1 else "Manchester United"

    s1 = assemble_sheet1(team, OUTPUTS_DIR / "sheet1.png")
    print("=== Sheet 1 ===")
    for k, v in s1.items():
        print(f"  {k}: {v}")

    print()
    s2 = assemble_sheet2(team, OUTPUTS_DIR / "sheet2.png")
    print("=== Sheet 2 ===")
    for k, v in s2.items():
        print(f"  {k}: {v}")

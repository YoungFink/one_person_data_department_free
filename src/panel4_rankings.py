"""
Panel 4 — rankings strip (panel_spec.md).

Slim horizontal strip, text only, no chart. Six lines, each the team's value
and its rank out of 20 (rank 1 = highest value, applied consistently across
all six metrics — panel_spec.md doesn't distinguish "better" vs "worse"
direction per metric, so ranking by raw value descending is the plain,
checkable reading):

1. Corners taken
2. Short corner rate       — short / total corners, per team (CLAUDE.md def)
3. Inswinging share        — inswinging / delivered corners only (CLAUDE.md:
                              short corners excluded from both num & denom)
4. Shots from corners      — same possession + 15s window (CLAUDE.md def)
5. Goals from corners      — same shot set, shot_outcome == "Goal"
6. xG from corners         — same shot set, sum of shot_statsbomb_xg

No generated prose summary — rankings are countable and checkable; a written
judgement is not.
"""

import sys
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data
import style

EVENTS_PATH = data.DATA_DIR / "pl_2015_16_events.parquet"
SHOT_WINDOW_SECONDS = 15
EVENT_COLS = ["id", "match_id", "possession", "minute", "second", "team", "type",
              "shot_statsbomb_xg", "shot_outcome"]


def _corners_from_shots(team_corners: pd.DataFrame, team_shots: pd.DataFrame) -> pd.DataFrame:
    windows = []
    for _, corner in team_corners.iterrows():
        window = team_shots[
            (team_shots["match_id"] == corner["match_id"])
            & (team_shots["possession"] == corner["possession"])
            & (team_shots["elapsed"] >= corner["elapsed"])
            & (team_shots["elapsed"] <= corner["elapsed"] + SHOT_WINDOW_SECONDS)
        ]
        if not window.empty:
            windows.append(window)
    if windows:
        return pd.concat(windows).drop_duplicates(subset="id")
    return team_shots.iloc[0:0]


def compute_league_table() -> pd.DataFrame:
    corners = data.load_corners()
    corners["elapsed"] = corners["minute"] * 60 + corners["second"]
    teams = sorted(corners["team"].unique())

    events = pd.read_parquet(EVENTS_PATH, columns=EVENT_COLS)
    shots_all = events[events["type"] == "Shot"].copy()
    shots_all["elapsed"] = shots_all["minute"] * 60 + shots_all["second"]

    rows = []
    for team in teams:
        team_corners = corners[corners["team"] == team]
        total_n = len(team_corners)
        short_n = int(team_corners["is_short"].sum())
        delivered = team_corners[~team_corners["is_short"]]
        delivered_n = len(delivered)
        inswing_n = int((delivered["technique_bucket"] == "Inswinging").sum())

        team_shots = shots_all[shots_all["team"] == team]
        q = _corners_from_shots(team_corners, team_shots)

        rows.append({
            "team": team,
            "corners_taken": total_n,
            "short_rate": (short_n / total_n * 100) if total_n else 0.0,
            "inswinging_share": (inswing_n / delivered_n * 100) if delivered_n else 0.0,
            "shots": len(q),
            "goals": int((q["shot_outcome"] == "Goal").sum()),
            "xg": float(q["shot_statsbomb_xg"].sum()),
        })

    df = pd.DataFrame(rows).set_index("team")
    for col in ["corners_taken", "short_rate", "inswinging_share", "shots", "goals", "xg"]:
        df[f"{col}_rank"] = df[col].rank(ascending=False, method="min").astype(int)
    return df


METRICS = [
    ("corners_taken", "Corners taken", "{:.0f}"),
    ("short_rate", "Short corner rate", "{:.1f}%"),
    ("inswinging_share", "Inswinging share", "{:.1f}%"),
    ("shots", "Shots from corners", "{:.0f}"),
    ("goals", "Goals from corners", "{:.0f}"),
    ("xg", "xG from corners", "{:.2f}"),
]


def build_panel4(team: str, output_path: Path, league_table: pd.DataFrame | None = None) -> dict:
    if league_table is None:
        league_table = compute_league_table()
    row = league_table.loc[team]

    width_in = style.SHEET_WIDTH_IN - 2 * style.PANEL1_MARGIN_IN
    height_in = 0.62

    fig = plt.figure(figsize=(width_in, height_in), dpi=style.DPI)
    fig.patch.set_facecolor(style.COLOR_PANEL_SURFACE)
    ax = fig.add_axes([0.01, 0.05, 0.98, 0.9])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    mono_font = style.get_font_properties(style.FONT_MONO, "regular")
    body_font = style.get_font_properties(style.FONT_BODY, "regular")
    body_bold_font = style.get_font_properties(style.FONT_BODY, "bold")

    n = len(METRICS)
    for i, (col, label, fmt) in enumerate(METRICS):
        cx = (i + 0.5) / n
        value = fmt.format(row[col])
        rank = int(row[f"{col}_rank"])
        ax.text(cx, 0.68, value, ha="center", va="center",
                 fontproperties=mono_font, fontsize=16, color=style.COLOR_TEXT)
        ax.text(cx, 0.30, f"rank {rank} of 20", ha="center", va="center",
                 fontproperties=body_bold_font, fontsize=7, color=style.COLOR_ACCENT)
        ax.text(cx, 0.08, label, ha="center", va="center",
                 fontproperties=body_font, fontsize=7, color=style.COLOR_TEXT_MUTED)
        if i > 0:
            ax.axvline(i / n, color=style.COLOR_BORDER, lw=0.8, ymin=0.1, ymax=0.9)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=style.DPI, facecolor=style.COLOR_PANEL_SURFACE)
    plt.close(fig)

    counts = {"team": team}
    for col, label, fmt in METRICS:
        counts[col] = row[col]
        counts[f"{col}_rank"] = int(row[f"{col}_rank"])
    counts["figure_width_in"] = width_in
    counts["figure_height_in"] = height_in
    counts["figure_width_px"] = round(width_in * style.DPI)
    counts["figure_height_px"] = round(height_in * style.DPI)
    return counts


if __name__ == "__main__":
    team = sys.argv[1] if len(sys.argv) > 1 else "Manchester United"
    out = Path(__file__).resolve().parent.parent / "outputs" / "panel4_test.png"

    league_table = compute_league_table()

    pd.set_option("display.width", 200)
    pd.set_option("display.max_rows", 30)
    print("=== Full league table (all 20 teams) ===")
    display_cols = []
    for col, label, fmt in METRICS:
        display_cols += [col, f"{col}_rank"]
    print(league_table[display_cols].sort_values("corners_taken", ascending=False).round(2))
    print()

    result = build_panel4(team, out, league_table)
    print(f"Panel 4 built for {team}")
    for k, v in result.items():
        print(f"  {k}: {v}")
    print(f"  saved to: {out}")

"""
Shared derivations used by every panel. Definitions match CLAUDE.md exactly.
Change a definition here, not per-panel, so every sheet stays consistent.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

SHORT_THRESHOLD_YARDS = 20  # pass_length < 20 => short corner (CLAUDE.md)
SIDE_SPLIT_Y = 40  # location y < 40 => Left, else Right (CLAUDE.md)


def _technique_bucket(row) -> str:
    """Visual bucket for Panel 2. Short corners get their own category
    regardless of any technique tag (panel_spec.md) — length, not technique,
    decides whether a corner reads as 'short' here. Delivered corners split
    into Inswinging / Outswinging / Straight / Untagged."""
    if row["is_short"]:
        return "Short"
    tech = row["pass_technique"]
    return "Untagged" if pd.isna(tech) else tech


def load_corners() -> pd.DataFrame:
    df = pd.read_parquet(DATA_DIR / "pl_2015_16_corners.parquet").copy()
    df["is_short"] = df["pass_length"] < SHORT_THRESHOLD_YARDS
    df["side"] = df["location"].apply(
        lambda loc: "Left" if loc[1] < SIDE_SPLIT_Y else "Right"
    )
    df["technique_bucket"] = df.apply(_technique_bucket, axis=1)
    return df


def team_corners(df: pd.DataFrame, team: str) -> pd.DataFrame:
    return df[df["team"] == team].copy()

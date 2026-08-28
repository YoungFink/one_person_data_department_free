"""
Step 1 data pull: Premier League 2015/16 (StatsBomb open data).

Writes three files to data/:
  - pl_2015_16_matches.csv       one row per match
  - pl_2015_16_events.parquet    full event stream, all matches
  - pl_2015_16_corners.parquet   corner events only, derived from the events file

Corner definition (CLAUDE.md): type.name == "Pass" AND pass.type.name == "Corner".
Deliberately NOT play_pattern == "From Corner" — that tags every event in the
possession following a corner and massively overcounts.
"""

from pathlib import Path

import pandas as pd
from statsbombpy import sb

COMPETITION_ID = 2
SEASON_ID = 27  # Premier League 2015/2016

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

CORNER_FIELDS = [
    "id",
    "match_id",
    "team",
    "player",
    "location",
    "pass_end_location",
    "pass_length",
    "pass_height",
    "pass_technique",
    "pass_outcome",
    "pass_recipient",
    "pass_assisted_shot_id",
    "pass_shot_assist",
    "pass_goal_assist",
    "possession",
    "timestamp",
    "minute",
    "second",
]


def pull_matches() -> pd.DataFrame:
    matches = sb.matches(competition_id=COMPETITION_ID, season_id=SEASON_ID)
    return matches


def pull_all_events(match_ids: list[int]) -> pd.DataFrame:
    frames = []
    for i, match_id in enumerate(match_ids, 1):
        ev = sb.events(match_id=match_id)
        ev["match_id"] = match_id
        frames.append(ev)
        if i % 40 == 0 or i == len(match_ids):
            print(f"  pulled {i}/{len(match_ids)} matches")
    return pd.concat(frames, ignore_index=True)


def extract_corners(events: pd.DataFrame) -> pd.DataFrame:
    is_pass = events["type"] == "Pass"
    is_corner = events.get("pass_type") == "Corner"
    corners = events[is_pass & is_corner].copy()

    available = [c for c in CORNER_FIELDS if c in corners.columns]
    missing = [c for c in CORNER_FIELDS if c not in corners.columns]
    if missing:
        print(f"  note: fields not present in this pull, skipped: {missing}")

    return corners[available].reset_index(drop=True)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    print("Pulling match list...")
    matches = pull_matches()
    match_ids = matches["match_id"].tolist()
    print(f"  {len(match_ids)} matches found")

    matches_path = DATA_DIR / "pl_2015_16_matches.csv"
    matches.to_csv(matches_path, index=False)
    print(f"  wrote {matches_path}")

    print("Pulling full event stream for all matches (this is the slow step)...")
    events = pull_all_events(match_ids)
    print(f"  {len(events)} total events")

    events_path = DATA_DIR / "pl_2015_16_events.parquet"
    events.to_parquet(events_path, index=False)
    print(f"  wrote {events_path}")

    print("Extracting corners (type == Pass AND pass_type == Corner)...")
    corners = extract_corners(events)
    print(f"  {len(corners)} corners found")

    corners_path = DATA_DIR / "pl_2015_16_corners.parquet"
    corners.to_parquet(corners_path, index=False)
    print(f"  wrote {corners_path}")

    # Verification: corners taken == corners faced, per match.
    taken = corners.groupby("match_id").size()
    matches_indexed = matches.set_index("match_id")
    home_faced = matches_indexed["home_team"]
    away_faced = matches_indexed["away_team"]

    corners_by_team = corners.groupby(["match_id", "team"]).size().unstack(fill_value=0)

    mismatches = []
    for match_id in match_ids:
        if match_id not in corners_by_team.index:
            continue
        row = corners_by_team.loc[match_id]
        home = home_faced.loc[match_id]
        away = away_faced.loc[match_id]
        home_taken = row.get(home, 0)
        away_taken = row.get(away, 0)
        total_taken = home_taken + away_taken
        # corners "faced" by a team = corners taken by the opponent
        # taken == faced check is really: total corners in match accounted for
        # by exactly the two participating teams, nothing orphaned.
        if total_taken != taken.get(match_id, 0):
            mismatches.append(match_id)

    print()
    print("=== Summary ===")
    print(f"Matches: {len(match_ids)}")
    print(f"Total corners: {len(corners)}")
    print(f"Matches with corner-count mismatch (taken vs faced): {len(mismatches)}")
    if mismatches:
        print(f"  mismatched match_ids: {mismatches}")


if __name__ == "__main__":
    main()

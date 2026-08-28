# The One-Person Data Department — Set-Piece Sheet

## What this project is

A single deliverable: a **two-sheet** A4 opposition set-piece pack covering
corners, generated from StatsBomb open data. Two sheets, not one — the height
arithmetic doesn't support four panels at the quality each needs on a single
page. See "Sheet layout" below. Plus the ability to ask questions of the same
data conversationally in this session.

This is a teaching build. It is deliberately small. No database, no ingest layer,
no config system. Files on disk, one script per panel, PNG out (screen document,
not print — see Visual Identity).

## Who runs this

A football analyst, not a developer. Explain what you're doing in football terms.
Show your logic before your numbers. If something is a judgement call, say so and
let me decide rather than picking silently.

## Data

StatsBomb open data via `statsbombpy`. No authentication required.

**Free series competition:** Premier League 2015/16 (competition_id 2, season 2015/2016).
380 matches, 20 teams, 4,107 corners. No 360 data.

**Later, paid course only:** Bundesliga 2023/24. This is NOT the full league — it is
Bayer Leverkusen's title season only. Leverkusen appear in all 34 matches; every
other team appears twice. It has 360 data, so it is the right dataset for a
freeze-frame layer, but it cannot be used for league-wide comparison.

Attribution is required on every output: credit StatsBomb, use their logo from the
media pack.

### Files on disk

Pulled via `statsbombpy` and verified against the raw open-data JSON (exact match,
4,107 corners, identical per-team split) before saving.

- `data/pl_2015_16_matches.csv` — 380 matches, one row each. Team names, scores,
  date, competition stage. Use this to resolve opponent/date for a given match_id.
- `data/pl_2015_16_corners.parquet` — **the file src/ should load.** Every corner
  event only (4,107 rows), with the fields the sheet needs: taker, team, match_id,
  location, pass_end_location, pass_length/height/technique, pass_outcome,
  pass_recipient, pass_assisted_shot_id/shot_assist/goal_assist. Does not contain
  what happened after the corner — only the corner kick event itself.
- `data/pl_2015_16_events.parquet` — full event stream, all 380 matches
  (1,313,773 rows). Only needed for questions the corners file can't answer, e.g.
  first contact, second balls, or anything in the possession following a corner.
  Don't load this by default — it's ~400x the size of the corners file.

## Definitions — agreed, do not change without asking

**Corner:** `type.name == "Pass"` AND `pass.type.name == "Corner"`. This counts the
kick itself, one event per corner taken.

Do NOT use `play_pattern == "From Corner"` for counting. That field tags every event
in the possession sequence following a corner, so it massively overcounts. It is
useful for finding what happened AFTER a corner, not for counting corners.

**Short corner:** `pass.length < 20` yards.

This is a proxy, not a StatsBomb category. There is no short-corner tag in the data.
The 20-yard figure sits in the trough of a bimodal length distribution: a cluster
from roughly 2 to 26 yards, a sparse region around 16 to 20, then a dominant peak at
30 to 46 yards which is the corner-arc-to-six-yard-box distance.

Validated: all 97 corners in the 15 to 20 yard band end in the wide corridor
(y < 20 or y > 60), none in the central channel. So the band captures genuine short
routines, not compressed near-post deliveries. 94 of 97 are ground passes, and
93 of 97 were completed to a named recipient (96%).

Known sensitivity: league-wide short% moves from 9.0% at a 16-yard threshold to
13.0% at 24 yards. Rank order is stable at the top. **Stoke City are the exception** —
8 of their 15 short corners sit in the 15 to 20 band, so they move from rank 9 to
rank 16 depending on the cut. Flag this if Stoke are ever the subject team.

**Side:** derived from `location[1]` (y-coordinate) on the corner event.
y < 40 = Left, y >= 40 = Right. Verified empirically against average y-position of
players tagged Left Back (~12) and Right Back (~68).

**Technique bucket (Panel 2):** four categories, not three. Inswinging,
outswinging, straight, and a separate **untagged** category with its own count
shown. Do not fold untagged long balls (`pass_length >= 20` with no
`pass_technique` value — 233 corners league-wide) into "straight". They are not
the same thing: "straight" is a StatsBomb-assigned technique, "untagged" is an
absence of one. Naming the gap honestly beats hiding it in an existing bucket.

**Direct vs second-phase shot (Panel 3):** direct = a shot whose event id is
referenced by `pass_assisted_shot_id` on the corner event (the corner ball itself
created the shot, no touch in between). Second-phase = any other shot in the same
`possession` within the agreed 15-second window. Every corner-derived shot is one
or the other, never both.

**Inswinging share (Panel 4):** denominator is delivered corners only — short
corners (`pass_length < 20`) are excluded from both numerator and denominator.
Label this on the sheet so "inswinging share" doesn't read as a share of all
corners taken.

**Zone grid (Panel 1):** 12 cells per side, mixed resolution, not mirrored. This
replaces an earlier uniform 3x3 version — superseded, not kept alongside this.
Modelled closely on `references/arsenal-corner-locations-1024x819.jpg`: fine
resolution where corner volume actually concentrates (in front of goal), coarse
further out. Rows are NOT equal height — cell height reflects real yards, so the
six-yard-box row is a shallow strip and the edge row is deep, matching the pitch
underneath rather than an abstract grid.

Depth bands (x), each 6 yards except the last — row labels as shown on the
panel:
- Six-yard box: x >= 114
- Penalty spot: 108 <= x < 114 (108 = the penalty spot, a real pitch reference
  point)
- 18-yard box: 102 <= x < 108
- Edge of the area: x < 102 (unbounded in the data; drawn only down to x = 84
  for visual context — the rectangle boundary is a crop choice, not a data
  boundary, so the cell's count/percentage still includes everything below
  x = 84)

Width bands (y), two resolutions:
- Fine (six-yard-box width, split into three): 30–36.67 / 36.67–43.33 / 43.33–50
  — used only for the Six-yard-box and Penalty-spot rows (3 cells each)
- Merged: 30–50 as one cell — used for the 18-yard-box row (matches the
  reference's own un-split "2%" band at that depth; do not split this into
  three, that would contradict the source image this grid is modelled on)
- Flank (2 cells, each spanning the full Six-yard-box + Penalty-spot + 18-yard-box
  depth as ONE tall cell, undivided): 0–30, 50–80. Originally 4 cells
  (0–18/18–30/50–62/62–80, an outer and inner sub-cell each side) — checked
  against all 20 teams, both sides (40 team/side combinations): the outer
  sub-cells were near-empty league-wide (0.9% of delivered corners each, half
  of all team/sides registering zero, three-quarters registering one or fewer)
  against 5.6%/6.7% for the inner sub-cells. Folded into 2 cells, not kept at 4.
- Edge-of-the-area row only, coarse 3-way split: 0–30, 30–50, 50–80

Total: 3 + 3 + 1 (fine/merged central) + 2 (flanks) + 3 (edge row) = 12 cells.

Front post / back post are directional headers spanning roughly half the grid
each (matching the reference's own header treatment), not a per-column label —
the column structure no longer maps 1:1 to three named bands. Labels flip
between the two grids exactly as before (side is not mirrored):

- Left-side grid: front post = near y = 0, back post = near y = 80
- Right-side grid: front post = near y = 80, back post = near y = 0

Row labels (Six-yard box / Penalty spot / 18-yard box / Edge of the area) are
shown once, on the left grid only — the rows are identical on both, so
repeating them wastes width twice over. The two grids are NOT equal width as a
result: the left grid carries the row-label gutter, the right doesn't, and its
column is narrower accordingly. Both still render the pitch itself at the same
px/yard, computed to match rather than assumed, so the grids stay visually
to-scale with each other despite the width difference.

**Counts exception:** percentage only in the 7 fine/merged central cells (as
small as 6.67 x 6 yards — a raw count does not fit legibly at that size).
Percentage AND raw count in the 2 flank cells and the 3 edge-row cells, which are
large enough to have room. This is the same principle as the old back-post rule
(counts exist so small numbers aren't misread as percentages) applied to
whichever cells are actually sparse/small under the new layout, not just one
named column. State the exception on the panel in one line.

**Fine-cell size, achieved not assumed:** rebuilding at the real sheet width
(11.69in, Panel 1 spanning the full top strip) initially gave fine cells only
~38px wide at 5pt font — checked directly, not guessed — well below the flank
cells' size. Fixed by removing the duplicate row-label gutter (see above) and
minimizing panel margins (0.15in each side, 0.25in gap between grids), which
raised px/yard from 5.66 to 8.19 and let fine cells reach 54.6 x 49.2px. That's
enough headroom for 7.2pt — capped at 6.5pt instead, to match the flank cells'
percentage text exactly rather than making the fine cells the most prominent
text on the panel. Panel 1's resulting height at this width: 4.53in.

**Scope: delivered corners only.** Short corners (`pass_length < 20`) are excluded
from the grid entirely — the short count is stated separately on the panel so the
numbers reconcile against the team's total corners. Reason: without this exclusion
the grid partly restates the short-corner metric rather than showing delivery
pattern. Confirmed on Man Utd (highest short rate, 22.8%) vs Crystal Palace
(lowest, 3.7%): including short corners, Man Utd's front-post share (45.3% left,
27.9% right) looked roughly 3-4x Crystal Palace's (11.0%, 6.6%) — but half to
two-thirds of that gap was short corners staying wide near the flag, not delivery
targeting. Delivered-only, the gap narrows (24.7% vs 6.6% left; 12.1% vs 4.5%
right) but survives — a real difference in aim, not an artefact of how often each
team plays it short.

**Caveat — must appear on the sheet itself, not just here:** `pass_end_location`
records where the ball finished, not where it was aimed. A defensive header
clearing an inswinger on the edge of the box looks identical in this data to a
ball that was never going to reach goal. This is most visible in the "front post,
edge" cell, which should not be read as intentional near-post targeting without
that caveat attached.

## Team as a parameter

The subject team must be adjustable by name. Nothing about the sheet should be
hard-coded to one club. I should be able to ask for any of the 20 teams and get the
same sheet back.

## Verification rules

These are not optional. The output goes to coaches.

1. **Print your counts.** Every sheet must show the underlying numbers it was built
   from — corners taken, corners in each category — so I can check them against the
   match record.

2. **Show logic before numbers.** When you define something, explain the rule first,
   then give the result. I need to be able to disagree with the rule.

3. **Separate reading from judging.** "How many corners did X take from the left"
   reads the data and can be checked. "Is X good at set pieces" is a judgement. When
   you are inferring rather than counting, say so explicitly.

4. **State limitations plainly.** If the data cannot answer something, say that
   rather than approximating. No 360 in this dataset means no freeze frames — say so
   rather than substituting something weaker without flagging it.

5. **Never name a player not confirmed in the lineup data.**

## Answering data questions (conversational)

The point of this project isn't only the sheets — I ask questions of the data
directly, in conversation, and expect the same rigor as the sheets get, adapted
for a quick back-and-forth rather than a fixed panel.

1. **State the definition before the number.** Almost every metric here is a
   proxy or a judgement call, not a StatsBomb category — short corner
   (`pass_length < 20`), shots/goals/xG from corners (same possession + 15s
   window), left/right (`y < 40`). Say which definition applies before giving
   the number, so I can disagree with the rule, not just the result.

2. **Always show the count, not just a percentage.** A percentage alone hides
   sample size — see the back-post/Stoke discussions. "16.7%" and "2 of 12"
   read very differently. Give both, every time.

3. **Separate reading from inference, and label inference as inference.**
   "Chelsea play 16.7% of their left corners short" is a reading — countable,
   checkable against the match record. "Because their left-sided taker is
   right-footed" is an inference about *why* — state it as inference
   explicitly, don't fold it into the reading, and check it against the data
   (actual taker identity) rather than assume it.

4. **If the data can't answer it, say so — don't approximate.** No 360 data
   means no freeze frames. No defensive-set-piece definition has been agreed
   at all (only attacking corners are defined). If a question needs something
   this project doesn't have, say that plainly rather than quietly answering
   an easier, adjacent question instead.

5. **Use the agreed definitions, and name which one applies.** 20-yard short
   corner threshold, 15-second shots-from-corners window, `y < 40` = left side
   — these are settled (see Definitions above). Use them by default, and say
   explicitly which is in play when it affects the answer, so a different
   convention from elsewhere doesn't get silently conflated with ours.

## Visual approach

Reference images go in `references/`. Work from those for layout and style rather
than inventing an aesthetic.

Keep all style decisions — colours, fonts, logo path, background — in one place so
they can be changed without touching the analysis code.

Screen document, not a print document. **Two** A4 **landscape** sheets, each
11.69 x 8.27in (~1.414:1 aspect ratio), exported as PNG at 1754 x 1240 px, not
300 dpi PDF. That resolution lives in the style module, not hardcoded into
layout code, so it can be changed without touching anything else. See
`panel_spec.md` for panel layout and the two-sheet split.

## Sheet layout

Two sheets, not four panels on one page — the arithmetic didn't support it.
Panel 1 at full sheet width needs 4.53in of an 8.27in-tall sheet (exact, from
the built file) to hit its fine-cell legibility target. Panel 2's existing
pitch+sidebar design needs 3.02in at half-sheet width just to render
undistorted. Add header, footer, Panel 4, and margins and four panels together
came to ~9.55in against an 8.27in page — over budget before Panel 3 even
existed. Full reasoning and the per-sheet height breakdown are in
`panel_spec.md` ("Two-sheet split").

- **Sheet 1:** header, Panel 1 (zone grid, full width), Panel 4 (rankings
  strip), footer. 6.52in used of 8.27in — 1.75in surplus.
- **Sheet 2:** header, Panel 2 and Panel 3 side by side, footer. Panels 2+3 get
  6.85in of height to work with; Panel 2's current design only uses 3.02in of
  it. **Not resolved** — Panel 2 needs rework and Panel 3 should be designed
  against the real 6.85in budget, not built compact and left surrounded by
  empty page.

Both sheets carry the header and footer, so either works standalone.

## Visual Identity

Light background — the sheet is for screen, not print, and club crests are
designed for light backgrounds.

All tokens below must live in one place in the code (a single style module) so
colours, fonts, and logo path can change without touching analysis logic.
Style and logic stay separate — analysis code should never contain a hex value or
a font name directly.

**Colours**

| Role          | Hex       |
|---------------|-----------|
| Background    | `#f4f2ee` |
| Panel surface | `#ffffff` |
| Border        | `#d8d4cc` |
| Text          | `#1c2330` |
| Muted text    | `#6e7f8f` |
| Accent        | `#f07830` |
| Secondary     | `#60aaee` |

**Fonts**

- Headings: Bebas Neue
- Body: DM Sans
- Numbers: DM Mono

Checked directly against this machine's matplotlib font cache — matplotlib
substitutes a default font silently rather than erroring on a missing one, so
this has to be verified up front rather than assumed:

- **Bebas Neue — available.** Installed system-wide (`/Library/Fonts/BebasNeue-Regular.ttf`
  plus several weights under `~/Library/Fonts/`). matplotlib's font manager already
  lists it (Regular, Bold, Book, Light, Thin). No action needed.
- **DM Sans — available.** Not installed system-wide, so the Regular/Medium/Bold
  weights were copied into `assets/fonts/` (DMSans-Regular.ttf, DMSans-Medium.ttf,
  DMSans-Bold.ttf) so this project doesn't depend on another project's folder
  still existing. Registered with matplotlib via `fm.fontManager.addfont()` — the
  style module must call this at import time, before any figure is created, or
  matplotlib falls back to its default sans silently. Weight metadata (400/500/700)
  reads correctly off the files, so `family="DM Sans", weight="bold"` resolves to
  the right file.
- **DM Mono — available.** Same treatment: Regular/Medium copied into
  `assets/fonts/` (DMMono-Regular.ttf, DMMono-Medium.ttf), registered the same way.

All three families confirmed resolving to real font files (not a silent fallback)
via `fm.findfont(..., fallback_to_default=False)` after registration.

## Branding assets are optional

`assets/` may not contain a personal logo, and `assets/badges/` may not contain
every club crest. The build must not fail when they are missing.

- **Missing club badge:** render the team name alone in the header. Do not
  substitute another image or leave a blank box.
- **Missing personal logo:** render the footer without it. StatsBomb attribution
  and the generated date still appear.
- **StatsBomb attribution is not optional.** If the logo file is absent, use text
  attribution instead. It must appear on every output.

Anyone following this build will supply their own branding, or none. The sheets
must work either way.

## Project structure

```
one-person-data-department/
├── CLAUDE.md          ← this file
├── references/        ← visual examples to work from
├── data/              ← StatsBomb data
├── outputs/           ← generated sheets
├── src/               ← code
└── venv/              ← Python environment
```

Python 3.14, statsbombpy 1.22.0, pandas 3.0.5, matplotlib 3.11.1, mplsoccer 1.8.0,
pyarrow 25.0.1 (Parquet read/write), cairosvg 2.9.0 (SVG badge conversion).

**cairo is a system dependency, not a venv package.** Installed via Homebrew
(`brew install cairo`) — it lives outside the venv entirely and won't show up in
a `pip freeze`/requirements file. cairosvg needs the native cairo library to
rasterize SVG; pip alone can't provide it. A fresh machine needs
`brew install cairo` run separately before `pip install cairosvg` will import.

## Working style

Don't write files unless I ask. When I'm exploring, I want answers, not artefacts.

If I ask for something that seems wrong or that the data can't properly support,
tell me before doing it.

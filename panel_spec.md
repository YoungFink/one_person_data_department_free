# Set-Piece Sheet — Panel Specification

Paste this into Claude Code. It defines what goes on the sheet before any code is
written.

---

## Sheet format

**Two A4 landscape sheets, not one.** The height arithmetic doesn't support four
panels at the quality each needs on a single page — see "Two-sheet split" below
for the numbers that forced this. Each sheet: 11.69 x 8.27in, PNG at 1754 x 1240
px. Screen document. Resolution set in the style module, not hardcoded.

Both sheets carry the header (crest, team name, subtitle) and footer (OTF logo,
StatsBomb attribution, date), so either one works standalone — a coach with just
Sheet 2 still knows whose data it is.

- **Sheet 1:** header, Panel 1 (zone grid, full width), Panel 4 (rankings
  strip), footer.
- **Sheet 2:** header, Panel 2 and Panel 3 side by side, footer.

Light palette as defined in CLAUDE.md. Restraint over decoration — white space,
one idea per panel, accent colour used sparingly.

## Header

- Club crest, top left, from `assets/badges/{team}.png`, scaled into a fixed box so
  the header doesn't shift between teams
- Team name as the sheet title
- Subtitle: "Corners | Premier League 2015/16"
- If a badge file is missing, render the team name only. The sheet must not break.
- Same header on both sheets.

## Footer

- OTF logo from `assets/OTF Logo Colour.png`, bottom right
- StatsBomb attribution, as required by their terms
- Generated date
- Same footer on both sheets.

## Two-sheet split — the arithmetic behind it

Panel 1 at full sheet width needs **4.53in** of an 8.27in-tall sheet (exact,
from the built file) to hit its fine-cell legibility target — see CLAUDE.md.
That alone is 55% of the page. Panel 2's existing pitch+sidebar design needs
**3.02in** at half-sheet width just to render undistorted (derived from its
actual gridspec/pitch-aspect code, not guessed). Header, footer, Panel 4, and
margins add roughly another 2in on top. Four panels together came to ~9.55in
against an 8.27in page — over budget before Panel 3 even existed. Splitting
into two sheets removes the competition for height between Panel 1 and the
Panel 2/3 row entirely; each sheet now has slack instead of a deficit (see the
per-sheet breakdowns below).

**Sheet 1 breakdown** (estimates for header/footer/Panel 4 — not yet built;
Panel 1 exact):

| Section | Height |
|---|---|
| Header | 0.70in (estimate) |
| Panel 1 | **4.53in (exact)** |
| Panel 4 | 0.50in (estimate) |
| Footer | 0.40in (estimate) |
| Margins/gaps (3 internal + 2 outer) | 0.39in |
| **Total** | **6.52in of 8.27in — 1.75in surplus** |

**Sheet 2 breakdown:**

| Section | Height |
|---|---|
| Header | 0.70in (estimate) |
| Footer | 0.40in (estimate) |
| Margins/gaps (2 internal + 2 outer) | 0.32in |
| **Reserved (non-panel)** | **1.42in** |
| **Panels 2+3 row gets** | **6.85in** |

Panel 2's current design only uses 3.02in of that 6.85in — a **3.83in surplus**
if Panel 2 and Panel 3 keep their current compact proportions. This is the same
"grids don't fill the available space" problem already fixed twice for Panel 1
(once on width, once on height), now showing up on Sheet 2. Not resolved yet —
Panel 2 will need rework and Panel 3 should be designed against the real 6.85in
budget from the start, not a compact default that leaves the page half empty.

---

## Panel 1 — Zone grid, by side

Two grids side by side within one panel. Left-side corners on the left, right-side
corners on the right. NOT mirrored — the side asymmetry is the point.

**[Addition] Draw the pitch.** Each grid must be rendered over a real pitch
outline: goal, six-yard box, penalty area, penalty spot, penalty arc. Use
`mplsoccer`'s `VerticalPitch` cropped to the depth range, not an abstract grid.

The zone shading must align exactly with the drawn pitch lines. The
six-yard-box row boundary must sit on the real six-yard line; the
penalty-spot row boundary must sit on the penalty spot.

**Why:** without the pitch, the panel reads as a table pinned over nothing. A
coach cannot tell where they are looking. This was built without a pitch once
and rejected.

**Delivered corners only.** Short corners (`pass_length < 20`) are excluded from
the grid — including them partly restates the short-corner metric rather than
showing delivery pattern (confirmed on Man Utd vs Crystal Palace: excluding short
corners roughly halved the apparent front-post gap between them, from an artefact
of short-corner rate down to a real difference in delivery targeting). State the
short count on the panel so it reconciles against the team's total corners.

- Percentage of that side's *delivered* corners ending in each zone. Each grid
  sums to 100% of its own side's delivered corners, not its total corners.
- Zone boundaries — **12 cells per side, mixed resolution, modelled closely on**
  `references/arsenal-corner-locations-1024x819.jpg`, not a uniform 3x3. This
  replaces the earlier 3x3 version entirely (see CLAUDE.md for the full
  reasoning and the exact boundaries) — fine cells where volume concentrates
  (in front of goal), large undivided cells further out, sized to real yards
  rather than equal rows:
  - Depth (row labels as shown on the panel): six-yard box (6yd) / penalty spot
    (6yd) / 18-yard box (6yd) / edge of the area (drawn to x=84, unbounded in
    the underlying data).
  - Width: fine 3-way split of the six-yard-box width for the six-yard-box and
    penalty-spot rows only; the 18-yard-box row's central band is one merged
    cell (matching the reference's own un-split "2%" band — do not split it);
    2 flank cells either side (0–30, 50–80), each spanning the full box depth
    undivided — originally 4, folded after checking all 20 teams showed the
    outer sub-cells (0–18, 62–80) near-empty league-wide; the edge-of-the-area
    row uses a coarse 3-way split.
  - Front post / back post are directional headers over each half (matching the
    reference), not a per-column label. Flip by side, not mirrored: left grid
    has front post near `y=0`; right grid has front post near `y=80`.
  - Row labels shown once, on the left grid only (rows are identical on both).
    The two grids are therefore NOT equal width — the right grid has no
    label-gutter and is narrower — but both render the pitch at the same
    px/yard, computed to match, so they stay visually to-scale with each other.
- **[Addition] Row heights follow real yards.** The six-yard-box row is a
  shallow strip; the edge row is deep. Do not force equal-height rows — that
  breaks alignment with the pitch underneath.
- Shading intensity by percentage, single-hue ramp from the accent colour.
- **Counts exception:** percentage only in the 7 fine/merged central cells —
  too small (down to 6.67 x 6 yards) to legibly hold a raw count too.
  Percentage AND raw count in the 2 flank cells and 3 edge-row cells, which have
  room. State this exception on the panel in one line.
- Label each grid with the side, the delivered corner count, and the short count
  for that side (so total = delivered + short is visible and checkable).
- **On-panel caveat, required:** `pass_end_location` is where the ball finished,
  not where it was aimed — a defensive clearance on the edge of the box looks
  identical here to a ball that was never going to reach goal. State this
  directly on the panel, near the front-post edge cell in particular, so it is
  not read as intentional near-post targeting.

Uses `pass_end_location` and `pass_length` from `data/pl_2015_16_corners.parquet`.

## Panel 2 — Delivery trajectories

**Straight line** from corner location to end location for every corner — not an
arc. StatsBomb records only the two points, no flight path; a curved line would
imply a ball trajectory (and a curve direction, which would visually contradict
the colour coding — inswingers and outswingers would bow identically) that isn't
in the data. Built and corrected once already: the first version used a
plotting-code-generated curve, which was misleading for exactly this reason.

**[Addition] Lines are straight.** Never draw curved arcs. StatsBomb records
start and end location only, with no flight path, so any curvature is
generated by the plotting code and applied uniformly — which makes
inswingers and outswingers bow identically and contradicts the colour coding.

- Colour by `pass_technique`: four buckets — inswinging, outswinging, straight,
  and **untagged** (no technique value) as its own category, not folded into
  straight. See Definitions in CLAUDE.md.
- **[Addition] Colour mapping — specify it, don't infer it.** The palette
  defines two categorical colours, but Panel 2 needs four technique
  categories. The mapping is:

  | Category | Token |
  |---|---|
  | Inswinging | Accent `#f07830` |
  | Outswinging | Secondary `#60aaee` |
  | Straight | Text `#1c2330` |
  | Untagged | Muted text `#6e7f8f` |

  Short corners are not drawn, so they need no colour.
- **Short corners (`pass_length < 20`) drawn in a visually distinct muted grey at
  reduced opacity** — a different grey from the "untagged" bucket, since they are
  different things (a deliberate short routine vs. a delivered corner StatsBomb
  didn't tag a technique for). So the delivery pattern reads first but the short
  routines are visibly present and the arc count reconciles with the corner total.
- **[Addition — supersedes the bullet above] Short corners are NOT drawn on the
  pitch.** They appear as a count in the stats block only.

  **Why:** drawn on the pitch, short corners read as failed deliveries fanning
  towards the corner flag. They are successful routines. This was tried both
  ways; drawing them misleads more than the reconciliation gains.
- End points marked.
- **[Addition] Lines are a faint background wash, not the main element.** Draw
  the connecting lines at low opacity and thin weight. The end points are the
  prominent element — larger, full opacity, coloured by technique.

  **Why:** 176 lines converging on two points is mostly ink. All the
  information is in where the ball finished, and prominent lines bury it.
  Match the weighting in
  `references/arsenal-corner-inswing-v-outswing-1024x717.jpg`.
- **[Addition] No legend on the pitch.** Technique counts live in the stats
  block below, with colour swatches. The pitch area carries data only.
- **[Addition] Fixed crop across all teams.** Crop to x >= 70. Do not tighten
  the crop per team. Some teams will show more empty grass; that is the cost
  of keeping panels comparable between opponents. Panel 2 and Panel 3 must use
  the same crop so that, side by side on Sheet 2, the same pitch renders at
  the same scale.
- **On-panel caveat, required:** state directly on the panel that lines show start
  and end location only, not ball flight, and that colour encodes technique, not
  curve.

Stats sidebar, which must reconcile:
- Total corners
- Of which short
- Of which delivered
- Inswinging / outswinging / other counts

## Panel 3 — Shots following corners

Shot locations for shots originating from corners.

**Definition, agreed:** a shot counts if it is in the same `possession` as the corner
AND occurs within **15 seconds** of the corner event. The time cap prevents a
clearance to halfway followed by a spell of build-up being credited to the corner.

Route: join `data/pl_2015_16_events.parquet` on `match_id` + `possession`, filter to
`play_pattern == "From Corner"`, apply the 15-second window.

- Marker size by xG, following the Opta reference.
- Goals highlighted in the accent colour, other shots muted.
- **[Addition] Fixed crop across all teams.** Crop to x >= 70, matching Panel
  2's crop exactly. Do not tighten the crop per team — some teams will show
  more empty grass; that is the cost of keeping panels comparable between
  opponents. Panel 2 and Panel 3 must use the same crop so that, side by side
  on Sheet 2, the same pitch renders at the same scale.
- Sidebar: goals, total shots, xG, xG per shot, and **the direct vs second-phase
  split** — a coach reading "79 shots" needs to know how many were first contact.

## Panel 4 — Rankings strip

Slim horizontal strip. Text only, no chart. Six lines, each showing the team's value
and its rank out of 20:

1. Corners taken
2. Short corner rate
3. Inswinging share
4. Shots from corners
5. Goals from corners
6. xG from corners

Format: value large in DM Mono, rank and label small in DM Sans.

**No generated prose summary.** Rankings are countable and checkable; a written
judgement is not, and it would sound equally confident either way. Any interpretive
comment is written by the analyst, not the tool.

---

## Verification requirements

1. Every panel prints the counts it was built from.
2. Panel 2's short + delivered must equal the total corners shown.
3. Panel 3 must show the direct vs second-phase split, not just a total.
4. Corner count must be re-verified after every join or filter.
5. Never name a player not confirmed in the lineup data.

## Team as parameter

Every element above must resolve from a single team name. No hardcoding. Changing
the team name regenerates the entire sheet.

## Known limitations to state on the sheet or in the log

- Short corner is a proxy (`pass_length < 20`), not a StatsBomb category.
- The 15-second window is a judgement call, not a data-derived boundary.
- No 360 data in this competition, so first contact cannot be derived from freeze
  frames — only from event locations.
- External check against Premier League official and FBref: Liverpool +1,
  Chelsea -1, Manchester United exact. Providers differ slightly at the margins.

---

## Build order

Do not build all four at once.

1. Panel 2 first (trajectories) — it exercises the corners file, the palette, the
   fonts and the badge lookup without needing the events join.
2. Get it correct, then get it looking right.
3. Then Panel 1, then Panel 3, then Panel 4.
4. Assemble last.

---

## [Addition] What this spec cannot give you

Everything above was learned by building something, looking at it, and deciding it
was wrong. The numbers were correct in every one of those rejected versions.

Expect to iterate on any panel you add. Budget three or four rounds per panel for
the visual work, even when the data is right first time. If a panel renders
correctly on the first attempt, look harder.

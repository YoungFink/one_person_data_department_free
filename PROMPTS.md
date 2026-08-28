# The prompt sequence

Thirteen prompts, paste them into Claude Code in order, in an empty folder. Each
one produces the same underlying numbers as this repo, because the definitions
are pinned down in `CLAUDE.md` and `panel_spec.md`, not left to whatever Claude
decides on the day.

**This route does not produce identical output.** The counts will match —
380 matches, 4,107 corners, a given team's short rate, all of it — because those
come from the data and the definitions, not from layout choices. But margins,
gaps, exact font sizes and the like will vary between runs, because those are
judgement calls made fresh each time. If you want the exact PNGs this repo
ships, run the code instead (see the main README).

Run the check after each prompt before moving to the next one. If a check
fails, fix it there — don't carry a wrong number forward into the next step.

---

## 1. Scaffold the project

**Prompt:**
> Set up a new project called The One-Person Data Department. Create this structure:
> `data/`, `outputs/`, `src/`, `assets/`, `assets/fonts/`, `assets/badges/`,
> `references/`. Don't add any code yet — just the folders, empty.

**Check:** `ls` the project root and confirm all six directories exist.

---

## 2. Add CLAUDE.md

**Prompt:**
> I'm going to paste a file called CLAUDE.md into this project. It defines the
> data, the metric definitions, the verification rules and the visual identity
> for everything we build. Save it at the project root and treat it as binding
> — don't change any definition in it without asking me first.
>
> [paste the full contents of this repo's `CLAUDE.md`]

**Check:** Ask Claude to summarise the corner definition, the short-corner
threshold, and the left/right side rule back to you in its own words. If any
of the three is wrong, the file didn't save correctly — check before going on.

---

## 3. Add panel_spec.md

**Prompt:**
> Here's panel_spec.md — the panel-by-panel specification for the sheet,
> including the two-sheet split and the build order. Save it at the project
> root. Don't build anything yet.
>
> [paste the full contents of this repo's `panel_spec.md`]

**Check:** Ask what order the four panels get built in. The answer should be
Panel 2, then Panel 1, then Panel 3, then Panel 4, assembled last — that's
stated explicitly in the spec, and if it comes back different, the file wasn't
read properly.

---

## 4. Environment and data pull

**Prompt:**
> Step 1: environment and data pull. Set up the Python environment with
> statsbombpy, pandas, matplotlib, mplsoccer and pyarrow. Then pull Premier
> League 2015/16 via statsbombpy into `data/`: a matches CSV, a full events
> Parquet, and a filtered corners-only Parquet using `type == "Pass"` and
> `pass_type == "Corner"` — explicitly not `play_pattern == "From Corner"`.
> When it's done, tell me the match count, the total corner count, and
> confirm corners taken equals corners faced.

**Check:** 380 matches, 4,107 corners, 0 mismatches between corners taken and
corners faced. This pull takes several minutes — StatsBomb's API is fetched
one match at a time, so slowness here is normal, not a hang.

---

## 5. Verify the short-corner threshold

**Prompt:**
> Step 2 is a verification pass, since CLAUDE.md is already in place.
> Re-derive the short corner threshold from the freshly pulled data rather
> than taking it from the spec. Show me the pass length distribution, confirm
> it's bimodal, and confirm the trough sits where the spec says it does. Then
> check the 15 to 20 yard band: how many corners fall in it league-wide, how
> many are ground passes, how many complete to a named recipient, and how
> many end in the central goal-mouth channel.

**Check:** 97 corners in the band, 94 of them ground passes, 93 completed to
a named recipient (96%), 0 ending in the central channel. If your numbers
differ, don't proceed — something upstream in the pull is off.

---

## 6. Prepare assets

**Prompt:**
> Step 3: prepare assets. Convert any club crest files that aren't already
> PNG, and register the DM Sans, DM Mono and Bebas Neue fonts with
> matplotlib. Copy every font file — Bebas Neue included — into
> `assets/fonts/` so the project doesn't depend on any font being
> pre-installed on this machine. If a font file is genuinely missing at
> render time, fall back to a system sans font rather than failing, and print
> a warning naming the missing font and what it fell back to. Note that
> `assets/` has no personal logo — that's intentional, and the build should
> handle it.
>
> Check before moving on: all 20 team names resolve to a badge file, and
> `fm.findfont(..., fallback_to_default=False)` succeeds for all three
> families using only the project's own copies — not a font already
> installed on this machine.

**Check:** 20/20 badges resolve. All three font families resolve from
`assets/fonts/` — test this by checking they'd still resolve on a machine
that has none of them pre-installed, not just on your own machine, since a
font already installed system-wide can mask a project that isn't actually
self-contained.

---

## 7. Describe Panel 1's geometry before building it

**Prompt:**
> Step 4 is a verification step, not a build step. Read panel_spec.md, then
> describe back the Panel 1 zone cell layout you'd build — the depth bands
> and width bands in pitch coordinates, and how many cells per side. Check it
> against `references/arsenal-corner-locations-1024x819.jpg`. Don't build
> anything yet. I want to confirm the geometry in words before any code
> exists.

**Check:** 12 cells per side, mixed resolution — a fine 3-way split in front
of goal, one merged cell for the 18-yard-box row, 2 flank cells, and a coarse
3-way split for the edge of the area. If the description doesn't name all
four depth bands (six-yard box, penalty spot, 18-yard box, edge of the area)
and both width resolutions, don't move on.

---

## 8. Build Panel 2 — delivery trajectories

**Prompt:**
> Build Panel 2 (delivery trajectories) at its real target size for the
> two-sheet layout: half-sheet width, pitch on top and stats below. Use
> `mplsoccer`'s `VerticalPitch`, cropped to x >= 70 — this crop must stay
> fixed across every team, not tightened per team, because Panel 2 and
> Panel 3 need to render at the same scale side by side.
>
> Colour mapping: Inswinging → Accent, Outswinging → Secondary,
> Straight → Text, Untagged → Muted text. Short corners are **not** drawn on
> the pitch at all — they read as failed deliveries fanning to the flag when
> drawn, but they're successful routines. Count them in the stats block only.
> Lines are a faint background wash (low opacity, thin); end points are the
> prominent element, full opacity, sized normally, coloured by technique. No
> legend on the pitch — technique counts with colour swatches go in the
> stats block instead.
>
> Print the counts: total, short, delivered, and all four technique buckets.

**Check:** the four technique buckets plus short sum to the team's total
corners. Untagged is its own bucket, never folded into Straight.

---

## 9. Build Panel 1 — zone grid

**Prompt:**
> Now build Panel 1 (zone grid) at full sheet width. Draw a real pitch under
> the shading — goal, six-yard box, penalty area, penalty spot, penalty arc
> — using `mplsoccer`, cropped to the depth range, not an abstract grid.
>
> The flank cells' width boundary is the six-yard-box width (y=30 and y=50),
> not the penalty-area width (y=18 and y=62). Anchoring to the wider
> penalty-area figure looks more "correct" against the pitch, but it drags
> the fine cells' width out with it and can put over 40% of deliveries in a
> single cell, destroying the resolution in front of goal — which is the
> whole point of this panel. The real penalty-area sideline will pass through
> the interior of the flank cells as a result; that's fine, because those
> cells carry under 1% of deliveries each. Use one consistent shading opacity
> across all 12 cells — don't vary opacity per cell to paper over an alignment
> mismatch; if a line looks wrong, fix the boundary, not the opacity.
>
> Print the delivered/short/total count for each side, and tell me the
> measured fine-cell font size at native resolution — actually measure the
> rendered pixel size, don't assume it from the point size.

**Check:** the 12 cells on each side sum to 100% of that side's own delivered
corners. Zoom into a flank cell in the rendered PNG — there should be no
visible extra division inside it. Zoom into the six-yard-box row — the fine
cells there should be genuinely fine (single-digit yards wide), not diluted.

---

## 10. Build Panel 3 — shots following corners

**Prompt:**
> Build Panel 3 (shots following corners) at half-sheet width, stacked
> layout, same crop as Panel 2 (x >= 70). A shot counts if it's in the same
> `possession` as a corner and within 15 seconds of the corner event — join
> `data/pl_2015_16_events.parquet` on `match_id` and `possession`. Marker
> size by xG. Goals in the accent colour, other shots muted. The direct
> versus second-phase split is the headline of the stats block, not just one
> line among others — direct means the shot's event id is referenced by
> `pass_assisted_shot_id` on the corner event itself.
>
> Print corners taken, total shots, direct, second-phase, goals, xG and xG
> per shot.

**Check:** direct plus second-phase equals the total shot count. Direct
should also equal (or very closely match) the number of that team's corners
with a non-null `pass_assisted_shot_id` — if it doesn't, the time window or
the join has a bug.

---

## 11. Build Panel 4 — rankings strip

**Prompt:**
> Build Panel 4 (rankings strip): a slim horizontal strip, text only, no
> chart. Six lines — corners taken, short corner rate, inswinging share,
> shots from corners, goals from corners, xG from corners — each showing the
> team's value and its rank out of 20. This needs the same shot-window logic
> as Panel 3, computed across all 20 teams, not just the one team on the
> sheet. Print the full 20-team table for all six metrics so I can check any
> rank by hand.

**Check:** spot-check two or three teams' ranks against the printed table by
hand. Confirm short corner rate and inswinging share use the denominators
CLAUDE.md specifies (total corners for short rate; delivered corners only,
excluding short, for inswinging share) — these are easy to compute with the
wrong denominator and get a plausible-looking wrong number.

---

## 12. Assemble both sheets

**Prompt:**
> Assemble both sheets for [team name]. Sheet 1 is header, Panel 1, Panel 4,
> footer. Sheet 2 is header, Panels 2 and 3 side by side, footer. Both
> 1754 x 1240px. The header needs the club crest, team name and subtitle; the
> footer needs the StatsBomb logo (or text attribution if it's missing), the
> generated date, and a personal logo slot that degrades gracefully when
> empty. Print the counts at each stage.

**Check:** open both PNGs at full size and look at the edges, not just the
centre. A panel built at "full sheet width" already has its own margins
baked in — pasting it with an *additional* offset pushes content off the
right edge silently, and it's easy to miss at thumbnail size. Confirm both
files are exactly 1754 x 1240px.

---

## 13. Regenerate for a second team

**Prompt:**
> Regenerate both sheets for a different team — pick one with a very
> different short corner rate or side split from the last one, so a
> hardcoded value would actually show up as wrong rather than accidentally
> looking right. Confirm nothing in the header, the panels or the footer is
> still referencing the first team.

**Check:** the new team's name, crest, and every number on the sheet changed;
nothing from the first team is left over anywhere. If you picked Stoke City,
their short corner rate is genuinely sensitive to the exact threshold used —
CLAUDE.md documents 8 of their 15 short corners sitting right at the edge of
the 15–20 yard band, moving their league rank from 9th to 16th depending on
the cut. That's a real property of their data, not a bug in your build.

---

## When the output looks wrong

If a rendered sheet looks off — spacing, alignment, a line that shouldn't be
there — don't ask Claude to "fix the spacing." Ask for a measurement instead.

"Fix the spacing" gets you a report that it's fixed. Whether that report is
true is a separate question, and often it isn't — the model is reporting its
intent, not a checked fact. "Tell me the pixel gap between each line,
measured on the rendered PNG" gets you an actual number, forces a real check
against the file that was actually produced, and either confirms the fix or
shows you it didn't work.

This applies to anything visual: a cell that looks divided when it shouldn't
be, text that looks too faint, a badge that looks the wrong size. Ask for the
pixel dimensions, the crop, the measured font size — not the description. It
was the single most useful technique in building this project.

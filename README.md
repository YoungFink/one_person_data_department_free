# The Person Data Department — Set-Piece Sheets

Opposition corner analysis, built from StatsBomb open data.

Two A4 landscape sheets for any team in the Premier League 2015/16 season.
Change the team name, get a new set of sheets. No paid data licence required.

Part of [Outside the Fink](https://www.youtube.com/@outsidethefink5063).

---

## What this produces

**Sheet 1** — where their corners land

- A zone grid split by side (left corners and right corners shown separately,
  not mirrored)
- Percentage and count of delivered corners in each zone
- A rankings strip: corners taken, short corner rate, inswinging share, shots,
  goals and xG from corners, each with the team's rank out of 20

**Sheet 2** — how the ball gets there and what happens next

- Delivery trajectories, coloured by technique, with the technique breakdown
- Shot locations following corners, sized by xG
- The direct versus second-phase split, which tells a coach whether the threat
  is the first contact or the second ball

---

## Three ways to use this

Pick whichever suits you. They're not sequential.

**1. Take the code and run it.**
You want working sheets today. Follow the setup below, run the script, done.
This produces exactly what you see in the videos.

**2. Follow the prompt sequence.**
You want to build it yourself and understand how. `PROMPTS.md` has thirteen
prompts that take you from an empty folder to finished sheets, with a check to
run after each one.

Be aware: **prompts do not produce identical output.** The numbers will be the
same every time, because the definitions are pinned down in the spec files. The
layout will vary — margins, gaps, exact font sizes. That's normal and it isn't a
mistake on your part. If you want pixel-identical output, use route 1.

**3. Read the spec files.**
`CLAUDE.md` and `panel_spec.md` are where the actual thinking lives. Every
definition, every visual decision, and the reasoning behind each one. If you only
read one thing in this repo, read those.

---

## Setup

You need Python 3 and, for routes 1 and 2, Claude Code.

### 1. Get the files

Download this repository (green **Code** button, then **Download ZIP**) and
unzip it somewhere sensible, like your Documents folder.

### 2. Create a Python environment

Open Terminal, navigate to the folder, and run:

```bash
python3 -m venv venv
source venv/bin/activate
pip install statsbombpy pandas matplotlib mplsoccer pyarrow
```

On Windows the activate line is `venv\Scripts\activate` instead.

You'll see a notice at the end about a newer version of pip being available.
**That is not an error.** Ignore it.

### 3. Pull the data

The data isn't in this repository — it's several hundred megabytes and StatsBomb
publish it themselves. Pull it with:

```bash
python src/pull_data.py
```

This takes around ten minutes. It fetches 380 matches one at a time and there's
very little visible progress while it runs. **It has not frozen.** Let it finish.

When it's done you should see 380 matches and 4,107 corners. If you get different
numbers, stop and check before going further.

### 4. Generate the sheets

```bash
python src/assemble.py "Manchester United"
```

Any of the twenty teams works. Use the exact StatsBomb spelling — `AFC
Bournemouth`, not `Bournemouth`. If you don't name a team it defaults to
Manchester United.

Two files land in `outputs/`: `sheet1.png` and `sheet2.png`.

---

## Club badges

Club crests are **not** included here. They're registered trademarks owned by the
clubs and redistributing them isn't something I can do.

The sheets work without them — a missing badge renders the team name alone. This
is handled in the code and tested.

If you want crests, source them yourself and put PNGs with transparent
backgrounds into `assets/badges/`. Filenames must match the StatsBomb team names
exactly:

```
assets/badges/Manchester United.png
assets/badges/Crystal Palace.png
assets/badges/AFC Bournemouth.png
```

Take the exact names from the data rather than guessing — the `team` column in
`data/pl_2015_16_matches.csv` is the authority.

Matplotlib can't read SVG or WebP, so convert to PNG first. Converting SVG needs
cairo, which on macOS is `brew install cairo`. It's a system library, not a
Python package, so `pip install` won't fix it if it's missing.

---

## Fonts

DM Sans and DM Mono are included (Open Font Licence). Bebas Neue is used for
headings — if it isn't installed on your machine, the code falls back to DM Sans
and prints a warning saying so.

Change any of this in `src/style.py`. Every colour, font and size lives in that
one file, deliberately, so you can rebrand the sheets without touching any
analysis code.

---

## The definitions, and why they matter

These are judgement calls, not facts. You may disagree with them, and if you do,
change them — but change them knowingly.

**A corner** is a pass event with `pass_type == "Corner"`. Not
`play_pattern == "From Corner"`, which tags every event in the possession
afterwards and massively overcounts.

**A short corner** is a pass under 20 yards. StatsBomb has no short-corner tag,
so this is a proxy. The 20-yard figure sits in the trough of a genuinely bimodal
distribution. All 97 corners in the 15–20 yard band end in the wide corridor,
none in the central goal-mouth channel, so the band captures the same routine
taken a bit further from the flag — not compressed near-post deliveries.

**A shot from a corner** is any shot in the same possession, within 15 seconds.
The time cap stops a clearance to halfway followed by a fresh attack being
credited to the corner. Fifteen seconds is a football judgement, not a standard
definition. Other sources will give you different numbers.

**The zone grid uses delivered corners only.** Including short corners made
teams that play short look like they target the near post, when they were
actually working the ball near the flag. Excluding them roughly halved the
apparent difference between Manchester United and Crystal Palace.

**`pass_end_location` is where the ball finished, not where it was aimed.** A
well-struck inswinger headed clear at the edge of the box looks identical in the
data to a poor delivery that was never going to reach anyone. There's no way to
separate those without 360 data, which this competition doesn't have. Don't read
the edge cells as intentional targeting.

Full reasoning for all of these is in `CLAUDE.md`.

---

## Checking the output

The sheets print their own counts. Check them.

Corners taken should equal corners faced across the season. Short plus delivered
should equal the total. The technique buckets should sum to delivered. Direct
plus second-phase should equal total shots.

Corner counts here differ from other providers by roughly one to two percent.
Checked against the Premier League site and FBref: Liverpool +1, Chelsea −1,
Manchester United exact. That's normal — providers tag marginal events
differently and there's no single correct number.

What matters is consistency within one provider. If your work runs on StatsBomb,
every internal comparison is valid regardless of what Opta says. Check outside
once so you know the size of the gap and can explain it if someone asks.

Be aware that a one-count difference can flip a ranked order. It did here:
Bertrand and Ward-Prowse swap second and third on Southampton's corner takers.

---

## What isn't here

**360 data.** Premier League 2015/16 doesn't have it, so first contact comes from
event locations rather than freeze frames. Everything in the open data with 360
is either a tournament, where a team plays three to seven games, or a single
team's season. Nothing gives you both 360 and a real per-team sample.

**Free kicks and throw-ins.** Corners only.

**Defensive set-piece analysis.** The mirror of this — what a team concedes from
corners — is buildable from the same data but isn't in these sheets.

---

## Attribution

Data provided by [StatsBomb](https://statsbomb.com). Free open data, used with
attribution as their terms require. If you build on this, keep the attribution.

Register at StatsBomb's resource centre and read the user agreement before using
the open data yourself.

---

## Licence

Code is MIT — do what you like with it.

Fonts are under the Open Font Licence. The StatsBomb logo belongs to StatsBomb.
Reference images in `references/` belong to their respective owners and are
included for illustration.

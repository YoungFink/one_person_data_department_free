"""
Single home for style decisions: colours, fonts, logo/badge paths, output
resolution. Analysis code must never contain a hex value or font name
directly — import from here instead.

Font registration happens at import time, before any figure is created.
matplotlib substitutes a default font silently on a missing family rather
than erroring, so every family is verified to resolve to a real file
(fallback_to_default=False) rather than assumed to be present.
"""

from pathlib import Path

import matplotlib.font_manager as fm

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
BADGES_DIR = ASSETS_DIR / "badges"

# --- Colours -----------------------------------------------------------

COLOR_BACKGROUND = "#f4f2ee"
COLOR_PANEL_SURFACE = "#ffffff"
COLOR_BORDER = "#d8d4cc"
COLOR_TEXT = "#1c2330"
COLOR_TEXT_MUTED = "#6e7f8f"
COLOR_ACCENT = "#f07830"
COLOR_SECONDARY = "#60aaee"

# --- Fonts ---------------------------------------------------------------

FONT_HEADING = "Bebas Neue"
FONT_BODY = "DM Sans"
FONT_MONO = "DM Mono"

# All font files ship inside the project (assets/fonts/) so a fresh checkout
# doesn't depend on any font being pre-installed on the machine running it.
# Keyed by weight so rendering code can ask for an exact file.
_FONT_FILES = {
    FONT_HEADING: {
        "regular": FONTS_DIR / "BebasNeue-Regular.ttf",
    },
    FONT_BODY: {
        "regular": FONTS_DIR / "DMSans-Regular.ttf",
        "medium": FONTS_DIR / "DMSans-Medium.ttf",
        "bold": FONTS_DIR / "DMSans-Bold.ttf",
    },
    FONT_MONO: {
        "regular": FONTS_DIR / "DMMono-Regular.ttf",
        "medium": FONTS_DIR / "DMMono-Medium.ttf",
    },
}

# Bundled with matplotlib itself, so this always resolves regardless of what
# is or isn't installed on the machine — the safety net under the safety net.
# Passed as a single-item list, not a bare string: matplotlib's FontProperties
# parses a plain string containing "-" as an old fontconfig pattern (breaks
# on "sans-serif" itself), so the list form is required to avoid that.
_SYSTEM_FALLBACK_FAMILY = "DejaVu Sans"


def _register_project_fonts() -> None:
    """Register each project font file with matplotlib. A missing file is
    not fatal here — it's a warning now, and verify_fonts() below falls
    back to a system font for that family at resolve time."""
    for family, weights in _FONT_FILES.items():
        for weight, font_path in weights.items():
            if font_path.exists():
                fm.fontManager.addfont(str(font_path))
            else:
                print(
                    f"[style] Warning: font file missing: {font_path} "
                    f"(needed for '{family}' {weight})"
                )


_register_project_fonts()


def get_font_properties(family: str, weight: str = "regular") -> "fm.FontProperties":
    """Return a FontProperties pointing at the project's own font file by
    exact path (fname=), not by family-name search.

    Family-name lookup (fm.findfont('Bebas Neue')) is ambiguous whenever a
    same-named font is also installed system-wide: matplotlib scores
    identically-weighted duplicates as ties and can return the system copy
    even after the project's own file is registered — confirmed on this
    machine, which already has five other "Bebas Neue" files under
    ~/Library/Fonts and /Library/Fonts. Rendering code should call this
    function rather than pass a bare family string, so the font actually
    used is always the project's own file regardless of what else is
    installed on the host.

    Falls back to a system sans font (with a warning) if the requested
    file is missing.
    """
    font_path = _FONT_FILES.get(family, {}).get(weight)
    if font_path is not None and font_path.exists():
        return fm.FontProperties(fname=str(font_path))

    fallback = fm.FontProperties(family=[_SYSTEM_FALLBACK_FAMILY])
    print(
        f"[style] Warning: '{family}' ({weight}) font file not found — "
        f"falling back to '{_SYSTEM_FALLBACK_FAMILY}'"
    )
    return fallback


def verify_fonts() -> dict[str, dict]:
    """Verify each required family two ways:

    1. registered: the project's own font FILE was successfully added to
       matplotlib's font manager (fname match in ttflist) — this is the
       reliable, unambiguous check that the project is self-contained.
    2. name_lookup_path: what fm.findfont(family, fallback_to_default=False)
       actually returns. On a clean machine this is the project's own file.
       On a machine that also has the same family installed system-wide
       (as this one does for Bebas Neue), it may return a *different* file
       under the same name — noted here, not hidden, since it means the
       plain name-based API can't be trusted alone as proof of self-
       containment when duplicates exist.

    Falls back to a system sans font (with a warning) if the project's own
    file for a family is missing entirely, rather than raising.
    """
    registered_fnames = {f.fname for f in fm.fontManager.ttflist}
    result = {}
    for family in (FONT_HEADING, FONT_BODY, FONT_MONO):
        regular_path = _FONT_FILES[family].get("regular")
        file_exists = regular_path is not None and regular_path.exists()
        registered = file_exists and str(regular_path) in registered_fnames

        try:
            name_lookup_path = fm.findfont(family, fallback_to_default=False)
        except ValueError:
            name_lookup_path = fm.findfont(
                fm.FontProperties(family=[_SYSTEM_FALLBACK_FAMILY])
            )
            print(
                f"[style] Warning: '{family}' could not be resolved by name at "
                f"all — falling back to '{_SYSTEM_FALLBACK_FAMILY}' "
                f"({name_lookup_path})"
            )

        matches_project_file = file_exists and name_lookup_path == str(regular_path)
        if registered and not matches_project_file:
            print(
                f"[style] Note: '{family}' is registered from the project file "
                f"({regular_path}), but a same-named font elsewhere on this "
                f"machine outranks it in name-based lookup — "
                f"fm.findfont() returned {name_lookup_path} instead. "
                f"Use style.get_font_properties('{family}') when rendering "
                f"to guarantee the project's own file is used."
            )

        result[family] = {
            "registered": registered,
            "name_lookup_path": name_lookup_path,
            "matches_project_file": matches_project_file,
        }
    return result


# --- Output resolution -----------------------------------------------------

SHEET_WIDTH_IN = 11.69
SHEET_HEIGHT_IN = 8.27
OUTPUT_WIDTH_PX = 1754
OUTPUT_HEIGHT_PX = 1240
DPI = OUTPUT_WIDTH_PX / SHEET_WIDTH_IN  # derived, not hardcoded twice

# Sheet 2 carries Panel 2 and Panel 3 side by side. The gap value reuses the
# 0.25in already settled on for Panel 1's own internal two-grid gap
# (panel_spec.md / CLAUDE.md), for visual consistency across the sheet.
PANEL_GAP_IN = 0.25
HALF_SHEET_WIDTH_IN = (SHEET_WIDTH_IN - PANEL_GAP_IN) / 2

# Panel 1's own internal margins/gap (CLAUDE.md "Fine-cell size, achieved not
# assumed") — kept here so panel code doesn't hardcode them separately.
PANEL1_MARGIN_IN = 0.15
PANEL1_GRID_GAP_IN = 0.25

# --- Branding assets (optional) --------------------------------------------

PERSONAL_LOGO_PATH = ASSETS_DIR / "OTF Logo Colour.png"  # path per panel_spec.md
STATSBOMB_LOGO_PATH = ASSETS_DIR / "Stastbomb Logo.png"


def get_badge_path(team_name: str) -> Path | None:
    """Return the PNG badge path for a team, or None if missing. Callers
    must render the team name alone when this returns None — never
    substitute another image or leave a blank box."""
    path = BADGES_DIR / f"{team_name}.png"
    return path if path.exists() else None


def get_personal_logo_path() -> Path | None:
    """Return the personal logo path, or None if absent. The footer must
    still render StatsBomb attribution and the generated date without it."""
    return PERSONAL_LOGO_PATH if PERSONAL_LOGO_PATH.exists() else None


def get_statsbomb_logo_path() -> Path | None:
    """Return the StatsBomb logo path, or None if absent — in which case
    callers must fall back to text attribution. StatsBomb attribution
    itself is never optional."""
    return STATSBOMB_LOGO_PATH if STATSBOMB_LOGO_PATH.exists() else None

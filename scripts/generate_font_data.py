"""Regenerate the woff2 faces embedded in the Remotion composer's bundle.

Downloads the latin-subset variable faces for Space Grotesk and Playfair
Display from the Google Fonts CSS API and rewrites
`remotion-composer/src/lib/fontData.ts` with them base64-encoded.

Why the fonts are embedded rather than fetched at render time: see
`remotion-composer/src/lib/localFonts.ts`. Short version — a font the render
has to wait for is a font that can fail the render, whether it stalls on the
network or never settles its promise in one of the browser tabs Remotion
recycles mid-render.

Run this only to pick up upstream font revisions; the generated file is
committed, so a normal checkout needs nothing.

Usage:
    python scripts/generate_font_data.py [--check]

    --check  Report whether the committed file is current; write nothing.
             Exits 1 if it is stale.
"""

from __future__ import annotations

import argparse
import base64
import re
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = PROJECT_ROOT / "remotion-composer" / "src" / "lib" / "fontData.ts"

# The CSS API serves variable woff2 only to browsers it recognises as modern;
# an older UA silently downgrades to per-weight ttf.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
)

# Every weight requested here resolves to the same variable file per style —
# asking for the range is what makes the API hand back the variable face.
FAMILIES = [
    {
        "css_url": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700",
        "faces": [("SPACE_GROTESK_NORMAL", "normal", "Space Grotesk")],
    },
    {
        "css_url": (
            "https://fonts.googleapis.com/css2?family=Playfair+Display:"
            "ital,wght@0,400;0,700;0,900;1,400;1,700"
        ),
        "faces": [
            ("PLAYFAIR_DISPLAY_NORMAL", "normal", "Playfair Display"),
            ("PLAYFAIR_DISPLAY_ITALIC", "italic", "Playfair Display"),
        ],
    },
]

# Each @font-face in the CSS is preceded by a subset comment; we want `latin`
# and not latin-ext / cyrillic / vietnamese.
FONT_FACE = re.compile(r"/\*\s*([\w-]+)\s*\*/\s*@font-face\s*\{(.*?)\}", re.S)

HEADER = """// Generated file — do not edit by hand.
// Regenerate: python scripts/generate_font_data.py
// Provenance, licensing and details: see ./FONTS.md
//
// The faces are embedded as base64 so that rendering never issues a network
// request for a font, and so that nothing has to be awaited to apply one.
// See ./localFonts.ts for why both of those matter.
"""


def fetch(url: str) -> bytes:
    return urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=60).read()


def latin_faces(css: str) -> dict[str, str]:
    """Map font-style -> woff2 URL for the latin subset only."""
    found: dict[str, str] = {}
    for subset, body in FONT_FACE.findall(css):
        if subset != "latin":
            continue
        style = re.search(r"font-style:\s*([\w-]+)", body)
        url = re.search(r"url\((https://[^)]+\.woff2)\)", body)
        if style and url:
            found.setdefault(style.group(1), url.group(1))
    return found


def render_module() -> str:
    blocks: list[str] = [HEADER]

    for family in FAMILIES:
        faces = latin_faces(fetch(family["css_url"]).decode("utf-8"))

        for const_name, style, display_name in family["faces"]:
            url = faces.get(style)
            if url is None:
                raise SystemExit(
                    f"No latin {style} face for {display_name} — the CSS API "
                    f"response changed shape:\n  {family['css_url']}"
                )

            raw = fetch(url)
            if raw[:4] != b"wOF2":
                raise SystemExit(
                    f"{display_name} {style} is not woff2 ({len(raw)} bytes). "
                    "The API likely downgraded the response; check USER_AGENT."
                )

            encoded = base64.b64encode(raw).decode("ascii")
            # Wrap so the generated file stays diff-friendly rather than
            # carrying three enormous single lines.
            chunks = [encoded[i:i + 100] for i in range(0, len(encoded), 100)]
            body = "\n".join(
                f'  "{chunk}"{";" if i == len(chunks) - 1 else " +"}'
                for i, chunk in enumerate(chunks)
            )
            blocks.append(
                f"/** {display_name} {style} — {len(raw):,} bytes */\n"
                f"export const {const_name}_WOFF2 =\n{body}\n"
            )

    return "\n".join(blocks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report whether the committed file is current; write nothing.",
    )
    args = parser.parse_args(argv)

    try:
        generated = render_module()
    except URLError as err:
        raise SystemExit(f"Could not reach the Google Fonts API: {err}")

    if args.check:
        if not OUTPUT.exists():
            print(f"{OUTPUT} is missing.")
            return 1
        if OUTPUT.read_text(encoding="utf-8") == generated:
            print(f"{OUTPUT.name} is up to date.")
            return 0
        print(f"{OUTPUT.name} is stale — rerun without --check.")
        return 1

    OUTPUT.write_text(generated, encoding="utf-8")
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

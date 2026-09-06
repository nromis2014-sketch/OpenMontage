# Bundled fonts

`fontData.ts` carries three base64-encoded woff2 faces, applied by
`localFonts.ts`. They replace `@remotion/google-fonts`, which fetched the same
faces from `fonts.gstatic.com` during every render.

| Constant | Family | Style | Weight range |
|---|---|---|---|
| `SPACE_GROTESK_NORMAL_WOFF2` | Space Grotesk | normal | 300–700 |
| `PLAYFAIR_DISPLAY_NORMAL_WOFF2` | Playfair Display | normal | 400–900 |
| `PLAYFAIR_DISPLAY_ITALIC_WOFF2` | Playfair Display | italic | 400–900 |

These are the `latin`-subset **variable** faces Google Fonts serves to current
browsers — one file per family and style, spanning the whole weight range, so
`fontWeight` still interpolates. Requesting individual weights returns the same
variable file each time, so storing one face per style is not lossy.

## Licensing

Both families are under the SIL Open Font License 1.1, which permits
redistribution alongside a project:

- Space Grotesk — <https://fonts.google.com/specimen/Space+Grotesk/license>
- Playfair Display — <https://fonts.google.com/specimen/Playfair+Display/license>

## Regenerating

The woff2 files are not kept in the repo, so regeneration re-downloads them
from the Google Fonts CSS API:

```bash
python scripts/generate_font_data.py
```

`--check` reports whether the committed file is current and writes nothing,
exiting non-zero when it is stale.

The script requests a weight *range* per family and keeps only the
`/* latin */` face, which is what makes the API return one variable file per
style rather than several static ones. It sends a current-browser User-Agent
for the same reason — an older UA silently downgrades the response to
per-weight ttf — and rejects any download not starting with the woff2 magic
bytes `wOF2`, so a downgraded response fails loudly instead of embedding an
unusable face.

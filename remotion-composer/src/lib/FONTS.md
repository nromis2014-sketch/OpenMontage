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

The woff2 files are not kept in the repo — `remotion-composer/public/` is
gitignored — so regeneration re-downloads them:

1. Fetch the CSS with a **current-browser User-Agent** (an older UA yields
   non-variable ttf/woff):

   ```
   https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700
   https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700
   ```

2. From each response take the `@font-face` block commented `/* latin */` —
   not `latin-ext`, `cyrillic` or `vietnamese` — and download its woff2 URL.
3. Base64-encode each file and replace the corresponding constant in
   `fontData.ts`. Verify each download starts with the magic bytes `wOF2`.

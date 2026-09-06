import {
  PLAYFAIR_DISPLAY_ITALIC_WOFF2,
  PLAYFAIR_DISPLAY_NORMAL_WOFF2,
  SPACE_GROTESK_NORMAL_WOFF2,
} from "./fontData";

/**
 * Self-hosted replacements for `@remotion/google-fonts`.
 *
 * The Google Fonts loaders fetch woff2 files from fonts.gstatic.com during the
 * render. Because the loaders run at module scope, a failed fetch aborts the
 * whole composition before a single frame is drawn — which made the "zero-key"
 * demos depend on live internet.
 *
 * The faces are compiled into the bundle as base64 (see `./fontData`) and
 * declared with plain `@font-face` rules whose `src` is a `data:` URI.
 *
 * Two failure modes drove that design. Fetching from fonts.gstatic.com (or
 * even from `public/`) can stall, and registration runs on every tab Remotion
 * spins up — it renders with several and recycles them mid-render. More
 * importantly, awaiting `FontFace.load()` under a delayRender() handle does not
 * reliably settle in those tabs: the handle stays uncleared and Remotion kills
 * the render at whatever frame is in flight. So this module blocks on nothing.
 * The bytes are already present, and the browser parses them during layout.
 *
 * As with `@remotion/google-fonts`, `fontFamily` is the family name for every
 * style — callers select italics with `fontStyle: "italic"`.
 */

export type FontStyle = "normal" | "italic";

type Face = {
  style: FontStyle;
  /** base64-encoded woff2. */
  data: string;
  /** Variable weight range, as a CSS `font-weight` descriptor. */
  weights: string;
};

type FamilySpec = {
  family: string;
  faces: Face[];
};

const SPACE_GROTESK: FamilySpec = {
  family: "Space Grotesk",
  faces: [
    { style: "normal", data: SPACE_GROTESK_NORMAL_WOFF2, weights: "300 700" },
  ],
};

const PLAYFAIR_DISPLAY: FamilySpec = {
  family: "Playfair Display",
  faces: [
    { style: "normal", data: PLAYFAIR_DISPLAY_NORMAL_WOFF2, weights: "400 900" },
    { style: "italic", data: PLAYFAIR_DISPLAY_ITALIC_WOFF2, weights: "400 900" },
  ],
};

const registered = new Set<string>();

function faceRule(family: string, face: Face): string {
  return [
    "@font-face {",
    `  font-family: "${family}";`,
    `  font-style: ${face.style};`,
    `  font-weight: ${face.weights};`,
    // Wait for the face rather than flashing a fallback. There is nothing to
    // wait on but a synchronous parse, so this never delays a frame for long.
    "  font-display: block;",
    `  src: url(data:font/woff2;base64,${face.data}) format("woff2");`,
    "}",
  ].join("\n");
}

function register(spec: FamilySpec): { fontFamily: string } {
  // Server-side passes (composition discovery, calculateMetadata) have no
  // document to register against.
  if (typeof document === "undefined" || registered.has(spec.family)) {
    return { fontFamily: spec.family };
  }
  registered.add(spec.family);

  const style = document.createElement("style");
  style.setAttribute("data-font", spec.family);
  style.textContent = spec.faces
    .map((face) => faceRule(spec.family, face))
    .join("\n");
  document.head.appendChild(style);

  return { fontFamily: spec.family };
}

/** Drop-in for `loadFont` from `@remotion/google-fonts/SpaceGrotesk`. */
export const loadSpaceGrotesk = (): { fontFamily: string } =>
  register(SPACE_GROTESK);

/** Drop-in for `loadFont` from `@remotion/google-fonts/PlayfairDisplay`. */
export const loadPlayfairDisplay = (): { fontFamily: string } =>
  register(PLAYFAIR_DISPLAY);

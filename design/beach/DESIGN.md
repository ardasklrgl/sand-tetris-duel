---
name: Night beach preview (provisional)
description: First standalone art preview; not the game's global design system.
colors:
  ink: "#ece6f5"
  muted: "#c0b9d1"
  line: "#51475e"
  surface: "#15121e"
  night: "#09070f"
  hover: "#2b223a"
  active: "#3b2c50"
  accent: "hsl(265 72% 77%)"
  focus: "hsl(55 72% 77%)"
  link: "hsl(55 72% 77%)"
typography:
  body: {fontFamily: "SFMono-Regular, Menlo, Consolas, monospace", fontSize: "12px", lineHeight: 1.5}
  title: {fontFamily: "SFMono-Regular, Menlo, Consolas, monospace", fontSize: "14px", fontWeight: 600}
  letters: {fontFamily: "Menlo, Consolas, monospace", fontSize: "6px", fontWeight: 500}
rounded: {button: "8px", panel: "10px", settings: "12px"}
spacing: {desktop-inset: "28px", mobile-inset: "18px", action-gap: "8px"}
components:
  button: {backgroundColor: "{colors.surface}", textColor: "{colors.ink}", rounded: "{rounded.button}", padding: "9px 13px"}
---
# Night beach preview
## Overview
Restored original soft-color beach treatment from the user's preferred screenshot. Preserve the restored exposure and original single-pass glow. Map source luminance to two shifting hue families: purple shadows, yellow highlights. The threshold slider controls the transition.
## Colors
Source luminance is retained while source RGB is replaced by the Flow hues, starting265° and55°, shifting0.85° per active second. The threshold sets the tint blend center, range0–1, default0.42, with0.16 half-width; hue luminance is normalized so applying the palette preserves the original exposure. Bright source pixels blend42% toward neutral. The original nine-sample glow now samples glyph-masked light, normalized by stroke coverage to retain its strength.
## Typography
Fixed continuous flattened README text in Menlo/Consolas, default6px. Letter positions stay fixed while source light moves.
## Layout
Full-screen standalone preview. Five setting columns on desktop, three below1100px, two below650px. Details panel sits above measured toolbar height. Original video uses cover cropping.
## Elevation & Depth
Single-pass glow: sample graded light only inside letter strokes at nine nearby points, normalize coverage, and add the highlight halo. Direct light also uses the glyph mask; no uniform ambient or unmasked image light is added. No framebuffer capture, multi-pass blur, artificial emission boost or new tone mapper.
## Shapes
Original compact rounded controls and dark translucent panels.
## Components
Letter size4–20px, brightness0.6–2.4 (default1.2), threshold0–1 (default0.42), glow0–1.5 (default1.5), speed0.25–1.25× (default0.75). Pause freezes footage and shifting accents. Reduced motion starts still. Source comparison remains available.
## Do's and Don'ts
- Preserve the preferred original glow and source luminance while using the two theme colors.
- Limit this revision to restoration plus threshold control; game integration is deferred.

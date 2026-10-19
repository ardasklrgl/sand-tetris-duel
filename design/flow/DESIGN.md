---
name: Flow — beach integration
description: Scoped record of the Flow variant, retaining its established game interface.
colors:
  bg: "#101116"
  panel: "#000"
  line: "#353641"
  muted: "#a9abb8"
  ink: "#eeeef5"
  ai: "hsl(265 72% 77%)"
  you: "hsl(55 72% 77%)"
typography:
  title: {fontFamily: "SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace", fontSize: "21px", fontWeight: 500, letterSpacing: "-.8px"}
  letters: {fontFamily: "Menlo, Consolas, monospace", fontSize: "4px", fontWeight: 500}
rounded: {main: "24px", board: "12px", button: "9px", scoreboard: "16px", result: "16px"}
components:
  button: {backgroundColor: "#1c1d26", rounded: "{rounded.button}", textColor: "{colors.ink}"}
---
# Flow beach integration
## Overview
**Creative North Star: "A duel above a shoreline written in README prose"**
This record covers the Flow variant's beach integration: established rounded Apple geometry and monospace game UI sit above fixed README letters lit by supplied moonlit video. Other game variants and the standalone preview remain separate.
## Colors
Dark neutral game surfaces retain readable ink and muted labels. AI/purple and player/yellow UI accents shift together at hue = 265 + active seconds × 0.85, the second hue 150° ahead; UI saturation/lightness are 72%/77%, artwork 72%/66%. Video luminance selects/blends the artwork's two hues. Game sand colors remain fixed.
## Typography
The title uses the token's system monospace stack; buttons are 11px, board titles 13px, stats 15px, scores 32px. Dense artwork repeats flattened README in its separate 4px letters stack; resizing rebuilds cells, animation leaves glyph positions fixed. The README explicitly repeats from its start until every viewport cell is filled; window resize and canvas-size observation both refresh coverage. Render one complete text row per draw to avoid missing raster regions observed with hundreds of thousands of individual glyph draw calls at high screen density.
## Layout
A centered column has maximum width 760px, padding 34px 44px 30px, with 24px between boards. At ≤700px main padding is 26px 24px and radius 20px; at ≤480px main padding is 24px 14px, radius zero, boards gap 14px and radius 8px. Background fills the viewport without stretching. Where a desktop right margin is available, the moon and reflection sit55% across that margin beyond the player board; use minimal proportional cropping to stay within the source frame. Phones keep centered cover cropping.
## Elevation & Depth
Main has a 40% dark tint, rgba(17,18,25,.40), and no shadow; the beach remains visible through it. Game boards, the shared match panel, and the existing scoreboard keep their own dark surfaces. The result popup sits over the boards at z-index 3, with #191a26f5, 1px line border and shadow 0 12px 38px #0009. Artwork uses a blurred glyph halo and subtle vignette.
## Shapes
Rounded main, boards, buttons, scoreboard and result follow the tokens; numeric inputs use 8px corners. The result is centered on the board region, constrained to available width, with 18px 22px padding (15px 19px on phones).
## Components
Board titles sit at the top-left inside black rounded board frames, in a35px header strip (32px on phones) above the unchanged gameplay canvas. One black match panel contains both stats groups, movement/drop/pause controls, keyboard help, seed input, replay and new match. It matches the scoreboard surface and16px radius, with22px24px padding (18px14px phone), two aligned stats columns and a22px gap before controls. Stats retain their original IDs for live updates.
The background has fixed approved settings: letterSize 4px, brightness 1.2, threshold 0.42, glow 1.5, waveSpeed 0.75. Still background/Animate background freezes/resumes footage and palette; reduced motion starts still, hidden tabs pause. Drawing caps near 30fps and device pixel ratio 1.5. Failure hides the background and disables its toggle. Existing gameplay and popup controls retain their behavior; button/input transitions are 180ms ease and focus outline is 2px player hue with 3px offset.
Media is the user's Gemini moonlit landscape video and the flattened local README, shared through /beach-assets/; provenance remains in design/beach/assets/SOURCE.md. The integration adds no preview settings toolbar.
## Do's and Don'ts
- Do retain fixed sand colors, readable game surfaces and the background motion toggle.
- Don't treat this Flow integration as replacement documentation for other game variants.

Match and scoreboard panels use pure black; the progress track is black with its colored completed segment retained.

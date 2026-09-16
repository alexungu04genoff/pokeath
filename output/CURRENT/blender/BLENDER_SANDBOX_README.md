# Blender sandbox kit

This folder is an editable, disposable Blender test kit. It is not an input to the production chassis generator or validation baseline. Manual edits made here must never be copied back to the real boards without a deliberate new engineering and validation pass.

STL is unitless. Import and export every STL here as **millimetres** in Blender. OBJ files contain the same geometry and coordinates for convenience.

## Coordinate convention

All bottom surfaces are at Z=0. Generic pieces use a lower-left local XY origin. The sloped prototype references intentionally share one assembly coordinate system: the two ordinary board spaces occupy X=0..86 and Y=0..48; test lugs extend to Y=-8 and Y=56. `sloped_part_B_reference` therefore begins at X=38.2 rather than resetting to X=0. This makes A, B, isolated lugs, and assembled references line up when imported together.

Standalone pin references have their own bottom at Z=0. In `START_HERE`, pins are positioned 0.2 mm upward to reproduce their table-clearance position in the joint.

## Canonical compatibility surfaces

Keep these unchanged if an edited part might later need to interoperate with the canonical system:

- Universal socket: 36 × 36 mm, 3 mm deep, R2 corners, with its current common top fingernail recess.
- Grid pitch: 38 mm; normal divider: 2 mm; board thickness: 10 mm; ordinary outer track rim: 6 mm.
- Tile interface: the socket floor and all four socket walls; tile clearance is not selected yet. The generic 36 × 36 tile is a nominal reference, not a confirmed print-fit tile.
- Section seam: 0.25 mm. The production snap-key/rail system remains canonical; the sloped lap lock is experimental and must not be propagated yet.

## Experimental sloped lock reference

The current experimental lock uses 45-degree sloped lap faces with 0.4 mm vertical / 0.283 mm face-normal gap. It projects 8 mm locally outside the ordinary rim. A is below Z=47.8−X and B is above Z=48.2−X. Representative 4 mm and 5 mm pin families use 4.4 mm and 5.4 mm bores respectively; both shown pins use the 0.20 mm-per-side fit variant. Pin head: 12 × 8 × 2.4 mm with a 0.6 mm shaft/root fillet. The 5 mm bore has a 2.1 mm minimum bearing thickness at its limiting edge. These dimensions are test geometry only.

## Files

| File stem | Role | XYZ extent (mm) |
| --- | --- | ---: |
| sloped_part_A_reference | production-reference prototype half A | 47.800 × 64.000 × 10.000 |
| sloped_part_B_reference | production-reference prototype half B | 47.800 × 64.000 × 10.000 |
| pin_4mm_020_clearance_reference | experimental 4 mm pin reference | 12.000 × 8.000 × 12.200 |
| pin_5mm_020_clearance_reference | experimental 5 mm pin reference | 12.000 × 8.000 × 12.200 |
| START_HERE | assembled reference mesh: A + B + 4 mm and 5 mm pins | 86.000 × 64.000 × 12.200 |
| blank_test_tile_0.15mm_per_side_1_dots_reference | tile-clearance test reference | 35.700 × 35.700 × 2.800 |
| blank_test_tile_0.20mm_per_side_2_dots_reference | tile-clearance test reference | 35.600 × 35.600 × 2.800 |
| blank_test_tile_0.25mm_per_side_3_dots_reference | tile-clearance test reference | 35.500 × 35.500 × 2.800 |
| blank_test_tile_0.30mm_per_side_4_dots_reference | tile-clearance test reference | 35.400 × 35.400 × 2.800 |
| generic_canonical_36mm_tile | nominal generic tile; not a selected print fit | 36.000 × 36.000 × 2.800 |
| generic_single_space_chassis | generic single-space canonical chassis | 48.000 × 48.000 × 10.000 |
| generic_2x2_chassis | generic 2×2 canonical chassis | 86.000 × 86.000 × 10.000 |
| sloped_lug_A_lower_4mm_reference | isolated lower mating lug | 14.800 × 11.000 × 10.000 |
| sloped_lug_B_upper_4mm_reference | isolated upper mating lug | 14.800 × 11.000 × 10.000 |

`START_HERE` is the only deliberately assembled multi-part reference mesh. All other files remain separate for editing. Use `boards/`, `tiles/`, `pins/`, and `experimental_parts/` to locate the individual files.

Production references: `sloped_part_A_reference`, `sloped_part_B_reference`, and the exported tile/socket dimensions. Disposable experiments: generic chassis pieces, isolated lugs, pins, generic tile, and all manual Blender edits.

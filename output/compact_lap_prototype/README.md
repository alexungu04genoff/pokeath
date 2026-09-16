# Compact 2 x 1 lap-pin prototype

Only this prototype is revised. All 16 production quadrants are hash-verified unchanged.

Gameplay chassis: 86 x 48 x 10 mm. Pitch 38 mm; sockets 36 x 36 mm, R2, depth 3 mm; dividers 2 mm; normal rim 6 mm; existing removal recess; board seam 0.25 mm. Socket floor has 7 mm solid material below it. Local mechanism-to-socket ligament: 2.75 mm.

Each compact rounded rectangular tab has a 16 x 11 mm core, R2 corners and a 20 mm wide reinforced root with R2 transition fillets. It extends 8 mm beyond the front/back rim locally at the seam. Body envelope: 86 x 64 x 10 mm; installed pins increase total height to 12.4 mm. Overlapping footprint bounding box is 20 x 11 mm including the widened root (less bores and rounded corners). A lower tab: Z=0–4.8 mm, thickness 4.8 mm. B upper tab: Z=5–10 mm, thickness 5 mm. Vertical clearance 0.2 mm; outline clearance 0.25 mm. These are rigid half-lap tabs, with no spring or flexing feature.

Slide B horizontally from +X toward A. Partial XY tab overlap necessarily occurs during joining; their Z intervals never overlap. Hole axes are offset by exactly the B translation and become coaxial only at full seating. Clearance means a pin can begin fitting slightly before perfect seating; it is not an exact-position interlock. Insert pins down from above, and pull their heads upward to remove. Both pins reduce yaw; try either size alone to compare stiffness. Gravity retains the pins upright; do not invert or carry by one section.

| Family | Shaft mm | Hole mm | Clearance/side | Straight wall | Entry wall |
|---|---:|---:|---:|---:|---:|
| 4 | 4.10 | 4.40 | 0.15 | 2.80 | 2.10 |
| 4 | 4.00 | 4.40 | 0.20 | 2.80 | 2.10 |
| 4 | 3.90 | 4.40 | 0.25 | 2.80 | 2.10 |
| 4 | 3.80 | 4.40 | 0.30 | 2.80 | 2.10 |
| 5 | 5.10 | 5.40 | 0.15 | 2.30 | 1.60 |
| 5 | 5.00 | 5.40 | 0.20 | 2.30 | 1.60 |
| 5 | 4.90 | 5.40 | 0.25 | 2.30 | 1.60 |
| 5 | 4.80 | 5.40 | 0.30 | 2.30 | 1.60 |

Pin head: 12 x 8 x 2.4 mm, R1.5 corners; shaft/head fillet 0.6 mm; tip lead-in 0.4 mm radial / 0.5 mm axial. Shaft length below head 9.8 mm; installed tip Z=0.2 mm. Upper hole lead-in 0.7 mm; lower 0.4 mm. Family numeral plus 1–4 dots are engraved only on head tops.

## Print orientation and supports

Print supplied STLs at 100%, preserving orientation. A: flat base down, sockets up, support-free. B: same orientation; its two thick upper tabs are cantilevers and need accessible supports under Z=5 mm. There are no enclosed support cavities or horizontal internal ceilings. A 45-degree underside ramp under B would occupy A’s mating volume, so it is intentionally omitted. Do not put supports in bores or sockets. Clean the exposed tab undersides before joining.

Pins: flat T-head on plate, smooth shaft vertically upward; predicted support-free. Never lay pins sideways. Head engravings require only short first-layer bridges. Use no brim initially, adding a 2 mm pin-only brim if adhesion needs it. Brim/support footprints are not included in STL bounds. Blank tiles print flat, support-free. Suggested 0.20 mm layers, 0.4 mm nozzle, calibrated PLA, at least four walls and solid pins/lugs; verify slicer paths.

Four blank tile tests have exact R2 corners and 2.8 mm thickness: 35.70 / 35.60 / 35.50 / 35.40 mm, identified by 1–4 dots. They sit 0.2 mm below dividers. Test both sockets, rotations/flipping, drop-in, removal, binding, rattle, divider feel, seam wobble, repeated pin insertion/removal and visible wear. Neither clearance is frozen.

## Validation

Socket floors were checked against the real universal footprint. Assembled A/B have no volumetric intersection. Horizontal assembly was sampled every 0.25 mm over 20 mm of travel; every position is collision-free. Pin seating and 23 vertical insertion/withdrawal positions per variant are collision-free. Each seated pin blocks a 1 mm lateral pull-apart. Rigid tabs occupy disjoint Z intervals throughout the path. All 14 individual STLs reload as single connected watertight/manifold solids with positive volume. The combined plate contains 14 separate closed solids. No true slicer run or physical test has been performed.

## Limits

Upper-tab support scars can affect the 0.2 mm lap gap. Vertical PLA pins depend on layer adhesion; inspect cracking at roots. Minimum chamfer wall is 1.6 mm on the larger bore. Tabs are substantially thicker than the recessed experiment, but wear and strength remain untested. R2 tab outline corners soften the shape; load-bearing tab roots remain a stress concentration to inspect during cycling. Smooth pins can lift out if inverted. Larger clearances permit rattle. No colored or special gameplay tiles are generated.

See assembly_sequence_sections.png, pin_lug_dimensions.png, validation.json and the A1 placement previews.

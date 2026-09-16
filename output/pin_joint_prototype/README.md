# Two-space PLA pin-joint physical prototype

Part A and B form two adjacent canonical spaces. Push horizontally together, then insert one vertical pin through each outboard stepped lug. Red A has lower ears; yellow B has upper ears. T heads rest on B and retain pins by gravity. Pull heads upward to remove. Both pins are recommended for a rigid joint; test either size alone to compare. Hold both halves when lifting: this is not a captive transport lock.

Gameplay chassis: 86 x 48 x 10 mm, plus outboard lug projections. Wells: 36 x 36 mm, 3 mm deep, R2; pitch 38 mm, nominal dividers 2 mm, external track rim 6 mm. The fingernail recess is unchanged. The lug footprint is outside the sockets; only local rim/staging volume changes. No socket is intersected by a seam or bore.

| Family | Shaft diameter | Bore diameter | Clearance per side | Head marking |
|---|---:|---:|---:|---|
| 4 mm | 4.10 | 4.40 | 0.15 | 4 + 1 dots |
| 4 mm | 4.00 | 4.40 | 0.20 | 4 + 2 dots |
| 4 mm | 3.90 | 4.40 | 0.25 | 4 + 3 dots |
| 4 mm | 3.80 | 4.40 | 0.30 | 4 + 4 dots |
| 5 mm | 5.10 | 5.40 | 0.15 | 5 + 1 dots |
| 5 mm | 5.00 | 5.40 | 0.20 | 5 + 2 dots |
| 5 mm | 4.90 | 5.40 | 0.25 | 5 + 3 dots |
| 5 mm | 4.80 | 5.40 | 0.30 | 5 + 4 dots |

Bores remain fixed at 4.40 and 5.40 mm, so changing the actual shaft diameter tests fit on the same pair of bodies. The 0.20 mm-per-side variants have exactly 4.00 and 5.00 mm shafts. All mating shafts are smooth, with no threads, hooks or spring features.

T heads: 12 x 6 x 2.4 mm, R1.5 plan corners, 0.4 mm shaft/head root fillet. Shaft engagement length 9.8 mm; bottom tip is 0.2 mm above the table. Bottom lead-in: 0.4 mm radial / 0.5 mm axial. Bore lead-in: 0.4 mm on A and 0.5 mm on B. Both solid ears are 4.875 mm thick, with 0.25 mm vertical clearance and 0.25 mm mating outline clearance. Lug supports use R7 lobes and R2 neck/root fillets.

Minimum wall around the straight bore: 4.80 mm (4 mm family), 4.30 mm (5 mm family). Minimum at the widest entry chamfer: 4.30 / 3.80 mm respectively.
Minimum material between locking cutouts and a tile socket: **2.152 mm**. All lug outlines are outside the tile socket projections.

## Print and test

Use PLA, 0.4 mm nozzle and 100% scale. For the two bodies, use 0.125 mm layers including the first layer: 4.875 mm and 5.125 mm then land exactly on layer boundaries, preserving the 0.25 mm lap gap. Using 0.20 mm body layers is possible but quantizes the vertical lap clearance. Pins and tiles can use 0.20 mm layers. Use four or more walls and solid infill in lugs and pins (local modifiers for lugs); verify load-bearing sections in the slicer. Do not auto-orient the supplied STLs. No brim is included in dimensions.

Part A: socket up, underside flat on the bed, no support needed. Part B: socket up, painted supports under the two raised ears only. They start at Z=5.125 mm; total supported ear underside is about 315.6 mm². Keep support out of bores and wells. Inspect and clean those mating undersides before assembling.

Pins are supplied horizontally to improve PLA bending strength along the shaft. Add light supports below the round shaft and root fillet. Remove scars without changing the fit diameter. For an initial support-free fit-only print, rotate shaft vertical with the flat T-head top on the bed; this orientation is weaker for repeated joint loading. Vertical bore orientation in the bodies needs no internal support.

Reuse the four included 2.8 mm blank tile tests: 35.70 / 35.60 / 35.50 / 35.40 mm, respectively 0.15 / 0.20 / 0.25 / 0.30 mm clearance per side. Existing one-to-four top dots identify them. They sit 0.2 mm below the dividers.

Test tile insertion/removal in both sockets and four rotations, repeated swapping/flipping, rattle, feel of the recess/dividers, seam flushness, pin insertion/removal, lateral joint rigidity with one and both pins, and visible PLA wear after repeated assembly. Start with 0.20 mm pin clearance; compare all four before selecting either pin or tile tolerance.

## Digital validation

Both socket floors match the canonical rounded square, with no pin/lug intrusion. Assembled parts do not intersect; all pin variants seat without interference. Translating B 1 mm outward with either seated pin fixed encounters solid interference, demonstrating a positive lateral stop. Every exported STL reloads as a connected, watertight mesh with consistent winding, two incident faces per edge, positive volume and an A1-compatible XY envelope. Production quadrant SHA-256 hashes are unchanged.

| STL | X x Y x Z, mm | Manifold / A1 fit |
|---|---|---|
| prototype_2x1_part_A.stl | 51.000 x 67.999 x 10.000 | Pass |
| prototype_2x1_part_B.stl | 50.999 x 67.999 x 10.000 | Pass |
| pins\T_pin_4mm_family_clearance_0.15_shaft_4.10.stl | 12.000 x 12.200 x 6.000 | Pass |
| pins\T_pin_4mm_family_clearance_0.20_shaft_4.00.stl | 12.000 x 12.200 x 6.000 | Pass |
| pins\T_pin_4mm_family_clearance_0.25_shaft_3.90.stl | 12.000 x 12.200 x 6.000 | Pass |
| pins\T_pin_4mm_family_clearance_0.30_shaft_3.80.stl | 12.000 x 12.200 x 6.000 | Pass |
| pins\T_pin_5mm_family_clearance_0.15_shaft_5.10.stl | 12.000 x 12.200 x 6.000 | Pass |
| pins\T_pin_5mm_family_clearance_0.20_shaft_5.00.stl | 12.000 x 12.200 x 6.000 | Pass |
| pins\T_pin_5mm_family_clearance_0.25_shaft_4.90.stl | 12.000 x 12.200 x 6.000 | Pass |
| pins\T_pin_5mm_family_clearance_0.30_shaft_4.80.stl | 12.000 x 12.200 x 6.000 | Pass |
| tiles\blank_test_tile_0.15mm_per_side_1_dots.stl | 35.700 x 35.700 x 2.800 | Pass |
| tiles\blank_test_tile_0.20mm_per_side_2_dots.stl | 35.600 x 35.600 x 2.800 | Pass |
| tiles\blank_test_tile_0.25mm_per_side_3_dots.stl | 35.500 x 35.500 x 2.800 | Pass |
| tiles\blank_test_tile_0.30mm_per_side_4_dots.stl | 35.400 x 35.400 x 2.800 | Pass |

## Limits and PLA risks

- Canonical fingernail recess locally leaves 1 mm of divider at the top; do not pry with tools.
- Upper B ears are unsupported during printing without painted supports; remove support scars carefully.
- Smooth gravity pins prevent lateral pull-apart but are not captive against vertical lifting or inversion.
- Largest pin clearance permits up to about 0.6 mm relative play; test rattle and seam movement.
- PLA wear, actual pin/ear strength and repeated-use durability require the physical print test.

No thin spring, hook, cantilevered latch or repeated-flex retention is present. The raised B lugs are thick structural ears, but require printing support. Digital collision tests do not predict PLA fatigue, layer adhesion or print tolerances. Dimensions come from exported meshes, not an actual Bambu Studio slicing run. No tolerance or production-lock change is frozen by this prototype. No colored/gameplay-effect tiles are generated.

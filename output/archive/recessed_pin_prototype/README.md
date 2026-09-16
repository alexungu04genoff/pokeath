# Fully recessed underside pin prototype

The canonical chassis envelope is 86 x 48 x 10 mm, with R8 exterior corners. All locking geometry and seated heads remain within it. Wells remain 36 x 36 mm, R2, 3 mm deep; pitch 38, dividers 2, outside rim 6, seam gap 0.25 mm. Both floors remain whole. Four blank 2.8 mm tile tests are copied unchanged. No production quadrant is modified.

Two compact clevis-style stations use one lower A lug and one interleaving upper B lug each, supported by broad internal backbones. This depth budget uses two bearing lugs per station. Both pin axes are under the divider, but neither bore nor pin reaches it or either socket: the cavities stop at Z=4.6 mm, below floors at Z=7 mm, leaving **2.4 mm solid roof** under the sockets.

Each housing is 20 x 12 mm, R2, centred at X=43 and Y=14 / 34 mm. A lower lug spans Z=1.2..2.8 (1.6 mm); B upper lug crosses the seam at Z=3.0..4.4 (1.4 mm), with 0.2 mm vertical clearance. Both lug footprints are 10 mm wide with R1 corners. B connects upward to its own roof at Z=4.6. Backbones and opposing lugs retain 0.25 mm XY clearance. The upper lug clears the opposite roof by 0.2 mm. Internal CAD roots overlap surrounding solid by 0.02 mm for robust manifold unions; this does not reduce the minimum 2.4 mm socket roof or change joint clearances.

45-degree shoulders along the central 15.6 mm of each cavity roof narrow the horizontal span from 12 to 10 mm. The rounded end regions retain short portions of the original ceiling. The shoulders rise from approximately Z=3.6 to Z=4.6 and do not collide with the interleaving lugs. The central ceiling is a two-sided bridge candidate, not a guaranteed support-free surface.

Pin head: 10 x 8 x 1 mm, bottom Z=0.2, top Z=1.2. Shaft: Z=1.2..4.2, length 3 mm, generous 0.6 mm root fillet and 0.4 mm tip lead-in. Lower bore entry has a matching 0.7 mm 45-degree chamfer; upper entry remains 0.3 mm. Minimum lower-entry lug wall is reported below. Pin heads seat against the underside of A's lower lug. No threads, spring, hook or snap feature is present.

| Family | Shaft | Hole | Clearance per side | Minimum entry wall |
|---|---:|---:|---:|---:|
| 4 | 4.10 | 4.40 | 0.15 | 2.10 |
| 4 | 4.00 | 4.40 | 0.20 | 2.10 |
| 4 | 3.90 | 4.40 | 0.25 | 2.10 |
| 4 | 3.80 | 4.40 | 0.30 | 2.10 |
| 5 | 5.10 | 5.40 | 0.15 | 1.60 |
| 5 | 5.00 | 5.40 | 0.20 | 1.60 |
| 5 | 4.90 | 5.40 | 0.25 | 1.60 |
| 5 | 4.80 | 5.40 | 0.30 | 1.60 |

Family numeral and one-to-four dots are on the exposed underside of each head, outside seating/mating surfaces. Existing tile dots identify clearances 0.15 / 0.20 / 0.25 / 0.30 per side, giving 35.70 / 35.60 / 35.50 / 35.40 mm tiles, thickness 2.8 mm.

## Print and assembly

Use the combined `prototype_2x1_ALL_COMPONENTS_A1.stl` for one session. Import at 100% without auto-arranging. Use 0.20 mm layers, a 0.4 mm nozzle and your calibrated PLA profile. Make the lug regions and pins solid PLA; use four or more walls. Bodies are flat-base-down, sockets-up. Pins are exported flat T-head on the bed, smooth shaft vertically upward. Do not lay pins on their sides. The shaft narrows upward through its fillet; the head identification engravings involve only small first-layer bridges. Pins and flat tiles are predicted support-free. Start without brim; a 2 mm pin-only brim is optional if adhesion fails. No brim is included in the geometry or placement bounds.

Pins and blank tiles: predicted support-free, head/base down. Bodies: selective supports still required below interleaving lug cantilevers; 45-degree roof shoulders need none. The remaining 10 mm two-sided roof span is a bridge candidate; test bridging and inspect in slicer, support locally if needed. Avoid bores, mating surfaces and sockets. Remove supports before assembly.

Remaining cross-seam lug undersides are one-sided cantilevers, not printable two-sided bridges. Selectively support these; 45-degree roof shoulders need no support. Trial the 10 mm central roof bridges and inspect the rounded ceiling end regions in the slicer, adding local roof supports if necessary. Support cleanup is possible through the open underside and seam before assembly; avoid bores, mating faces and sockets. No slicer toolpath, bridging test or physical support-removal test has been performed.

Join both halves on their sides or upside down, then push the smooth pins upward from the underside until heads seat. Set the board on a flat table. Heads are recessed 0.2 mm and the table traps them, allowing only 0.2 mm downward travel, leaving at least 1 mm upper-lug shaft engagement. They are not captive when the board is lifted. Hold the heads/support the assembly when lifting; expose the underside and pull the head to remove. No repeated flexing is required.

## Validation and limits

Both exported socket floors match the universal rounded square; all 14 STLs are connected, watertight/manifold and fit the A1. Part A and B do not overlap. All eight pin variants seat, pull out downward without collision and block 1 mm lateral separation. Locking projections remain inside the canonical XY outline. Production hashes are unchanged. Previews include underside with/without pins and actual mesh sections through both pin stations, showing the socket floors and 2.4 mm roof.

**PLA risk:** the 1.4 mm cross-seam upper lug and 1.0 mm head are thin relative to a larger external joint. Their broad roots and short shaft reduce leverage, but repeated-use durability is not established. Print solid, avoid prying and test wear. The head retains 0.8 mm beneath its 0.2 mm identification engraving. Vertical pin layer adhesion remains a strength limit; these pins must stay head-down, shaft-up.

STL bounds are measured geometrically; no Bambu Studio slicing run, strength simulation or physical fit test has been performed. No pin/tile clearance is frozen and no gameplay tiles are generated.

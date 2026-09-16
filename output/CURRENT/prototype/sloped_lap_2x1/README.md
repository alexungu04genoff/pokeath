# Sloped 2 x 1 pin prototype

Canonical gameplay geometry is preserved: pitch 38; socket 36 x 36, R2, depth 3; divider 2; normal rim 6; chassis thickness 10; seam 0.25 mm; original fingernail recess. The compact tab footprint retains the 8 mm local external projection and R2 reinforced roots. All 16 production quadrants are unchanged.

A occupies the volume below Z=47.8-X; B occupies the volume above Z=48.2-X, clipped to Z=0..10. Both mating faces are 45 degrees. Their vertical separation is 0.4 mm, equivalent to 0.283 mm normal clearance. Translating B outward by d increases the gap to 0.4+d, so horizontal joining cannot geometrically wedge these faces together. They guide vertical alignment when contacting, but are not a precision self-centering coupling. The vertical pin remains the primary lateral lock.

At the pin axis X=43: A is 4.8 mm thick and B is 4.8 mm thick. At the widest 5.4 mm bore edges, each retains at least 2.1 mm vertical bearing thickness. This is the limiting section to inspect for PLA wear. T-head remains 12 x 8 x 2.4 mm, root fillet 0.6 mm, tip lead-in 0.4 mm radial / 0.5 mm axial, upper bore chamfer 0.7 mm. The lower bore opens directly into the sloped face; no horizontal counterbore is cut. Socket floor retains 7 mm solid material; mechanism-to-socket ligament remains 2.75 mm.

| Family | Shaft | Bore | Clearance per side |
|---|---:|---:|---:|
| 4 | 4.10 | 4.40 | 0.15 |
| 4 | 4.00 | 4.40 | 0.20 |
| 4 | 3.90 | 4.40 | 0.25 |
| 4 | 3.80 | 4.40 | 0.30 |
| 5 | 5.10 | 5.40 | 0.15 |
| 5 | 5.00 | 5.40 | 0.20 |
| 5 | 4.90 | 5.40 | 0.25 |
| 5 | 4.80 | 5.40 | 0.30 |

## Print orientation and support prediction

Both board halves print flat-base-down, socket-up. A grows inward as it rises. B starts on a full-height-connected foot and expands leftward at 45 degrees; the prior floating horizontal ear is removed. No large horizontal tab underside remains. The circular bore interrupts the slope and may require short local bridges up to 5.4 mm; inspect those toolpaths in Bambu Studio. Start without supports on the tabs if the calibrated PLA profile handles 45-degree slopes and these bridges; add local support only if the first test shows sagging. This is a geometric prediction, not a sliced or physical result.

Pins are exported flat T-head on the plate, smooth shaft vertically upward. No side printing or shaft support is intended. Head identification grooves create short first-layer bridges. Start without brim; use a small 2 mm pin-only brim only if adhesion requires it. Use 0.20 mm layers, calibrated PLA and solid pins/tabs with at least four walls. The sloping thin tips need careful slicing and should not be used as pry points.

Four blank tiles retain 35.70 / 35.60 / 35.50 / 35.40 mm sizes, exact R2 corners, 2.8 mm thickness and identifying dots. No fit clearance is frozen.

## Validation and limits

The pre-export CAD and reloaded STLs were checked for collision-free horizontal joining at 81 positions over 20 mm. All eight pins seat and withdraw vertically, and resist 1 mm lateral separation. All 14 components are watertight/manifold. The plate contains all components in their recommended orientations. Updated actual-mesh sections show separated, joining, seated and pinned states. A1 support diagnostics are overhang projections rather than generated support toolpaths.

The 45-degree faces have deliberate clearance and should not be clamped or forced into a friction fit. Surface roughness, layer steps and elephant foot may still affect joining. Smooth pins remain gravity-retained and can fall out when inverted. Vertical pin layer adhesion, thin wedge tips and 2.1 mm minimum bore-edge bearing thickness require physical PLA testing. Production geometry is unchanged.

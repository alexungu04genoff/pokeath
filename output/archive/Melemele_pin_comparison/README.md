# Melemele full-size comparison board

This is a separate experiment with the miniature prototype's rigid stepped-lug mechanism. The 16 canonical production quadrants are unchanged. No physical fit results have been supplied; 5 mm shafts / 5.4 mm bores / 0.20 mm per-side clearance are provisional.

Assembled chassis: 405.28 x 285.76 x 10 mm. With T heads: 405.28 x 285.76 x 12.40 mm.

Same 38 mm pitch, 36 x 36 x 3 mm sockets, R2, 2 mm dividers, 6 mm nominal external track rim, canonical removal recess and 0.25 mm section seam gap. Lugs adapt the exterior only; no socket is split or shrunk. Existing scenery silhouette and socket positions are inherited from Melemele.

| Quadrant | Finished XYZ, mm | Maximum XY | A1 / manifold |
|---|---|---:|---|
| 1 | 146.194 x 165.182 x 10.000 | 165.182 | Pass |
| 2 | 165.211 x 146.294 x 10.000 | 165.211 | Pass |
| 3 | 203.828 x 190.898 x 10.000 | 203.828 | Pass |
| 4 | 180.661 x 203.389 x 10.000 | 203.389 | Pass |

Print the four quadrant files separately at 100% with the baked orientations. Print `three_5mm_T_pins_one_plate.stl` once for three identical pins. `Melemele_assembled_SIZE_REFERENCE_NOT_FOR_A1.stl` is for viewing the full size only: it does not fit an A1 bed as one object.

Use the prototype print instructions: body layers 0.125 mm including the first layer preserve the 0.25 mm vertical lap gap; pins can use 0.20 mm layers. Supports are required under upper lugs and horizontal pin shafts. Make lugs/pins solid. Gravity retains pins; support all sections when lifting.

Validation: all four sections are watertight, fit below 248 mm and preserve all 29 socket floors. Section solids do not intersect and inserted pins clear their paired lugs. Full-size plan compares this board with the 86 x 68 mm two-space prototype on one millimetre scale. No gameplay tiles are generated.

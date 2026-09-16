# A1 placement review

Largest finished production quadrant: **Akala Q4**. All 16 actual STL bounds were compared. These are scaled plate renders of finished meshes, not Bambu Studio screenshots.

| Item | Finished X x Y x Z (mm) | Left/right gap | Front/back gap | Scale | Additional rotation |
|---|---|---|---|---|---|
| Akala Q4 | 229.243 x 229.280 x 10.000 | 13.378 / 13.378 | 13.360 / 13.360 | 100% | 0 degrees |
| Prototype, all 14 components | 167.400 x 161.000 x 12.200 | 44.300 / 44.300 | 47.500 / 47.500 | 100% | 0 degrees |

The production STL already includes its intended 9.16 degree print rotation. Only centered XY translation is applied. Z remains socket-up and flat-base-down. No brim, loose assembled keys, purge tower or generated support footprint is included. The prototype arrangement is copied directly from its combined print STL.

## Support assessment

Production: selective supports may be needed beneath internal locking-channel roofs/cantilevers. Confirm with the physical lock coupon and slicer support preview; avoid supports in sockets or pin/rail mating surfaces. Prototype: part_A: socket up, flat underside on bed, no supports. part_B: socket up; paint accessible supports only under raised lug ears at Z=5 mm, avoid bores and sockets. pins: Flat T-head down, shaft vertical up; predicted support-free. No side printing. Optional 2 mm brim if adhesion requires.. tiles: flat underside on bed; existing top identification dots. A 2 mm pin-only brim is optional if adhesion fails and is not included here. Clean supports before assembly.

Orange diagnostic images project actual downward faces steeper than 45 degrees and above Z=0.4 mm. They identify candidate regions, including internal roofs, but do not evaluate bridging, layer paths, support access or support reach. They are not printed support geometry. Any slicer-generated support extending outside the model must be checked separately.

Both model envelopes fit the 256 x 256 mm plate. The production section has about 13.36 mm minimum edge clearance and is 18.72 mm below the 248 mm target. This is comfortable geometric fit; warping, adhesion, support removal and mechanical strength remain physically untested. No STL or canonical mechanical dimension was changed.

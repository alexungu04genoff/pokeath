# Canonical physical chassis standard

The authoritative machine-readable manifest is [chassis_standard.json](chassis_standard.json). This document is a readable mirror of that frozen standard; if the two ever differ, treat the JSON as the source to reconcile before generating files.

| Item | Frozen value |
| --- | --- |
| Target printer | Bambu Lab A1, 256 × 256 mm build area |
| Sections per board | 4 |
| Grid pitch | 38.0 mm |
| Universal socket | 36.0 × 36.0 mm rounded square |
| Socket depth | 3.0 mm |
| Socket corner radius | 2.0 mm |
| Internal divider | 2.0 mm nominal |
| Board thickness | 10.0 mm |
| Outer track rim | 6.0 mm minimum |
| Section seam | 0.25 mm |
| Top tile-removal recess | 6.0 mm wide; extends 1.0 mm into the divider; 1.2 mm deep |
| Blank fit-test tile thickness | 2.8 mm |
| Candidate tile clearances | 0.15 / 0.20 / 0.25 / 0.30 mm per side |

Every ordinary playable space uses the same rounded-square socket. Curved board outlines adapt around that socket; they do not create a special corner-tile geometry. The top removal recess is the existing common feature and preserves unrestricted tile rotation.

The frozen production outputs are under `output/CURRENT/boards/`. The production snap-key/rail dimensions remain those in `chassis_standard.json`; the experimental sloped lap-pin mechanism is deliberately excluded from this standard.

`final_tile_clearance_per_side_mm` is `null`: a tile clearance has not been selected. Pin family and pin clearance are likewise unselected. Neither may be treated as a production dimension until the physical test record selects them.


# Finished STL sizing at 40 mm pitch

All dimensions are millimetres. Measured from reloaded exported STLs at 100% scale. Print rotations are baked in; do not automatically reorient. No brim included.

| Board | Grid pitch | Nominal well | Internal divider | Minimum outer rim | Largest quadrant XY |
|---|---:|---|---:|---:|---|
| Akala | 40 | 38 x 38 | 2 | 7.396 | Q4: 245.900 x 245.899 |
| Melemele | 40 | 38 x 38 | 2 | 6.598 | Q4: 210.877 x 171.710 |
| Poni | 40 | 38 x 38 | 2 | 3.378 | Q4: 231.379 x 231.379 |
| Ulaula | 40 | 38 x 38 | 2 | 6.047 | Q4: 211.741 x 210.036 |

Outer rims follow the artwork silhouette and have variable width; the reported width is the actual minimum distance from a playing well to the external board outline. Curved corners reduce the rectangular well footprint; START banners remain flat, with no engraved text. Finish wells follow their artwork proportions.

| Board | Quadrant | Finished print STL XY | Baked rotation | Envelope with loose keys installed* |
|---|---:|---|---:|---|
| Akala | 1 | 207.860 x 211.995 | 0.00 deg | 212.078 x 217.320 |
| Akala | 2 | 210.032 x 210.020 | 48.76 deg | 210.032 x 216.632 |
| Akala | 3 | 241.008 x 241.022 | 43.36 deg | 241.008 x 254.311 |
| Akala | 4 | 245.900 x 245.899 | 7.94 deg | 256.575 x 250.758 |
| Melemele | 1 | 169.988 x 133.727 | 0.00 deg | 174.113 x 139.052 |
| Melemele | 2 | 172.110 x 133.727 | 0.00 deg | 175.998 x 139.052 |
| Melemele | 3 | 210.798 x 171.710 | 0.00 deg | 219.438 x 181.160 |
| Melemele | 4 | 210.877 x 171.710 | 0.00 deg | 216.202 x 181.160 |
| Poni | 1 | 209.414 x 212.903 | 0.00 deg | 213.608 x 218.228 |
| Poni | 2 | 210.379 x 208.473 | 0.00 deg | 210.379 x 213.798 |
| Poni | 3 | 231.336 x 231.342 | 82.80 deg | 231.336 x 237.154 |
| Poni | 4 | 231.379 x 231.379 | 71.92 deg | 242.715 x 237.024 |
| Ulaula | 1 | 210.965 x 172.858 | 0.00 deg | 215.090 x 178.183 |
| Ulaula | 2 | 185.545 x 185.558 | 26.90 deg | 191.590 x 192.209 |
| Ulaula | 3 | 210.965 x 210.036 | 0.00 deg | 220.415 x 219.486 |
| Ulaula | 4 | 211.741 x 210.036 | 0.00 deg | 217.586 x 219.486 |

*Installed keys are separate components and also span neighbouring quadrants. This assembly envelope is not the quadrant print footprint. Print three separate keys per board.

Largest finished STL axis: **245.900 mm**. Recommendation: **Keep 40 mm pitch**.

Validation: all 16 quadrants reloaded as connected, watertight meshes with consistent winding and positive volume; wells stay wholly inside their assigned quadrant and have continuous flat floors. Installed keys clear the boards and encounter the latch stop on withdrawal.

Limitations: no Bambu Studio slicing run or physical snap-fit test; support removal and latch elasticity remain untested. Existing paper-art PDFs use the earlier scale and must be regenerated for these boards.

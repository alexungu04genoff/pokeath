# Canonical chassis validation: 38 mm pitch

All dimensions are millimetres. Measured from reloaded exported STLs at 100% scale. Print rotations are baked in; do not automatically reorient. No brim included.

| Board | Grid pitch | Nominal well | Internal divider | Minimum outer rim | Largest quadrant XY |
|---|---:|---|---:|---:|---|
| Akala | 38 | 36 x 36 | 2 | 6.001 | Q4: 229.243 x 229.280 |
| Melemele | 38 | 36 x 36 | 2 | 6.001 | Q4: 200.445 x 157.227 |
| Poni | 38 | 36 x 36 | 2 | 6.001 | Q4: 220.770 x 220.750 |
| Ulaula | 38 | 36 x 36 | 2 | 6.001 | Q3: 194.878 x 195.227 |

Every grid socket is an identical rounded square: 36 x 36 mm, radius 2 mm, depth 3 mm. Base thickness 10 mm; floor Z=7 mm. Nominal divider 2 mm. A 6 mm wide, 1 mm exterior fingernail recess is 1.2 mm deep and locally leaves 1 mm of divider. It is identical at the top edge of every socket; tile rotation is unrestricted. Wide START/finish banners remain flat staging areas, not non-universal sockets. Outer track rim is rebuilt to 6 mm; preserved scenery can extend farther. The JSON includes the minimum external-rim distance for each quadrant.

| Board | Quadrant | Finished print STL XY | Baked rotation | Envelope with loose keys installed* |
|---|---:|---|---:|---|
| Akala | 1 | 194.241 x 194.878 | 0.00 deg | 198.294 x 200.203 |
| Akala | 2 | 193.187 x 193.210 | 46.10 deg | 193.187 x 199.785 |
| Akala | 3 | 226.552 x 226.525 | 41.94 deg | 226.552 x 239.624 |
| Akala | 4 | 229.243 x 229.280 | 9.16 deg | 239.942 x 234.088 |
| Melemele | 1 | 156.878 x 118.878 | 0.00 deg | 160.680 x 124.203 |
| Melemele | 2 | 156.878 x 118.878 | 0.00 deg | 160.725 x 124.203 |
| Melemele | 3 | 194.878 x 157.227 | 0.00 deg | 204.005 x 166.047 |
| Melemele | 4 | 200.445 x 157.227 | 0.00 deg | 205.770 x 166.047 |
| Poni | 1 | 194.241 x 202.371 | 0.00 deg | 198.294 x 207.696 |
| Poni | 2 | 194.878 x 194.241 | 0.00 deg | 198.293 x 199.566 |
| Poni | 3 | 219.996 x 220.012 | 82.76 deg | 219.996 x 225.805 |
| Poni | 4 | 220.770 x 220.750 | 71.90 deg | 232.488 x 226.177 |
| Ulaula | 1 | 194.878 x 164.327 | 0.00 deg | 198.709 x 169.652 |
| Ulaula | 2 | 173.878 x 173.898 | 26.48 deg | 179.753 x 180.470 |
| Ulaula | 3 | 194.878 x 195.227 | 0.00 deg | 204.034 x 204.006 |
| Ulaula | 4 | 195.079 x 195.127 | 0.06 deg | 203.832 x 203.839 |

*Installed keys are separate components and also span neighbouring quadrants. This assembly envelope is not the quadrant print footprint. Print three separate keys per board.

Largest finished STL axis: **229.280 mm**. Recommendation: **Canonical 38 mm chassis; tile clearance awaits physical fit test**.

Validation: all 16 quadrants reloaded as connected, watertight meshes with consistent winding and positive volume; wells stay wholly inside their assigned quadrant and have continuous flat floors. Installed keys clear the boards and encounter the latch stop on withdrawal.

Limitations: no Bambu Studio slicing run or physical snap-fit test; support removal and latch elasticity remain untested. Existing paper-art PDFs use the earlier scale and must be regenerated for these boards.

## Mechanical constants and checks

All quadrants: seam gap 0.25 mm; snap engagement 0.8 mm; spring tongue 1.0 mm; rail lateral clearance 0.3 mm; roof clearance above key 1.2 mm. Key length 34 mm and flange width 10.4 mm. Cavity roof Z=4.6 mm; socket floor Z=7 mm leaves 2.4 mm above the cavity. None of these mechanical dimensions is scaled.

| Board | Q | XYZ mm | Max XY | Rim min | Sockets whole | Manifold | A1 fits |
|---|---:|---|---:|---:|---|---|---|
| Akala | 1 | 194.241 x 194.878 x 10.000 | 194.878 | 6.001 | Yes | Yes | Yes |
| Akala | 2 | 193.187 x 193.210 x 10.000 | 193.210 | 6.001 | Yes | Yes | Yes |
| Akala | 3 | 226.552 x 226.525 x 10.000 | 226.552 | 6.001 | Yes | Yes | Yes |
| Akala | 4 | 229.243 x 229.280 x 10.000 | 229.280 | 6.001 | Yes | Yes | Yes |
| Melemele | 1 | 156.878 x 118.878 x 10.000 | 156.878 | 6.001 | Yes | Yes | Yes |
| Melemele | 2 | 156.878 x 118.878 x 10.000 | 156.878 | 6.001 | Yes | Yes | Yes |
| Melemele | 3 | 194.878 x 157.227 x 10.000 | 194.878 | 6.001 | Yes | Yes | Yes |
| Melemele | 4 | 200.445 x 157.227 x 10.000 | 200.445 | 6.001 | Yes | Yes | Yes |
| Poni | 1 | 194.241 x 202.371 x 10.000 | 202.371 | 6.001 | Yes | Yes | Yes |
| Poni | 2 | 194.878 x 194.241 x 10.000 | 194.878 | 6.001 | Yes | Yes | Yes |
| Poni | 3 | 219.996 x 220.012 x 10.000 | 220.012 | 6.001 | Yes | Yes | Yes |
| Poni | 4 | 220.770 x 220.750 x 10.000 | 220.770 | 6.001 | Yes | Yes | Yes |
| Ulaula | 1 | 194.878 x 164.327 x 10.000 | 194.878 | 6.001 | Yes | Yes | Yes |
| Ulaula | 2 | 173.878 x 173.898 x 10.000 | 173.898 | 6.001 | Yes | Yes | Yes |
| Ulaula | 3 | 194.878 x 195.227 x 10.000 | 195.227 | 6.001 | Yes | Yes | Yes |
| Ulaula | 4 | 195.079 x 195.127 x 10.000 | 195.127 | 6.001 | Yes | Yes | Yes |

The nominal 6 mm rim includes a 0.003 mm CAD offset compensation so tessellation and contour simplification do not undershoot the 6 mm minimum. Export removes only sub-0.0025 mm coincident/sliver vertices. Independent validation checks exported universal socket floors within 0.01 mm.

Print `fit_test/` before a full board. The four identical sockets and 0.15/0.20/0.25/0.30 mm-per-side blank tiles determine the final clearance. No clearance is frozen yet.

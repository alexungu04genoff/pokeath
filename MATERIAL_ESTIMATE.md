# Material estimate

Generated from actual exported STL mesh volumes using PLA density **1.240 g/cm³**.

## What these numbers mean

`Solid-mesh mass` is the theoretical mass if every watertight mesh volume were solid PLA. It is a useful upper bound for the model itself.

`Actual FDM print mass` cannot be calculated from STL volume alone. Perimeters, top/bottom layers, infill pattern and percentage, supports, brim, purge, modifiers and slicer compensation determine it. Use Bambu Studio’s post-slice filament estimate for the selected profile. This report deliberately does not present a guessed FDM mass.

## Production quadrants: solid-mesh upper bound

| Board | Quadrant | Volume (cm³) | Solid-mesh mass (g) |
| --- | ---: | ---: | ---: |
| Akala | 1 | 275.886 | 342.10 |
| Akala | 2 | 133.474 | 165.51 |
| Akala | 3 | 208.663 | 258.74 |
| Akala | 4 | 245.111 | 303.94 |
| Melemele | 1 | 148.179 | 183.74 |
| Melemele | 2 | 148.157 | 183.72 |
| Melemele | 3 | 230.017 | 285.22 |
| Melemele | 4 | 237.045 | 293.94 |
| Poni | 1 | 254.104 | 315.09 |
| Poni | 2 | 257.900 | 319.80 |
| Poni | 3 | 274.150 | 339.95 |
| Poni | 4 | 234.702 | 291.03 |
| Ulaula | 1 | 228.727 | 283.62 |
| Ulaula | 2 | 101.200 | 125.49 |
| Ulaula | 3 | 234.739 | 291.08 |
| Ulaula | 4 | 253.142 | 313.90 |

## Production board totals: solid-mesh upper bound

| Board | Quadrants | Volume (cm³) | Solid-mesh mass (g) |
| --- | ---: | ---: | ---: |
| Akala | 4 | 863.135 | 1070.29 |
| Melemele | 4 | 763.398 | 946.61 |
| Poni | 4 | 1020.856 | 1265.86 |
| Ulaula | 4 | 817.808 | 1014.08 |
| **All four chassis** | **16** | **3465.197** | **4296.84** |

The four-board chassis solid-volume upper bound represents **4.297 standard 1 kg PLA rolls**; purchasing requires whole rolls, so round up to **5 roll(s)** before allowance for slicing waste, supports, brims, retries or accessories.

## Sloped 2×1 prototype kit: solid-mesh upper bound

The combined one-plate STL is excluded here because it duplicates the individual parts.

| Component type | Count | Volume (cm³) | Solid-mesh mass (g) |
| --- | ---: | ---: | ---: |
| board part | 2 | 35.002 | 43.40 |
| pin | 8 | 3.034 | 3.76 |
| tile test | 4 | 14.115 | 17.50 |
| **Prototype kit total** | **14** | **52.151** | **64.67** |

## Re-running

Run `python estimate_material.py` for the default 1.240 g/cm³ PLA density. Use `python estimate_material.py --density 1.27` for another material density. The script only reads STL files and writes this report plus `material_estimate.csv`; it never regenerates geometry.

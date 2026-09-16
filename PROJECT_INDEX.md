# Project directory and generator index

## Canonical production path

| Path | Purpose |
| --- | --- |
| `chassis_standard.json` | Single machine-readable frozen chassis manifest. |
| `build_canonical_chassis.py` | Generates the four-board canonical chassis, fit coupon and production previews. It rewrites outputs. |
| `validate_canonical_chassis.py` | Independent canonical mesh/socket/rim validator. It also rewrites validation previews and the print-kit zip. |
| `output/canonical_chassis/` | Current production candidate: 16 quadrant STLs, blank tile fit test, finished bounds and sizing report. |
| `output/canonical_chassis/finished_stl_bounds.json` | Exported STL dimensions, rotations, socket locations and mechanical checks. |
| `output/canonical_chassis/SIZING_REPORT.md` | Readable per-board and per-quadrant sizing report. |

## Current physical experiment

| Path | Purpose |
| --- | --- |
| `build_sloped_lap_prototype.py` | Generates the experimental 2×1 sloped lap-pin test, previews and reports. It rewrites its output folder. |
| `output/sloped_lap_prototype/` | Current test kit: A/B bodies, 4 mm and 5 mm pin variants, four blank tiles, visual checks and A1 placement previews. |
| `build_one_plate_test.py` | Packs an existing prototype folder’s fourteen components into a single A1 plate STL; rewrites that prototype’s combined STL and report. |
| `render_a1_placement.py` | Creates simulated A1 plate placement and overhang previews from finished STLs; rewrites placement-preview files. |

## Analysis and legacy material

| Path | Purpose |
| --- | --- |
| `analyse_board_sizes.py` | Board-layout and grid-size analysis used by chassis generators. |
| `build_printable_board.py` | Earlier smooth-board generator and shared CAD helpers. |
| `build_final_sizing.py` / `output/final_sizing_40mm/` | Superseded 40 mm sizing exploration. |
| `build_pin_joint_prototype.py` / `output/pin_joint_prototype/` | Superseded large outboard pin-lug prototype. |
| `build_recessed_pin_prototype.py` / `output/recessed_pin_prototype/` | Superseded fully recessed pin experiment. |
| `build_compact_lap_prototype.py` / `output/compact_lap_prototype/` | Superseded flat compact lap-tab experiment. |
| `build_melemele_pin_comparison.py` / `output/Melemele_pin_comparison/` | Size-reference comparison, not a production A1 print set. |
| `output/layered/`, `output/sculpted/`, `output/paper_art/` | Earlier artwork/relief/paper workflows at earlier physical standards. |
| `build_print_kit.py` | Earlier print-kit builder for the old board workflow. |

All `build_*.py` files are generators and may change output artifacts. Use their corresponding validation JSON, reports and previews for read-only inspection. Do not treat legacy output folders as interchangeable with the canonical chassis.


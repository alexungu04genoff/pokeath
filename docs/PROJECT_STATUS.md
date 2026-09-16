# Pokémon Athletes physical-board status

The production chassis is frozen at the universal standard documented in [CANONICAL_STANDARD.md](CANONICAL_STANDARD.md). The current production candidate is `output/CURRENT/boards/`: four boards, each split into four printable sections.

The sloped 2×1 lap-pin assembly in `output/CURRENT/prototype/sloped_lap_2x1/` is an experiment only. It must **not** be copied into the sixteen production quadrants until it passes the physical PLA test in [NEXT_PHYSICAL_TEST.md](NEXT_PHYSICAL_TEST.md).

Tile fit is also unselected. The four blank tile variants test 0.15, 0.20, 0.25, and 0.30 mm clearance per side. Do not create normal, special-effect, or custom tile libraries until a clearance is selected from the physical test.

Pin selection is unselected. The prototype provides 4 mm and 5 mm nominal families, each with the same four clearance variants. Do not apply either family or clearance to production boards until it is selected from the physical test.

The older `output/final_sizing_40mm/`, `output/pin_joint_prototype/`, `output/recessed_pin_prototype/`, `output/compact_lap_prototype/`, and artwork/relief folders are historical explorations. They are retained for reference and are not the current chassis or locking recommendation.

The 16 finished production quadrant STLs remain the files in `output/CURRENT/boards/{Akala,Melemele,Poni,Ulaula}/quadrant_*.stl`. The largest is Akala Q4 at 229.243 × 229.280 × 10.000 mm, within the 256 × 256 mm A1 build plate and the 248 mm design target.


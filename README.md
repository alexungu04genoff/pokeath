# Pokémon Athletes physical-board project

Use the current assets below. If a task does not explicitly request a historical prototype, always use **`output/CURRENT/`** and the current generators.

1. Want the current printable boards? → [`output/CURRENT/boards/`](output/CURRENT/boards/)
2. Want the current physical lock prototype? → [`output/CURRENT/prototype/`](output/CURRENT/prototype/)
3. Want to experiment in Blender? → [`output/CURRENT/blender/`](output/CURRENT/blender/). Start with `START_HERE.obj`; board quadrants are in `boards/<board>/`.
4. Want old experiments? → [`output/archive/`](output/archive/)

The production chassis is frozen at 38 mm pitch, 36 × 36 mm universal sockets, 3 mm socket depth, R2 socket corners, 2 mm dividers, 10 mm total thickness, and a 6 mm track rim. The sloped 2×1 lap-pin prototype is experimental and must not be propagated to production boards until physical testing approves it.

## Project layout

- `assets/` — original board and racer reference images.
- `src/chassis/` — current canonical chassis generator and validator.
- `src/prototypes/` — physical prototype generators; only the sloped-lap output is current.
- `src/blender/` — Blender sandbox export utility.
- `src/tools/` — material, placement, and rendering utilities.
- `src/legacy/` — generators retained solely for archived workflows.
- `docs/` — current engineering, testing, material, and print-planning documentation.

Run modules from the repository root, for example `python -m src.chassis.validate_canonical_chassis`. Generated STL, PNG, PDF, ZIP, and OBJ assets remain ignored according to the repository policy.

# Current Blender exports

Start with `START_HERE.obj` to inspect the assembled sloped-lap prototype in its shared coordinates.

- `boards/<board>/quadrant_*.obj` — current canonical production quadrants, ready to import directly into Blender.
- `tiles/` — nominal and clearance-test universal tile references.
- `pins/` — representative 4 mm and 5 mm experimental T-pins.
- `experimental_parts/` — editable prototype halves, mating lugs, and generic chassis samples.

All files use millimetres and have their print-bottom surface at Z=0. `START_HERE.obj` is the only deliberately multi-part reference mesh; all other assets remain separate editing objects. The sloped lap mechanism is experimental and is not part of the canonical production quadrants.

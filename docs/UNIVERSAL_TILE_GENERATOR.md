# Universal gameplay-tile generator

This generator creates removable tiles for the canonical **36 × 36 mm**, R2, 3 mm-deep sockets. It does not choose the physical clearance. Keep testing the four candidates before setting a production value.

## Generate test tiles

Run from the repository root:

```powershell
python -m src.tiles.generate_tiles --clearance 0.15 --clearance 0.20 --clearance 0.25 --clearance 0.30
python -m src.tiles.validate_tiles
```

The examples are written to `output/CURRENT/tiles/examples/`. They are blank/custom category references only, not a game tile library.

## Safe parameters

- `--clearance`: per-side fit clearance in millimetres. Use any test value; 0.15, 0.20, 0.25, and 0.30 mm are the present candidates. No value is frozen.
- `--category`: `normal`, `special`, `hidden-special`, or `blank-custom`. This controls metadata and output names only.
- `--recessed-icon-area`: adds a 0.45 mm-deep generic top icon field.
- `--embossed-icon-area`: adds a 0.45 mm-high generic top icon field. It cannot be combined with the recessed field.
- `--engraved-text TEXT` and `--engraved-icon circle|star`: add 0.35 mm top engravings.
- `--hidden-special-back-marker`: adds the same 0.30 mm underside dot marker to any requested hidden-special test tile.
- `--label`: changes only the output filename prefix.

## Compatibility surfaces

Do not change these in the generator without a new canonical chassis decision: 36 mm socket basis, 2 mm corner radius, 2.8 mm base thickness, tile socket-wall interface, or the socket floor relationship. Optional top features may change total tile height and should be checked against playing-piece clearance.

The validator reloads each STL and checks its computed width for the requested clearance, manifoldness, positive volume, Z=0 print base, and compatibility with the 256 × 256 mm A1 plate. It intentionally reports `clearance_selected: false`.

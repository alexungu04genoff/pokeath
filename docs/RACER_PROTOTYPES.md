# Racer-piece sandbox

`output/CURRENT/racers/` provides neutral 8 × 8, 9 × 9, and 10 × 10 mm bases, an 8 mm base with a small upright portrait panel, and a 36 mm socket crowding scene containing six 8 mm dummy racers arranged:

```text
[1][2][3]
[4][5][6]
```

The matching OBJ files are in `output/CURRENT/blender/racers/` for quick Blender inspection. These are sizing aids only: no Pokémon artwork, character identity, or final racer standard has been selected.

```powershell
python -m src.racers.generate_racer_prototypes
python -m src.racers.validate_racer_prototypes
```

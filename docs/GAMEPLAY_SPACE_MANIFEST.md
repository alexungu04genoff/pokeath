# Gameplay-space manifest

`output/CURRENT/gameplay_spaces/` contains one JSON manifest per board and `all_boards.json` for the complete set. It maps each canonical socket to its row, column, quadrant ownership, and only gameplay information that existing project data supports.

The original reference images are visual sources, but this repository does not contain reliable machine-readable color sampling or complete effect text for every board. Those fields are therefore explicitly `null`/unknown instead of guessed.

Only Ulaula has an existing ordinary/special mapping in `src/chassis/build_printable_board.py` through `EFFECT_IDS`. Those spaces are marked `special` with generic identifier `effect`; no original effect text is encoded. The other boards retain `ordinary_or_special: "unknown"` until source-backed gameplay data is supplied.

Regenerate and validate from the repository root:

```powershell
python -m src.tools.build_gameplay_space_manifest
python -m src.tools.validate_gameplay_space_manifest
```

Neither command loads, exports, or changes CAD geometry.

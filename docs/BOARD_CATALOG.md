# Board developer catalog

Open `output/CURRENT/catalog/index.html` in a browser. Each static map overlays canonical socket IDs, quadrant ownership, special/ordinary status where source-backed, and canonical assembly coordinates in hover tooltips over the original board artwork.

The original artwork remains the visual color reference. The machine-readable gameplay manifest deliberately keeps per-socket color unknown until reliable source data is supplied.

Regenerate with:

```powershell
python -m src.tools.build_board_catalog
```

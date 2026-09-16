"""Create static HTML debug maps over original board reference artwork."""
from __future__ import annotations

import html
import json
from pathlib import Path

from src.chassis import analyse_board_sizes as study
from src.chassis.build_canonical_chassis import CONFIGS

ROOT = Path(__file__).resolve().parents[2]
MANIFESTS = ROOT / "output" / "CURRENT" / "gameplay_spaces"
OUT = ROOT / "output" / "CURRENT" / "catalog"


def board_html(manifest: dict[str, object]) -> str:
    name = manifest["board"]
    config = CONFIGS[name]
    image = next(item[1] for item in study.BOARDS if item[0] == name)
    overlays = []
    for space in manifest["spaces"]:
        row, column = space["row"], space["column"]
        x = config["origin"][0] + (column + .5) * study.PITCH
        y = config["origin"][1] + (row + .5) * study.PITCH
        kind = space["ordinary_or_special"]
        color = {"special": "#ed4d35", "ordinary": "#48b06a", "unknown": "#e9bd38"}[kind]
        title = f"{space['canonical_socket_id']} | Q{space['quadrant_ownership']} | {kind} | canonical {space['assembly_center_mm']} mm"
        overlays.append(f'<g><rect x="{x-55:.1f}" y="{y-55:.1f}" width="110" height="110" rx="8" class="socket" stroke="{color}"/><text x="{x:.1f}" y="{y+5:.1f}">{space["canonical_socket_id"]}</text><title>{html.escape(title)}</title></g>')
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>{name} catalog</title><style>
body{{font-family:system-ui;margin:20px;background:#182027;color:#eef3f5}}svg{{max-width:100%;height:auto;background:#fff}}.socket{{fill:rgba(255,255,255,.08);stroke-width:5}}text{{font-size:24px;font-weight:700;fill:#111;text-anchor:middle;paint-order:stroke;stroke:#fff;stroke-width:5px;stroke-linejoin:round}}.legend span{{margin-right:18px}}.special{{color:#ed4d35}}.ordinary{{color:#48b06a}}.unknown{{color:#e9bd38}}</style></head><body>
<h1>{name} developer catalog</h1><p>Socket labels and quadrant ownership are canonical. The image is the original reference artwork; color is visual-only because reliable per-socket color metadata is not encoded.</p>
<p class="legend"><span class="ordinary">green: source-backed ordinary</span><span class="special">red: source-backed special</span><span class="unknown">gold: classification unknown</span></p>
<svg viewBox="0 0 1614 1536" role="img"><image href="../../../{image}" x="0" y="0" width="1614" height="1536"/>{''.join(overlays)}</svg>
</body></html>'''


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    links = []
    for name in ("Akala", "Melemele", "Poni", "Ulaula"):
        manifest = json.loads((MANIFESTS / f"{name}.json").read_text())
        filename = f"{name}.html"
        (OUT / filename).write_text(board_html(manifest), encoding="utf-8")
        links.append(f'<li><a href="{filename}">{name}</a> — {len(manifest["spaces"])} canonical sockets</li>')
    (OUT / "index.html").write_text("<!doctype html><meta charset=utf-8><title>Board catalog</title><h1>Pokémon Athletes board catalog</h1><p>Static debug maps generated from canonical socket manifests.</p><ul>" + "".join(links) + "</ul>", encoding="utf-8")
    print("PASS: generated four board catalog HTML maps.")


if __name__ == "__main__":
    main()

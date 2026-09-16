"""Build a source-grounded gameplay-space manifest without changing CAD."""
from __future__ import annotations

import json
from pathlib import Path

from src.chassis.build_canonical_chassis import CONFIGS
from src.chassis.build_printable_board import EFFECT_IDS

ROOT = Path(__file__).resolve().parents[2]
BOARDS = ROOT / "output" / "CURRENT" / "boards"
OUT = ROOT / "output" / "CURRENT" / "gameplay_spaces"


def source_classification(board: str, row: int, column: int, config: dict[str, object]) -> tuple[str, str | None, str | None, str]:
    """Return only classifications encoded by existing project source data."""
    if board != "Ulaula":
        return "unknown", None, None, "No ordinary/special mapping is encoded for this board."
    sequence = 0
    for candidate_row, columns in config["rows"].items():
        for candidate_column in columns:
            sequence += 1
            if candidate_row == row and candidate_column == column:
                if sequence in EFFECT_IDS:
                    return "special", "effect", None, "Existing EFFECT_IDS source mapping; effect text is not encoded."
                return "ordinary", None, None, "Existing Ulaula placement mapping; no effect identifier."
    raise AssertionError(f"Missing Ulaula socket R{row}C{column}")


def ownership(bounds: dict[str, object]) -> tuple[dict[str, int], dict[str, list[float]]]:
    owners: dict[str, int] = {}
    centers: dict[str, list[float]] = {}
    for quadrant in bounds["quadrants"]:
        for socket_id, center in zip(quadrant["socket_ids"], quadrant["socket_centers_assembly_mm"]):
            if socket_id in owners:
                raise ValueError(f"Canonical socket appears in more than one quadrant: {socket_id}")
            owners[socket_id] = quadrant["quadrant"]
            centers[socket_id] = center
    return owners, centers


def build_board(board: dict[str, object]) -> dict[str, object]:
    name = board["board"]
    config = CONFIGS[name]
    owners, centers = ownership(board)
    spaces = []
    for row, columns in config["rows"].items():
        for column in columns:
            socket_id = f"R{row}C{column}"
            classification, effect_id, effect_text, classification_note = source_classification(name, row, column, config)
            spaces.append({
                "board": name,
                "canonical_socket_id": socket_id,
                "row": row,
                "column": column,
                "original_visual_color": None,
                "original_visual_color_status": "unknown_not_encoded_in_machine_readable_project_data",
                "ordinary_or_special": classification,
                "classification_status": classification_note,
                "original_effect_identifier": effect_id,
                "original_effect_text": effect_text,
                "effect_status": "unknown_not_encoded" if classification != "special" else "generic_effect_only_no_text_encoded",
                "quadrant_ownership": owners[socket_id],
                "assembly_center_mm": centers[socket_id],
            })
    canonical = set(owners)
    recorded = {space["canonical_socket_id"] for space in spaces}
    if canonical != recorded:
        raise ValueError(f"{name}: source layout and canonical sockets differ: missing={canonical-recorded}, extra={recorded-canonical}")
    return {
        "board": name,
        "schema_version": 1,
        "source_notes": [
            "Canonical IDs, quadrant ownership, and centers come from output/CURRENT/boards/finished_stl_bounds.json.",
            "Original visual colors are not encoded as reliable machine-readable gameplay data; values remain explicitly unknown.",
            "Only Ulaula ordinary/special classification is encoded by existing EFFECT_IDS source data. No effect text is encoded.",
        ],
        "spaces": spaces,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bounds = json.loads((BOARDS / "finished_stl_bounds.json").read_text())
    manifests = [build_board(board) for board in bounds["boards"]]
    for manifest in manifests:
        (OUT / f"{manifest['board']}.json").write_text(json.dumps(manifest, indent=2) + "\n")
    combined = {"schema_version": 1, "generated_from": "canonical socket ownership and existing project source data",
                "invented_gameplay_data": False, "boards": manifests}
    (OUT / "all_boards.json").write_text(json.dumps(combined, indent=2) + "\n")
    print(f"PASS: wrote {len(manifests)} board manifests with {sum(len(item['spaces']) for item in manifests)} canonical sockets.")


if __name__ == "__main__":
    main()

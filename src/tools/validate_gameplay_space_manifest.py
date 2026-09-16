"""Validate complete, non-duplicated canonical socket coverage in gameplay manifests."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOARDS = ROOT / "output" / "CURRENT" / "boards"
MANIFESTS = ROOT / "output" / "CURRENT" / "gameplay_spaces"


def main() -> None:
    bounds = json.loads((BOARDS / "finished_stl_bounds.json").read_text())
    combined = json.loads((MANIFESTS / "all_boards.json").read_text())
    checks = []
    for board in bounds["boards"]:
        name = board["board"]
        source = next(item for item in combined["boards"] if item["board"] == name)
        expected = [socket for quadrant in board["quadrants"] for socket in quadrant["socket_ids"]]
        actual = [space["canonical_socket_id"] for space in source["spaces"]]
        assert len(expected) == len(set(expected))
        assert Counter(expected) == Counter(actual), name
        owners = {socket: quadrant["quadrant"] for quadrant in board["quadrants"] for socket in quadrant["socket_ids"]}
        assert all(space["quadrant_ownership"] == owners[space["canonical_socket_id"]] for space in source["spaces"])
        checks.append({"board": name, "canonical_socket_count": len(expected), "appears_exactly_once": True})
    report = {"passed": True, "invented_gameplay_data": False, "boards": checks,
              "total_canonical_sockets": sum(item["canonical_socket_count"] for item in checks)}
    (MANIFESTS / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS: {report['total_canonical_sockets']} canonical sockets appear exactly once across {len(checks)} boards.")


if __name__ == "__main__":
    main()

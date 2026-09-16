"""Continuous rigid translation checks for the Ulaula experiment only.

A translated solid sweeps its initial volume plus prisms swept by leading
boundary triangles. Intersecting these prisms tests the entire segment, not
sampled poses. Prism intersections may overlap: their sum is a conservative
upper bound, never presented as the volume of one physical collision.
"""
from itertools import permutations
import numpy as np
import trimesh
import manifold3d as manifold

VOLUME_TOLERANCE = .001  # mm3, aggregate conservative overlap bound
DIRECTIONS = [(x, y, 0) for x, y in [(1,0),(-1,0),(0,1),(0,-1),
                                     (1,1),(1,-1),(-1,1),(-1,-1)]]


def solid(mesh):
    result = manifold.Manifold(manifold.Mesh64(np.asarray(mesh.vertices, dtype=np.float64),
                                              np.asarray(mesh.faces, dtype=np.uint64)))
    assert result.status() == manifold.Error.NoError
    return result


def swept_collision(moving, fixed, displacement):
    """Sweep from seated outward; reverse is the same insertion path."""
    displacement = np.asarray(displacement, dtype=float)
    start_bounds = moving.bounds + displacement
    assert np.any(start_bounds[1] < fixed.bounds[0]) or np.any(start_bounds[0] > fixed.bounds[1]), "Start must be fully separated"
    obstacle = solid(fixed)
    initial = abs((solid(moving) ^ obstacle).volume())
    if initial > VOLUME_TOLERANCE:
        return {"passed": False, "collision_lower_bound_mm3": initial, "reason": "seated overlap"}
    total = initial
    faces = moving.triangles[moving.face_normals @ displacement > 1e-9]
    low = np.minimum(faces.min(axis=1), (faces + displacement).min(axis=1))
    high = np.maximum(faces.max(axis=1), (faces + displacement).max(axis=1))
    mask = np.all(high >= fixed.bounds[0], axis=1) & np.all(low <= fixed.bounds[1], axis=1)
    count = 0
    for triangle in faces[mask]:
        prism = manifold.Manifold.hull_points(np.vstack([triangle, triangle + displacement]))
        assert prism.status() == manifold.Error.NoError
        overlap = prism ^ obstacle
        assert overlap.status() == manifold.Error.NoError
        total += abs(overlap.volume())
        assert np.isfinite(total)
        count += 1
        if total > VOLUME_TOLERANCE:
            return {"passed": False, "overlap_bound_mm3": total, "prisms_checked": count,
                    "reason": "continuous swept boundary intersects installed part"}
    return {"passed": True, "overlap_bound_mm3": total, "prisms_checked": count}


def enumerate_orders(parts):
    # 600 mm exceeds the assembled XY diagonal; the initial part is fully free.
    distance = 600.
    cache = {}
    sequences = []
    for order in permutations(range(4)):
        steps = []
        for position, moving in enumerate(order[1:], 1):
            installed = order[:position]
            candidates = []
            for direction in DIRECTIONS:
                vector = np.asarray(direction, dtype=float)
                vector *= distance / np.linalg.norm(vector)
                checks = []
                for fixed in installed:
                    key = (moving, fixed, direction)
                    if key not in cache:
                        cache[key] = swept_collision(parts[moving], parts[fixed], vector)
                    checks.append({"installed_quadrant": fixed+1, **cache[key]})
                candidates.append({"outward_unit_vector": (vector/distance).tolist(),
                                   "start_offset_mm": vector.tolist(), "checks": checks,
                                   "passed": all(c["passed"] for c in checks)})
            steps.append({"quadrant": moving+1, "installed": [i+1 for i in installed],
                          "candidates": candidates, "passed": any(c["passed"] for c in candidates)})
        sequences.append({"order": [i+1 for i in order], "steps": steps,
                          "passed": all(s["passed"] for s in steps)})
        print("Assembly order", sequences[-1]["order"], sequences[-1]["passed"], flush=True)
    return sequences

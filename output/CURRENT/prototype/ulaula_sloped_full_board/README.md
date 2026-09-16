# DIGITALLY VALIDATED EXPERIMENT / PHYSICAL TEST STILL REQUIRED

Ulaula only. Production boards and the existing 2×1 experiment are byte-for-byte unchanged. No gameplay tiles were generated.

## Original collision diagnosis

The original builder unioned complementary wedges into intact 10 mm chassis material. Unlike the 2×1 builder, it omitted the local chassis relief. Neither wedge/wedge nor chassis/chassis intersections contribute any seated volume. Every reported collision is one wedge penetrating the opposite quadrant's chassis, including its inward/root region. The independently measured component volumes below include the actual bore subtraction.

At the right edge the old tangent points toward -Y, reversing which owner receives the full-height end of each wedge. This explains its much larger overlap. The two old profiles also came from opposite prototype edges, so their root projections were mirrored rather than sharing one consistently inward-oriented footprint. These are transplant errors, not boolean noise or a collision with a distant lock.

| Joint | Before mm³ | After mm³ | Exact old material intersections |
|---|---:|---:|---|
| [1, 3] | 93.119095 | 0.000000000 | Q1 wedge into Q3 chassis: 41.794044 mm³; Q3 wedge into Q1 chassis: 51.325019 mm³ |
| [2, 4] | 447.381403 | 0.000000000 | Q2 wedge into Q4 chassis: 331.653354 mm³; Q4 wedge into Q2 chassis: 115.728096 mm³ |
| [3, 4] | 93.205329 | 0.000000000 | Q3 wedge into Q4 chassis: 41.888643 mm³; Q4 wedge into Q3 chassis: 51.316686 mm³ |

Exact assembly-space bounding boxes are in original_collision_diagnosis.json. old_collision_debug.png colors the two contributing regions separately; old_collision_q*_q*.stl preserves the original intersection solids.

## Local correction

Use one common profile with its reinforced root pointing inward and its slope coordinate pointing from the first owner to the second. Within a 0.25 mm buffered joint mask, partition chassis plus lug with the complementary 45° half-spaces. Their planes remain z=4.8-u and z=5.2-u, giving 0.4 mm vertical clearance. Move each pin center 2 mm outward to keep the entire relief clear of sockets and fingernail recesses; local outward projection is 7 mm. No board scaling or gameplay dimensions change. Set-difference checks prove that material outside those local masks is identical to the frozen chassis rebuild.

## Four-piece assembly

All 24 original orders are impossible because their required final state already contains interference. Changing validation direction cannot fix that. The old validator's 8 mm direction follows the edge inward vector, not the wedge's slope coordinate, and cannot establish sequential assembly.

The corrected exported STLs have 8 certified orders among all 24 tested. Use **Q1 → Q3 → Q4 → Q2**, with all pins removed:

Q3 enters from below (-Y insertion), Q4 from the right (-X insertion), and Q2 from above (+Y insertion). Adding Q4 last in Q1-Q2-Q3-Q4 fails all eight tested directions: Q2 obstructs the rightward withdrawal, Q3 obstructs the downward withdrawal, and the diagonals also collide. Leaving Q2 until last removes that constraint.

- Add Q3 from XY offset [0.0, 600.0] mm; translate toward its seated position in direction [-0.0, -1.0], against every already-installed quadrant.
- Add Q4 from XY offset [600.0, 0.0] mm; translate toward its seated position in direction [-1.0, -0.0], against every already-installed quadrant.
- Add Q2 from XY offset [0.0, -600.0] mm; translate toward its seated position in direction [-0.0, 1.0], against every already-installed quadrant.

Then lower all three smooth 4 mm pins vertically. Their 4.4 mm bore axes coincide only at zero relative planar displacement; clearance permits small play and does not imply an infinitely precise seating detector. Vertical insertion and withdrawal over 15 mm are continuously checked against all four bodies. See assembly_order.png and assembly_search.json for diagrams and every candidate's results.

## Validation and numerical limits

Motion checks cover the complete translation, not isolated samples: the initial solid plus every leading boundary triangle's swept prism contains the swept solid. Each prism is intersected with each obstacle. The sum of intersection volumes is a conservative bound because prisms can overlap. A bound at most 0.001 mm³ is accepted as boolean/tessellation noise; meaningful interference fails. Start offsets are 600 mm, beyond the complete assembly's XY diagonal, so incoming quadrants start fully separated. Reversing the certified outward sweep yields the insertion path. Eight cardinal/diagonal directions are tested at every step of every ordering. A failed direction is not a proof against arbitrary curved paths.

All six seated quadrant pairs pass, not just the three locks. The shared exporter's 2.5 micron edge-collapse cleanup opened these meshes during development; this experiment directly exports float32 STL and verifies topology instead of welding vertices. All four reloaded float32 STL quadrants are watertight, consistently wound, single solids with two incident faces per edge. Gameplay/socket/recess masks are disjoint from the local changes. Frozen hashes cover every production-board file, every existing 2×1 file, and its builder source.

| Quadrant | A1 placement X × Y × Z mm | Below 248 mm |
|---|---|---|
| Q1 | 201.285 × 175.961 × 10.000 | Yes |
| Q2 | 182.385 × 182.416 × 10.000 | Yes |
| Q3 | 206.634 × 206.606 × 10.000 | Yes |
| Q4 | 206.413 × 206.434 × 10.000 | Yes |

## Print and physical limits

Flat base down, sockets up. 45 degree ramps; local 4.4 mm bore bridges require slicer/physical inspection with 0.4 mm nozzle. Pins flat head down. No sliced or physical support certification.

The 45° half-space construction preserves the approved-for-testing mechanical principle. Rigid PLA, no springs, snap tabs or flexing features. Slopes, thin tips, bore bridges, pin fit and wear still require slicing and physical testing. Smooth pins are gravity-retained and can fall out when inverted. This is not production-approved; Akala, Melemele and Poni are unchanged.

Reproduce from repository root: `python -m src.prototypes.build_ulaula_sloped_full_board` with requirements-cad.txt. Generated STL/OBJ/PNG assets follow the repository's ignore policy; reports and generators are versioned.

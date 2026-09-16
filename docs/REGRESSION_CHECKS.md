# Regression checks and CI

GitHub Actions runs `python -m src.tools.run_regression_checks` on every push and pull request. The check rebuilds canonical manufacturing outputs in CI, then verifies:

- all 16 canonical quadrants are watertight/manifold and fit the 256 mm A1 plate;
- each production quadrant retains 36 × 36 mm sockets and 10 mm chassis thickness;
- generated production hashes match the frozen baseline;
- canonical validators, manifests, racer sandbox, and catalog work;
- selected current modules import successfully; and
- generated `output/CURRENT/` metadata does not reference archive paths.

Run the same command locally from the repository root. A hash mismatch is intentional only when a reviewed production chassis geometry change also updates its baseline.

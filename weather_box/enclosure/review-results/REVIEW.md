# Revision 4 review — November 7, 2026

**Disposition: ready to submit for a first-fit print.** Both revision 3 findings are fixed and verified. Physical fit has not been tested, and this was not signed off by an independent human engineer. The revision 3 review is kept in `revision-3/`.

## Revision 3 findings: resolved

| Finding | Fix | Evidence |
|---|---|---|
| P1: screen fence blocked both left M3 nut seats (0.678 mm³ overlap) | Nut and screw cavities are cut from the complete shell after all fences are added | A standard 5.5 mm AF x 2.4 mm nut, and a 30 mm insertion sweep above it, overlap the exported shell by 0.0 mm³ at all four corners. The coupon now reproduces the real corner and fence, and also shows 0.0 |
| P2: no hard stop against USB insertion force | Two corner stops at the ribbon end, 0.4 mm nominal clearance, leaving a 20.8 mm central opening | PCB shifted 0 and 0.3 mm toward the ribbon: no collision. At 0.5 mm and beyond it collides with the stops, so travel is limited to about 0.4 mm |

## Checks completed (all against the exported STLs)

- Reimported all four files: watertight, consistent winding, one connected solid each, minimum Z=0, expected extents. SHA-256 values match between `validation.json`, `independent-checks.json` and `slicer-checks.json`.
- M3 screw shanks clear all three assembled parts. The three parts do not overlap each other or the measured component envelopes.
- Sliced with PrusaSlicer 2.9.7 (generic 150 mm bed, PLA, 0.4 nozzle, 0.2 mm layers, 3 perimeters, 5 top/bottom layers, 20% gyroid, no supports, brim or raft). All four slice with no errors or warnings. Every layer has extrusion, Z increases, and all extrusion is inside the bed. Layers: shell 165, carrier 131, back 15, coupon 34.
- Generic estimates, not the library's quote: shell 50.6 g (4h18m), carrier 26.1 g (3h31m), back 29.9 g (3h35m), coupon 7.2 g (50m). The three case parts total 106.6 g, about $6.40 at $0.06/g.
- New this pass: plastic around each nut pocket is 0.50 mm at the two left corners (the screen pocket sits close) and 0.91 mm at the two right corners. The slicer prints the 0.5 mm wall on every layer from z=4.0 to 6.8 (one perimeter line), so it is not dropped.

## Remaining risks (physical, not proven problems)

- **Left nut walls are thin (0.5 mm).** Insert nuts by dropping them in; do not press or hammer them. Do not overtighten. If one cracks, the coupon shows the same corner.
- **Thread engagement is only 1.9 mm nominal.** Tighten until snug only. Dry-assemble first.
- The model omits the real battery socket and plug, FPC connector and latch, switch, buttons, cable shapes and strap overlap. The 20.8 mm connector opening between the new stops is an assumption: check the connector and latch clear them before seating the board.
- Pin positions under the board were not measured. USB access is a nominal 35 x 14 x 8 mm space, not your measured cable housing.
- The active image position is assumed centered. Use `screen-fit-template.pdf` before taping the screen.
- Magnet holding force and strap tension need real-world checks. Test over a padded surface before leaving it on the fridge.
- The library's own slicer profile, and whether Holladay's printer has a bed the size you need, are not checked. All parts fit both the 150 mm and 220 mm printers listed.
- Printed PLA warms and creeps: do not leave the case in a hot car or in direct sun.

## Reproduce

`make_case.py` regenerates the STLs. `review-results/check_exported_geometry.py` and `slice_review.py` rerun the checks (the slicer needs PrusaSlicer 2.9.7 under ignored `.venv/review-tools/`). Generic G-code stays in `.venv/review-tools/` and is NOT for the library's printer.

PrusaSlicer 2.9.7 official release, DMG SHA-256 f735f9d527823d159d9ac1e8f84ce1b74ea571e705e70e723bee546d070db60b: https://github.com/prusa3d/PrusaSlicer/releases/tag/version_2.9.7

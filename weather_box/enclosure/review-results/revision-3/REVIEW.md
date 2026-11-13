# Revision 3 second-pass review — November 7, 2026

**Disposition: changes requested. Do not submit the revision 3 enclosure for printing yet.**

This is a second pass by the same assistant using separate checks against exported STLs, not an independent human engineering sign-off. No geometry, STL, review.html, assembly instruction or packaged ZIP was changed during review.

## Findings

### P1 — Screen fence obstructs both left-hand M3 nut seats

Source: `make_case.py:29–36`.

The nut cavity is subtracted from each individual boss before that boss is unioned with the existing shell and screen fence. The fence therefore remains inside part of the nut cavity. Independent Boolean tests against the exported shell, using a standard 5.5 mm-across-flats × 2.4 mm-high M3 hex nut at its specified seated position, find **0.678254 mm³** overlap at (6,6) and **0.678256 mm³** at (6,76). The right-hand seats are clear. The obstructing fence reaches z=4.6 while the nominal nut starts at z=4.0.

Consequence: the left nuts cannot occupy their intended position without removing plastic. A nut resting on the obstruction sits too high and may prevent the carrier seating correctly. Tightening harder is not an acceptable remedy.

Correction: subtract the nut wells and screw pilot clearances from the complete shell AFTER all fences/bosses are unioned. Recheck remaining wall thickness and screen clearance, then test both the seated nut and its top-down insertion path at all four positions.

The optional coupon passes the same nut test because it lacks this fence. Extend the coupon or use a corner section that reproduces the surrounding shell geometry. Existing whole-part mesh tests do not include nuts, explaining why they passed.

### P2 — Board has no hard restraint against USB insertion force

Source: `make_case.py:53–57`; assembly instruction 13.

The board has side guides and end stops only at x=54.6, its USB end. Inserting a plug into the inward-facing socket pushes the board toward -X, away from those end stops and toward the screen ribbon. The strap crosses the board in the Y direction, so longitudinal retention depends on friction.

Independent swept-position tests of the PCB show 0, 1, 2, 3 and 4 mm movement toward the ribbon produces no meaningful collision with the carrier (only about 0.000002 mm³ numerical surface noise). This proves there is no geometric stop over that travel; it does NOT prove how much the actual strap will slip under a particular plug force.

Consequence: a loose or relaxed strap may permit board movement and load the short screen ribbon during charging. The source does not establish an insertion-force rating for the strap.

Correction: add small positive stops at safe PCB edges on the ribbon end, clear of the FPC connector/latch and flex cable. Keep the straps for lift-out retention. Verify both USB insertion/removal directions and cable access before printing the revised design.

## Validation gaps / physical checks

These are uncertainties, not proven collisions:

- The model omits the actual battery socket/plug, FPC connector/latch, switch/buttons, flexible cable shapes and strap overlap. Wire length and bend reach cannot be established by checking an empty rectangular aisle.
- The underside pin keepout explicitly stops short of the support rails; actual pin locations were not measured. Its passing collision test depends on that assumption.
- USB access is a nominal 35 × 14 × 8 mm space, not the user's measured cable housing.
- The centered active-image position is assumed within the opening; the paper template remains necessary because margin measurements changed during the discussion.
- Nut engagement is only 1.9 mm nominal before chamfers and manufacturing tolerances. Not a demonstrated failure, but confirm with specified hardware and an empty dry assembly.
- Ferrite magnet holding force and strap tension require real-world checks. Dimensional fit does not establish them.

## Checks completed

- Reimported all four exported STLs without running the source generator: watertight, consistent winding, one connected solid each, Z=0, expected extents.
- Checked nominal M3 screw shanks against all three assembled printed parts: clear.
- Tested all four actual-shell nut seats and the isolated coupon separately: two actual seats fail, coupon passes.
- Checked the PCB's free longitudinal travel against the exported carrier.
- Sliced every file with **PrusaSlicer 2.9.7**, using a generic 150 mm bed, PLA, 0.4 mm nozzle, 0.2 mm layers, three perimeters, five top/bottom layers, 20% gyroid infill, no supports, raft or brim. All four files sliced without error or repair warnings.
- Programmatically examined every output layer for nonempty extrusion, increasing Z and in-bed extrusion coordinates. Shell: 165 layers; carrier: 131; back: 15; coupon: 20. Expected final Z reached in each. This is not a manual visual inspection of every toolpath.
- The generic slicer emits bridges over sparse internal infill; this alone is not a design failure. No support-material feature was generated with supports disabled. Successful slicing is not proof of hardware fit or the suitability of the library's actual printer profile.

Evidence: `independent-checks.json`, `slicer-checks.json`, `toolpath-checks.json`, and per-part slice logs. Reproduction scripts are in this directory. Generic review G-code is kept only under ignored `.venv/review-tools/` and is NOT for sending to the library or running on its printer.

PrusaSlicer was downloaded from its official 2.9.7 release; DMG SHA-256 verified as f735f9d527823d159d9ac1e8f84ce1b74ea571e705e70e723bee546d070db60b. It ran in CLI mode with a project-local data directory; the disk image was unmounted afterward. No application was installed into /Applications.
https://github.com/prusa3d/PrusaSlicer/releases/tag/version_2.9.7

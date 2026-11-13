# Holladay printing package — revision 4

Ready to submit for a first-fit PLA print. Meshes are validated and slice cleanly; physical fit is not yet tested. The library performs printer-specific slicing. This is one enclosure made from three files.

## Files to submit

- `01_front_shell.stl` — print one, 126 × 82 × 33 mm.
- `02_electronics_carrier.stl` — print one, 120 × 76 × 26.2 mm.
- `03_back.stl` — print one, 126 × 82 × 3 mm.
- `optional_fit_coupon.stl` — optional separate first print (66 × 30 × 6.8 mm) to check your screw, nut, magnet and strap. Its nut corner reproduces the actual shell and adjacent screen fence. It is not part of the assembled case.

Every STL is already oriented with its intended flat bottom on Z=0. The assembled case is 126 × 82 × 36 mm, plus exposed magnet thickness and adhesive. Each STL is under 0.2 MB.

Suggested starting settings for staff: PLA, 0.2 mm layers, 0.4 mm nozzle, 3 perimeters, 5 top/bottom layers, 15–20% infill. All pieces are designed to print without supports in the supplied orientation. Staff should check their slicer's layer preview; use a brim if needed for adhesion. Do not automatically reorient them. A raft may affect the flat mating surfaces.

Print at 100% scale with STL units interpreted as millimeters. DO NOT RESIZE. No G-code is supplied because machine profiles belong to the library.

The County Library lists Holladay with both Adventurer 3 (150 × 150 × 150 mm) and Adventurer 5M Pro (220 × 220 × 220 mm). All parts fit either listed printer individually; do not assume all parts fit one build plate. Verify current machine availability with staff.
https://www.slcolibrary.org/what-we-have/create

The request form accepts STL/OBJ, maximum 25 MB uploads. The published price is $0.06/g including supports; staff determine the charge from slicing. If submitting separate requests, the form asks for three minutes between submissions. Select Holladay and do not consent to resizing.
https://www.slcolibrary.org/what-we-have/3d-printing-request

## Copy into the request form

Battery-powered e-ink fridge display enclosure, one project consisting of three STL files. Please print one of each in PLA, all the same color. Dimensions are in millimeters; print at 100% scale. Do not resize: parts must fit existing electronics. Each file is already oriented for printing, flat side down. Largest footprint is 126 × 82 mm. Suggested settings: 0.2 mm layers, 3 walls, 5 top/bottom layers, 15–20% infill. Designed without supports; please inspect layer preview. Please contact me if the files need changes, do not fit the available machine, or the estimate exceeds $10. The optional fit coupon, if provided separately, is a preliminary fit check and not a required enclosure part.

## What was checked

Exported STL reimport: watertight, consistent winding, positive volume, exactly one connected solid per file, expected dimensions, minimum Z=0, and file size. Manifold Boolean checks found no volume overlap between the three assembled parts or measured component envelopes. A 0.2 mm layer sweep found no new material beyond a 0.2 mm expansion of the preceding layer. Separately, all four files were sliced with PrusaSlicer 2.9.7 (generic PLA, 0.4 mm nozzle, 0.2 mm layers, no supports) with no errors or warnings; see `review-results/REVIEW.md`. That is not the library's printer profile.

The modeled lowest pin tips clear the carrier by 2.1 mm; the screen back to PCB underside gap is 9 mm. The pin projection assumption is 1.5 mm; the overall measured assembly thickness remains 18.5 mm. Board pads touch only the outermost 0.8 mm of its long edges. Confirm these edges are clear on your actual board before seating it.

Remaining physical checks: screen opening/alignment, printed tolerance, actual connector/wire/strap routing, underside pin placement, battery lead reach, USB plug access, and magnet holding power on the refrigerator. Four ferrite magnets' dimensions do not establish their holding force. Test over a padded surface before leaving the display on the fridge.

A solid-volume PLA calculation (density 1.24 g/cm³) is about 115 g for the three pieces if printed fully solid. The generic-profile slice at 20% gyroid infill used 106.6 g (50.6 + 26.1 + 29.9), about $6.40 at the published rate. This is NOT the library's quote; their profile, infill and any brim change the weight.

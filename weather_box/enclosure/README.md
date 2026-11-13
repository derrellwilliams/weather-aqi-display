# Fridge enclosure — revision 4

Three printable parts: front shell, removable electronics carrier, back. Four M3 × 30 mm screws and four M3 nuts secure the whole assembly. Two reusable straps anchor through paired carrier slots and fasten to themselves: one holds the driver board/XIAO; one holds the battery. Thin perimeter cushioning tape retains the screen. No external USB or button holes. Back removes for charging.

- **review.html** is the permanent interactive review file. Keep it; update it in place. It embeds the actual exported meshes, grayscale electronics reference shapes and the existing project display artwork. Do not delete it during cleanup.
- **print-files/** contains the three STLs and an optional fit coupon. All are in mm and oriented for printing.
- **PRINTING.md** contains Holladay submission text and settings.
- **ASSEMBLY.md** contains the hardware list, strap threading and assembly instructions.
- **screen-fit-template.pdf** is a 100% scale paper check for the display window.
- **validation.json** records automated mesh, interference and layer-support checks.
- **make_case.py** is the parametric source of truth. **case-review.scad** imports the final meshes for OpenSCAD viewing; it is no longer the obsolete revision 1 design.
- **update_preview.py** regenerates the preserved HTML from **assembly-meshes.json**.

The case is 126 × 82 × 36 mm excluding magnets. The panel is offset inside the case to center its visible opening: 16.3 mm left/right borders and 12.3 mm top/bottom. Your confirmed battery dimensions are used: 49.8 × 32.3 × 9.9 mm. It is rotated in-plane to bring its wire end closer to the driver board. The board underside sits 9 mm behind the screen back. Carrier corner sleeves carry screw loads independently of electronics.

Status: validated STL geometry for a first-fit PLA print. Not yet physically fit-tested or run through the library's own printer profile. Generic PrusaSlicer 2.9.7 slicing of all four files succeeded and is recorded in review-results/. Component positions and USB/wire keepouts use measurements and photo-based assumptions; the actual cable, underside pins, strap fit, display alignment and magnet strength must be checked during assembly. See PRINTING.md for exact limits of validation. No file has been submitted to the library.

## Rebuild

From the project root:

```
python3 -m venv enclosure/.venv
enclosure/.venv/bin/python -m pip install -r enclosure/requirements.txt
enclosure/.venv/bin/python enclosure/make_case.py
enclosure/.venv/bin/python enclosure/update_preview.py
enclosure/.venv/bin/python enclosure/make_documents.py
```

Runtime dependencies are isolated in ignored `.venv/`. No firmware or cloud code is changed.

Library references checked November 7, 2026:
- https://www.slcolibrary.org/what-we-have/create — Holladay lists Adventurer 3 (150 mm cubed) and Adventurer 5M Pro (220 mm cubed).
- https://www.slcolibrary.org/what-we-have/3d-printing-request — STL/OBJ, 25 MB limit, $0.06/g.

Hardware reference: standard M3 pan-head dimensions are documented by TR Fastenings (DIN 7985 / ISO 7045); the pockets also accept M3 socket heads up to the limits in ASSEMBLY.md. Back-to-back strap attachment is described by VELCRO Brand ONE-WRAP instructions: https://www.velcro.com/products/electronics-organization/one-wrap-ties/ . Amazon search terms are supplied without requiring any particular seller.

## Revision 4 corrections
Nut and screw cavities are now cut from the complete shell, preventing the screen fence from blocking the left nuts. Two corner stops now oppose USB insertion force with 0.4 mm nominal longitudinal clearance. The updated coupon reproduces the actual top-left corner and screen fence. Hardware insertion and both PCB travel directions are regression-tested. See review-results/REVIEW.md for results and physical-fit limits.

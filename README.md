# Elevation / Pivot - compact controller stack

**P6 compact attempt: two 80 x 130 mm boards.** Active branch:
`compact-80x130`. The complete P5 120 x 200 mm design is preserved on
`custom-controller-stack`, commit `29b4387`, and pushed to GitHub.

| Open in KiCad | Placement and board responsibility |
|---|---|
| [Carrier project](Elevation_Pivot_Daughter-Board.kicad_pro) | Power conversion/protection, brakes, CAN, motor encoders, Modbus and ADC/temperature; five DE9s |
| [Controller project](controller/Elevation_Controller.kicad_pro) | STM32H723, Ethernet/USB/debug, SSI and stepper interfaces; four DE9s |

All 503 footprints are placed on both faces: 258 controller, 245 carrier.
The complete SSI and stepper sheets moved to the controller (92 components).
Moved references gain 1000: e.g. carrier J2 becomes controller J1002.
Components, functional connections and native KiCad BOM metadata are preserved.
The converter architecture is unchanged and remains open for review.

**P6 uses a new stacking pinout. Do not mate P6 with P4/P5 boards.** J30 carries
clean logic and STM32 supplies; J31 carries field supplies and -BATT return.
All 50 contacts and four shared support pairs are checked. Board-face gap is
12 mm, PCB thickness 1.6 mm; tall converters face outward below the carrier.

No routed tracks, vias or copper zones. This demonstrates a compact placement
candidate, not completed routing, cable/enclosure fit or manufacturing release.

- [Current handoff](PROJECT_HANDOFF.md)
- [Assembly and placement notes](assembly/README.md)
- [Exact migration and P6 pinout](assembly/compact_manifest.json)
- [Electrical audit](docs/validation/p6_electrical_results.json)
- [Placement audit](docs/validation/p6_placement_results.json)
- Review images: `docs/reviews/p6/` (top and bottom of each board).

Run `python tools/validate_stack.py` for P6 exports, ERC, connectivity and native
PCB checks. BOM remains in the schematic editor's **Project BOM** field-table
preset. Earlier P4 PDFs and P5 assembly notes describe historical revisions.

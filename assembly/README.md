# P6 compact assembly - placement attempt

Both boards are **80 x 130 mm**, (20,20) to (100,150), with no XY translation.
Thickness is 1.6 mm each; face-to-face gap 12 mm. P5 is preserved in commit
`29b4387` on `custom-controller-stack`; this branch uses a new P6 pinout.

| Item | Controller | Carrier |
|---|---|---|
| J30 part | TSW-115-07-S-D | SSW-115-01-S-D |
| J30 origin / angle | (40,82.46), B.Cu 270 deg | (40,85), F.Cu 90 deg |
| J31 part | TSW-110-07-S-D | SSW-110-01-S-D |
| J31 origin / angle | (40,94.46), B.Cu 270 deg | (40,97), F.Cu 90 deg |
| H30 | (25,25) | (25,25) |
| H31 | (95,25) | (95,25) |
| H32 | (25,145) | (25,145) |
| H33 | (95,145) | (95,145) |

The footprint-origin offset is intentional; all same-numbered contact centres
match. Four shared 3.2 mm holes reserve 8 x 8 mm hardware envelopes. Carrier-only
enclosure holes are at (25,80), (95,80), (36,145), (84,145). Select actual supports,
screw lengths and retention method later. Keep metal hardware clear of domains.

**Only mate P6 boards together.** J30 carries clean logic, 5 V, 3.3 V and STM32
ground. J31 carries field rails and -BATT. This changes the P4/P5 electrical
contract. See `stack_interface.json` and `stack_pinout.csv` for every contact.

Both faces carry components. Controller F.Cu faces outward/up, with Ethernet,
USB, debug, four field DE9s and interface circuits. MCU and logic buck use B.Cu
in the gap. Carrier B.Cu faces outward/down, with five field DE9s, main power
parts and tall converters; small receiver/isolator/ADC circuits use F.Cu.
The 17.5 mm converters require that space plus tolerances below the carrier.
Inward package heights, solder tails and full assembly collisions remain to
be released against actual parts. The nominal STEP includes converter envelopes.

In assembled top-view coordinates, the controller left edge has STAR STEP
then PORT STEP; its right edge has STAR SSI then PORT SSI. Carrier left edge:
PORT MOTOR then BRAKES. Carrier right edge: STAR MOTOR then CAN. MODBUS exits
the carrier bottom. Bottom-view images mirror this correctly. DE9 bodies and
some edge-connector bodies overhang intentionally; PCB dimensions exclude
backshells and cables. Verify cable mating, bends and fastening access in the enclosure.

Connector nominal insertion remains:
`2.54 + 5.84 + 8.51 + 0.13 - 12 = 5.02 mm`, within SSW's 3.68-6.35 mm range.
Header/socket drills remain 1.02/1.04 mm. Finish spacer/seating/board-bow
tolerances. Sources: [TSW](https://suddendocs.samtec.com/prints/tsw-xxx-xx-xxx-x-xx-xxx-mkt.pdf),
[SSW](https://suddendocs.samtec.com/prints/ssw-1xx-xx-xxx-x-xx-xxx-xx-mkt.pdf),
[mating data](https://suddendocs.samtec.com/catalog_english/ssw_th.pdf).

Local review images are in `docs/reviews/p6/`, top/bottom for each board.
Dense references remain on F.Fab/B.Fab when silkscreen space is insufficient.
Nine digital-isolator copper corridors are shown on Dwgs.User and checked for
pad intrusion on both faces. Convert these to enforced copper keepouts and
complete isolation/return-plane design before routing. Existing manufacturer
guidance and converter height sources are recorded in `docs/archive/P5_ASSEMBLY.md`.

`python tools/validate_stack.py` checks both schematics and PCBs, including the
373 original assembled net groups and 50 mating pads. Current evidence lives
in `docs/validation/p6_electrical_results.json` and `p6_placement_results.json`.
Carrier J1 has one documented library difference from moving edge-clipped silkscreen to Fab; its pads are unchanged. Controller inherited footprint/drill/pad findings remain. The design is a placement study, with no routing, zones or fabrication release.
Library/footprint release, high-current placement refinement and cable/enclosure,
thermal/vacuum, vibration and final manufacturing checks remain open.

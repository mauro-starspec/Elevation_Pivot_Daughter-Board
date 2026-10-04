# P5 placement and nominal stack assembly

Electrical pinout P4.1; mechanical placement P5, 2026-10-03. Both native PCBs
are **120 x 200 mm**, with all 503 footprints placed. No routed tracks, vias
or copper zones remain. Schematics and native KiCad BOM fields are unchanged.
The 5 V converter arrangement remains open for review.

## Shared mechanical contract

All dimensions are millimetres in KiCad coordinates, viewed from above in the
assembled orientation. `stack_interface.json` is the shared contract.

| Item | Controller | Carrier |
|---|---|---|
| Outline | (20,20) to (140,220) | (20,20) to (140,220) |
| Size / thickness | 120 x 200 / 1.6 | 120 x 200 / 1.6 |
| Main component side | F.Cu, outward/upward | B.Cu, outward/downward |
| J30 part | TSW-115-07-S-D | SSW-115-01-S-D |
| J30 origin | (80.54,100) | (78,100) |
| J31 part | TSW-110-07-S-D | SSW-110-01-S-D |
| J31 origin | (82.54,143) | (80,143) |
| Stack connector side / angle | B.Cu / 180 degrees | F.Cu / 0 degrees |
| H30 centre | (43,26) | (43,26) |
| H31 centre | (112,26) | (112,26) |
| H32 centre | (56,213) | (56,213) |
| H33 centre | (103,213) | (103,213) |

Board translation is **(0,0)**. All 50 same-numbered mating pads coincide.
The 2.54 mm footprint-origin offset accounts for opposite-side mounting and
numbering. Only mate the P5 mechanical pair; earlier P4 coordinates differ.
The electrical contract remains 32 application signals, reset, four power
contacts and thirteen grounds.

Four 12 mm supports establish the face gap. Their 3.2 mm NPTH holes have an
8 x 8 mm clear hardware envelope on both boards. Carrier enclosure holes are
at (26,26), (134,26), (26,214), (134,214). Supports, stack headers and edge
connectors are locked. Actual supports, screw length and vibration retention
remain to be selected; metal hardware must not bridge isolated domains.

## Placement and access

The 17.5 mm carrier converters cannot face inward across the 12 mm gap.
Carrier components therefore face outward below the lower board; only its
stacking sockets occupy the top. Allow converter height plus tolerance and
enclosure clearance below the carrier. Controller components face upward.

Nine DE9s face outward: four per side and Modbus at the bottom. In assembled
top view, the left edge has STAR STEP, CAN, BRAKES and PORT MOTOR; the right
has STAR SSI, PORT SSI, PORT STEP and STAR MOTOR. The bottom-view render
correctly mirrors this. Connector bodies intentionally overhang; all pads
remain within the outline. Actual harness backshells, bends and tool access
still need enclosure verification.

Carrier protection sits near connectors, receivers on the field side and
isolators toward the central clean-logic corridor. Converter space remains
reserved while consolidation is undecided. Controller MCU decoupling, VCAP
and clock parts surround their pins. The PHY lies between MCU and Ethernet;
power conversion forms a separate cluster. Ethernet/USB exit the top. Debug,
buttons and test points are on the outward face. Unused lower controller area
follows the equal-size requirement; components were not spread out to fill it.

Dense reference labels are on F.Fab/B.Fab where silkscreen would cross pads;
all identifiers remain available in the PCB editor and assembly views.
Routing must preserve isolation boundaries, reference continuity, oscillator
separation and compact power loops. Placement does not establish final EMC,
creepage, thermal performance or controlled impedance.

## Connector fit

Selected Samtec connectors have 2.54 mm pitch and 30 microinch gold contacts.
Header post length is 5.84 mm above its 2.54 mm body; socket body is 8.51 mm
with 0.13 mm standoff. At a 12 mm board-face gap:

`insertion = 2.54 + 5.84 + 8.51 + 0.13 - 12 = 5.02 mm`

This is within the specified 3.68-6.35 mm range. Complete the tolerance stack
with actual spacers, seating, soldering and board bow. Header/socket drills
are intentionally different: 1.02/1.04 mm. Unshrouded connectors require
orientation and seating checks; asymmetrical supports assist orientation.

Sources: [TSW](https://suddendocs.samtec.com/prints/tsw-xxx-xx-xxx-x-xx-xxx-mkt.pdf),
[SSW](https://suddendocs.samtec.com/prints/ssw-1xx-xx-xxx-x-xx-xxx-xx-mkt.pdf),
[mating data](https://suddendocs.samtec.com/catalog_english/ssw_th.pdf).
Height sources: [R-78HB](https://recom-power.com/pdf/Innoline/R-78HB-0.5.pdf),
[Wurth](https://www.we-online.com/components/products/datasheet/173950575.pdf),
[REC10K](https://recom-power.com/pdf/Econoline/REC10K-AW.pdf).

## Files and verification

Native PCB files are in the root and `controller/` projects. Local previews:
`outputs/placement/controller_3d.png` (top), `elevation_3d.png` (bottom),
and corresponding `*_placement.png` footprint-envelope views.
`Elevation_Stack_Mechanical.step` includes boards, connectors, supports and
conservative converter envelopes; it is not a fully populated/vendor-certified model.

`tools/validate_stack.py` verifies ERC, netlists, 50 mating pads, connector
sides/drills, thickness and four support pairs. `tools/validate_placement.py`
(KiCad Python) verifies preserved parts/pad nets/DNP, outline, no routing,
no footprint-envelope overlaps, all pads within edges, 8 mm support envelopes,
selected critical pin distances and all 21 schematic files byte for byte.

Carrier DRC: zero violations. Controller: 117 inherited library-footprint
differences, nine U401 thermal-hole drill-rule findings and four clearances
internal to U101. No exclusions were added. There are no component-to-component
clearance findings. The 401 controller and 499 carrier unconnected items are
expected. Evidence: `docs/validation/p5_placement_results.json`.

Resolve the inherited footprint/manufacturing findings before routing release.
Exact connector footprint release, full 3D/cable/enclosure fit, stackup,
thermal/vacuum behavior, vibration and fabrication qualification remain open.
`tools/place_stack_pcbs.py` starts from a local pre-placement snapshot; do not
rerun it over later manual edits without reviewing them.

## Official layout guidance consulted

- [ST AN5419](https://www.st.com/resource/en/application_note/an5419-getting-started-with-stm32h723733-stm32h725735-and-stm32h730-value-line-hardware-development-stmicroelectronics.pdf): MCU decoupling and functional separation.
- [ST AN2867](https://www.st.com/resource/en/application_note/an2867-oscillator-design-guide-for-stm8afals-stm32-mcus-and-mpus-stmicroelectronics.pdf): compact oscillator placement.
- [TI LMR33630](https://www.ti.com/lit/ds/symlink/lmr33630.pdf): nearby VIN/BOOT capacitors and compact switching cluster.
- [TI ISO1410](https://www.ti.com/lit/ds/symlink/iso1410.pdf) and [ISO7760](https://www.ti.com/lit/ds/symlink/iso7760.pdf): local bypassing and separated domains.
- [ADI LTC4364](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4364-1-4364-2.pdf): grouped protection and provision for Kelvin sensing.
- [Microchip LAN8742](https://ww1.microchip.com/downloads/en/DeviceDoc/DS_LAN8742_00001989A.pdf): PHY interface, supply and clock requirements.

Guidance was checked against official sources during this pass. Unrouted boards
do not yet demonstrate compliance with complete manufacturer layout guidance.

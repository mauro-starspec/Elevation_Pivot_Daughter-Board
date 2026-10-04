# Elevation / Pivot - custom controller stack

P4.1 electrical design / P5 placement, 2026-10-03: two KiCad 9 projects in one
repository. Both boards are now **120 x 200 mm**, with all 503 footprints placed
and no tracks, vias or copper zones. The controller faces upward; carrier
components face outward below the stack to accommodate the tall converters.
Schematics and native KiCad BOM fields are unchanged. Routing is not started.

| Board | Open in KiCad | Role |
|---|---|---|
| Elevation carrier | [Elevation_Pivot_Daughter-Board.kicad_pro](Elevation_Pivot_Daughter-Board.kicad_pro) | Field connectors, power, brakes, drives, SSI, encoders, CAN, Modbus RTU, ADC and isolation |
| Controller | [controller/Elevation_Controller.kicad_pro](controller/Elevation_Controller.kicad_pro) | STM32H723, Ethernet, USB-C, SWD, watchdog and shared 3.3 V logic supply |

The 30-contact J30 and 20-contact J31 connect matching pin numbers. Headers mount
on the controller underside; sockets mount on the carrier top. Four matching
M3 supports set a nominal 12 mm board-face gap. Their positions are locked.

- [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md): current scope and remaining work.
- [docs/CONTROLLER_STACK_P4.md](docs/CONTROLLER_STACK_P4.md): electrical integration.
- [docs/PIVOT_MODBUS.md](docs/PIVOT_MODBUS.md): isolated pivot Modbus RTU and DE9 wiring.
- [assembly/stack_pinout.csv](assembly/stack_pinout.csv): all contacts and MCU assignments.
- [assembly/README.md](assembly/README.md): assembly dimensions and connector selection.
- Local schematic export: `outputs/P4_Stack_Schematic_Review.pdf`; older assembly covers are superseded by the P5 assembly notes until re-exported.

Run `python tools/validate_stack.py`. It checks ERC, preserved circuitry, MCU
assignments, PCB/netlist parity, mating pad registration and support clearances.
The former `validate_pivot_schematic.py` entry point now forwards to this checker.

Both SSI channels, both DE9 motor encoder interfaces and both passive 1206
thermistors remain. Field sheets preserve the user's drawing edits. No battery
voltage/device current monitoring or new one-shot fuse was added. PSRB retains
system power control. Existing brake-current feedback remains.

P3 and the previous routed carrier are recoverable from Git commit `0c9ba1f`.
Controller source: [mauro-starspec/stm32h723-controller](https://github.com/mauro-starspec/stm32h723-controller)
at `2328ccb`. That separate source checkout is untouched. Firmware is unchanged.

Placement previews: `outputs/placement/controller_3d.png` and
`outputs/placement/elevation_3d.png`. Placement evidence:
[P5 audit](docs/validation/p5_placement_results.json). Carrier DRC has no
violations; controller inherited footprint/library and fine-pitch/drill findings
remain explicit. This is a placement review, not a fabrication or flight release.

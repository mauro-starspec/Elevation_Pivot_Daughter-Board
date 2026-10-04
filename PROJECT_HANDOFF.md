# Project handoff - P6 compact stack

Updated 2026-10-03. Branch `compact-80x130`. User requires maximum 100 x 175 mm
and asked for an **80 x 130 mm** attempt, with circuitry redistributed between
the boards as needed. Preserve the prior design first; no routing.

## Preservation

P5 (120 x 200 mm) is committed as `29b4387` and pushed to
`origin/custom-controller-stack`. Its native projects, BOM, libraries, STEP and
previews remain recoverable. Historical notes: `docs/archive/P5_HANDOFF.md`
and `docs/archive/P5_ASSEMBLY.md`. Never silently rerun a P5 builder over P6.

## Current design

Two matched 80 x 130 mm, 1.6 mm thick, four-layer boards, outlines (20,20) to
(100,150). Both faces are populated. No tracks, routed vias or copper zones.

- Controller: original MCU/Ethernet/USB/debug/watchdog/logic power, plus complete
  SSI and stepper interface circuits. Four DE9s. 258 footprints.
- Carrier: input protection/converters, brakes, CAN, both motor encoders,
  Modbus, ADS1115 and passive temperature sensors. Five DE9s. 245 footprints.

The move transfers 92 components. Original references gain 1000 on the
controller to avoid collisions, and retain original UUIDs, values, footprints,
fit/DNP state and procurement fields. Circuit drawing geometry is retained on
the moved sheets. Hierarchical signals become standard global labels. The
carrier root is reorganized as a sheet overview. Field library aliases are
prefixed Field_ in the controller to avoid shadowing its standard KiCad libraries.

Native BOM metadata and Project BOM presets remain the source of truth. No
parts were removed or replaced to reach the smaller size. Purchasing holds,
temperature uncertainty, connector footprint review and supply consolidation
questions from P5 remain open. No battery/current monitoring was reintroduced.
Both SSI and both A/B/Z motor encoders, Port/Star naming, two passive 1206
thermistors, CAN, Modbus and brake-current feedback remain.

## Interface and mechanics

P6 is electrically and mechanically incompatible with P4/P5 stacking pinouts.
Only mate this P6 pair. J30: clean logic plus 5 V / 3.3 V and STM32 ground.
J31: field supply rails with -BATT returns. Field power is now allowed across
J31 intentionally; the old P4 statement that no field rails cross is superseded.
The six field nets are +5V_FIELD, both SSI +6.5 V rails, both SSI +5 V rails,
and -BATT. Parallel supply contacts preserve capacity provisionally; verify
actual field/encoder loads and derating before release. MCU assignments are
unchanged, and functions now on the controller no longer traverse J30.

`assembly/stack_interface.json`, `assembly/compact_manifest.json` and
`assembly/stack_pinout.csv` are the current contract. The CSV is interface
documentation, not a replacement BOM. Stack gap remains 12 mm with 5.02 mm
nominal mating insertion. Mounting centres and connector pad locations match
exactly. Main converters face outward below the carrier; controller MCU and
logic buck are on its inward B.Cu face. Low-profile carrier interfaces use
the inward F.Cu face. The assembly model includes conservative converter
envelopes, not all component models or a qualified harness/enclosure.

Some connector bodies intentionally overhang the laminate. The requested
80 x 130 mm dimension is the PCB outline, not the cable/backshell envelope.
Inward components, solder tails and support screws require final Z-height
review against actual package drawings and the enclosure.

## Verification and review boundary

Run `python tools/validate_stack.py` (dispatches to P6 checks) and
`python tools/validate_bom_fields.py` for metadata preservation. Electrical
audit checks the complete assembled circuit through all 50 paired contacts:
373 original net groups preserved, all 503 values/footprints preserved,
native BOM fields/presets retained, zero ERC findings on both boards.

The native PCB audit checks schematic/pad parity, equal outlines, no routing,
component and opposite-side through-hole-tail collisions, support envelopes,
all pads inside the edges, selected critical pin distances, and clear copper
corridors beneath nine digital isolators. Those corridors are drawn on
Dwgs.User. Enforce them as routing/zone keepouts before introducing copper;
they are not substitutes for final creepage and insulation coordination.

Review current results in `docs/validation/p6_*_results.json`. The controller
inherits the P5 U101 pad-clearance, U401 thermal-hole and library-footprint
findings. Carrier J1 has one intentional footprint-instance difference: edge-clipped silkscreen moved to its fabrication layer, with all pads unchanged. No rule waivers are added. Unconnected nets are expected.

This is a compact placement attempt. Routing feasibility, return-path planning,
DC/DC hot loops, exact footprint release, cable access, final full 3D collision
check, power/thermal/vacuum and vibration qualification remain open. Some
bulk power capacitors still need refinement when high-current routes are designed.
Do not present this as fabrication-ready or expand beyond the user's maximum.

## Rebuilding and further work

P6 scripts: `build_compact_schematics.py`, `place_compact_pcbs.py` (KiCad Python),
`annotate_compact_pcbs.py` (KiCad Python), `update_compact_contract.py`, and
`build_stack_models.py` (CadQuery). Builders start from the preserved P5 snapshot;
do not run them over subsequent manual edits without reviewing the changes.
The validation entry point is read-only for design files.

Next review the physical split and harness exits, then refine the compact power
placement and decide converter consolidation. Keep routing separate until
authorized. Actual encoder and servo-controller models remain unconfirmed.
Modbus is the existing isolated two-wire RTU/RS-485 provision; firmware has
not been changed. See historical P5 handoff for MCU assignments and original
BOM provenance; P6 manifest overrides its board ownership and stack coordinates.

# Project handoff - Elevation / Pivot controller stack

Updated 2026-10-03. Electrical revision **P4.1**, mechanical **P5 placement**.
Branch: `custom-controller-stack`.

## Current authorization: component placement, no routing

The user requested equal board dimensions and actual placement, authorizing
removal of old traces and planes. Both native PCBs are now 120 x 200 mm.
All 166 controller and 337 carrier footprints are placed; no tracks, vias or
copper zones remain. Carrier components face outward below the stack, allowing
17.5 mm converters with the retained 12 mm interboard gap. Controller parts
face upward, with its stacking headers underneath. The 50 mating contacts and
four support pairs align. Schematics and native KiCad BOM metadata are unchanged.

Placement DRC has no footprint-envelope or component-to-component clearance
findings. Carrier DRC has zero violations. Controller retains 117 inherited
library differences, nine U401 thermal-hole drill findings and four internal
U101 pad clearances. These are not suppressed. Resolve before routing release.
See `assembly/README.md` and `docs/validation/p5_placement_results.json`.

The 5 V converter arrangement remains open; no electrical consolidation was
performed. Servo identity and harness remain unconfirmed. No fabrication,
routing or purchasing release is implied.

The earlier planning/BOM pass below is historical. Its no-placement statements
describe that earlier pass; P5 is the subsequently authorized placement work.

### Native KiCad BOM fields - updated 2026-10-03

Both projects now have a saved **Project BOM** preset in the schematic editor's
Edit Symbol Fields table. The source of truth is each symbol's properties,
including Manufacturer, MPN, LCSC, Operating Temperature, Function, Assembly,
BOM Status, Footprint, Datasheet and BOM Review. Source links, temperature
basis/min/max, verification dates and supplier status are additional columns.
Legacy field aliases are synchronized for existing consumers. New properties
are hidden on the drawing; circuit values, footprints and positions are unchanged.

Inventory: carrier 337 references / 303 fitted parts; controller 166 references /
134 fitted parts. All 437 fitted parts have MPNs, including explicit candidates;
390 have C-codes, a mixture of newly matched catalog IDs and inherited records.
A code is not proof of current stock or JLC assembly availability. Purchasing
status remains provisional. The native grouped purchasing views currently contain
87 carrier rows and 65 controller rows, with DNP options identifiable. The 54 PCB
features (pads, solder links and holes) are excluded from purchasing. Mechanical
supports and harness hardware still need their own actual selections.

New metadata covers stack connectors, DE9s, encoder receivers/isolation,
thermistors, Modbus, FB201/C222 and associated passives. C188 is provisionally
KEMET C0805C102KDRACTU. C110/C140 are explicit 10 uF/100 V TDK candidates on HOLD
pending effective capacitance and supply review. PS5/PS10/PS11 remain on HOLD.
F1/F2 remain in the circuit with a review note against the user's fuse preference.
U14's -CT/-R suffix discrepancy and inherited datasheet/footprint mismatches are
visible review items. Carrier R17/D9/Q16/D6/D12 still lack verified temperature
ranges. Recorded legacy ranges and junction absolute limits are not application
qualification; inspect Temp Status and Temp Basis. Historical stock notes are
not current availability evidence.

Validation: `python tools/validate_stack.py` and
`python tools/validate_bom_fields.py`. Both schematics pass ERC with zero
violations/exclusions; all 50 stack contacts and four supports still match.
The BOM pass preserved all 21 schematic drawing/electrical structures, both
netlists including net names/pins, and both PCB files byte for byte.
Evidence: `docs/validation/bom_fields_review_results.json` and
`docs/validation/bom_drawing_baseline.json`. Local pre-edit snapshot:
`_work/before_bom_fields_20261003/`. `tools/update_bom_fields.py` is the migration
used for this pass, with reviewed supplemental data in `docs/bom_field_updates.json`;
do not rerun over later manual table edits without reviewing its proposed changes.

### BOM requirements and provenance

Preserve the existing procurement detail. The source format is
`../stm32h723-controller/output/bom/controller_bom.csv`, with supporting
`docs/supplier_temperature_matrix.csv` and `docs/FOOTPRINT_RELEASE_AUDIT.csv`
in that source checkout. Those are historical inputs, not the merged-board BOM.

Maintain the two native board-specific tables in the current schematics. Do not
replace them with CSV/workbook deliverables. Every reference retains its board
identity through its project. Group purchases by
exact manufacturer and MPN, with compatible package, ratings and fit status;
never by value alone. Keep DNP options, PCB-only features and purchased assembly
hardware identifiable. Each row needs:

- Board, references, quantity, function/description and fitted/DNP status.
- Manufacturer, exact orderable MPN including suffix, and datasheet URL.
- JLCPCB/LCSC C-code, exact-part verification, JLC library/assembly status,
  availability observation, source link and check date. A catalog C-code alone
  does not establish JLC assembly availability. Missing IDs stay explicit.
- Minimum/maximum operating temperature in degrees C, rating basis and source.
  Keep ambient, junction and storage ratings distinct. The required electronics
  temperature range is still unresolved; do not inherit the source BOM's
  "acceptable -40 to +85" judgment as approval for this balloon application.
- Value, tolerance, voltage/current/power ratings and dielectric where relevant.
- Package, footprint, maximum height, footprint verification status/source,
  assembly method, alternatives and any unresolved selection notes.

The carrier uses fields such as `MANUFACTURER_PART_NUMBER`, `LCSC` and
`Operating Temperature`; the controller uses `MPN`, `LCSC Part #` and separate
temperature fields. These are now normalized in the symbols while preserving provenance.
"See datasheet", blank values and old stock snapshots are unfinished evidence.

The first metadata pass covered J30/J31 headers/sockets, J20/J21/J22 DE9 selections,
encoder/thermistor additions, the Modbus parts, and controller FB201/C222.
The current controller R104 MPN is CRCW08052K21FKEA (2.21k), while the old BOM
still lists CRCW08051K33FKEA (1.33k). Current C221 is 1u with updated MPN, while
the old BOM groups it with 4.7u parts. Rebuild membership and quantities before
reusing supplier records; match historical evidence by exact MPN, not reference.

### Power review before fixing the converter area

| Present supplies | Current role | Planning treatment |
|---|---|---|
| PS5, PS10, PS11 | Field 5 V and two motor-encoder 5 V rails, all returning to -BATT | First consolidation comparison: one adequately sized source with branch filtering/protection versus the present split |
| PS2, PS6 | SSI 6.5 V preregulators feeding local 5 V stages | Separate review; these are not simply duplicate 5 V outputs |
| PS1 | Brake 5 V from +24V_BRAKE / GND_BRAKE | Retain the brake-domain boundary in the comparison |
| PS4 | Isolated 5 V for STM32 logic | Retain the logic isolation boundary |
| U14 | Isolated CAN supply from field 5 V | Retain the CAN isolation boundary |

This is a comparison to perform, not an approved circuit change. Establish
encoder demand, concurrent field/Modbus/CAN loads, startup, input range,
temperature derating, branch faults and recovery before selecting a replacement.
The existing shared encoder receiver supply already comes from PS10/U105, so
independent encoder converters do not currently give fully independent feedback.
Compare cost, occupied area, heat and failure consequences. Filtering does not
replace galvanic isolation. Keep converter footprints and their placement
provisional until this decision is settled.

### Placement complete; footprint release remains

Both outlines run from (20,20) to (140,220), with zero board translation.
Connector placement, functional groups, critical decoupling and support
clearances are established. Actual connector MPN drawings, package/pad mapping,
paste/drills and inherited controller library/rule findings still need release
review. Check cable backshells, tool access, height and the enclosure together.
Use `assembly/README.md` for current geometry and local review image paths.

## Project organization and status

One repository, two KiCad 9 projects:

- Root `Elevation_Pivot_Daughter-Board.kicad_pro`: carrier, 12 schematic pages.
- `controller/Elevation_Controller.kicad_pro`: controller, 9 schematic pages.

Both schematics are complete for this review pass. Both PCB drafts contain the
current netlists, matching J30/J31 footprints and four matching supports. They
are unrouted, with all footprints placed in P5. Only intentional connector
body overhangs extend beyond outlines; all pads are inside. Routing and full
assembly qualification remain. Do not describe the PCBs as fabrication-ready.

P3 source and routed PCB: Git commit `0c9ba1f`; local snapshot
`_work/before_controller_stack/`. Controller source: sibling
`../stm32h723-controller`, commit `2328ccb`; that checkout was not modified.
Shared Stack libraries live in the parent repo. Keep the directory structure.

## Decisions carried forward

Keep Port/Star terminology, both SSI channels and both motor A/B/Z encoders.
J20/J21 are DE9 sockets. One ISO7760FDWR isolates all six encoder signals toward
the MCU; AM26LV32E receivers remain on the field side. P4.1 currently has both
5 V encoder supplies and the shared receiver 3.3 V supply; the 5 V supply split
is now explicitly open for review. Actual encoder identity and the
installed DE9 harness are still unverified.

Keep TH1/TH2 as TDK B57621C5103J062 passive 1206 thermistors. Existing ADS1115
U21 AIN2/3 and existing I2C isolator U24 read them. Readings require brake power.
No extra temperature IC, regulator or isolator is needed.

Other systems measure battery voltage/device current. PSRB switches device
power remotely. Do not restore deleted P1 monitoring/distribution circuits,
external thermistor inputs or newly added one-shot fuses. Preserve existing
brake-current feedback and field protection. Use standard 1.27 mm signal labels,
conventional power/ground symbols and plain-language component captions.

## Board split and power

The carrier keeps field connectors, converters, protection, brakes, drive
commands/faults, SSI, motor receivers/isolation, CAN and ADS1115.

The controller retains STM32H723ZGT6, decoupling/VCAP, 8 MHz HSE, optional LSE,
reset/boot buttons, LAN8742A Ethernet, USB-C, external ST-LINK through STDC14,
watchdog and status LEDs. Removed: 20 ADC channels, generic expansion headers,
expansion power switches, analog LDO, INA181 monitor and TMP235 sensor.
VDDA uses a ferrite and 1 uF/100 nF filtering from 3V3_DIG.

Carrier isolated PS4 supplies 5 V on J30-25/26. Controller TPS259470A input
protection feeds LMR33630, which supplies both MCU and carrier clean-side logic.
The 3.3 V return is J30-29/30. Both boards share GND_STM32/controller GND.
Field power/returns do not cross this interface. The isolation barriers remain
on the carrier, between clean logic and field electronics.

R104 is now 2.21 kohm: nominal 1.51 A electronic current limit with automatic
retry. This is inherited semiconductor protection, not a replaceable fuse or
an ADC current-monitor function. USB VBUS remains sense-only. PS4 startup,
actual load, inrush, thermal derating and fault recovery need bench verification.

## Interface and assembly

J30 has 30 contacts; J31 has 20. Same pin number mates to same pin number.
`assembly/stack_interface.json` and `assembly/stack_pinout.csv` define the
contract: 32 application signals, reset, four power contacts and thirteen grounds.
P4.1 reassigns J31-13/14/18 from ground to Modbus TX/RX/DE on BOTH boards.
Only mate P4.1 electrical / P5 mechanical boards together. P5 changes both outlines and connector/hole coordinates as a matched pair.

## Pivot Modbus addition (P4.1)

User requires Modbus for the pivot servo. Implemented provisionally as two-wire
Modbus RTU over RS-485; drive model, electrical variant and harness remain
unconfirmed. New carrier sheet `Pivot_Modbus.kicad_sch` uses U160 ISO1410DWR
(combined isolation + RS-485, wide SOIC-16) and J22 DE9 socket. Existing CAN stays.
J22 follows the Modbus V1.02 assignment: 1=Common (-BATT), 5=D1(+), 9=D0(-),
shell=PIVOT_CHASSIS; all other contacts NC. This differs from the encoder ports.
U160 A is positive D1; TI's A/B naming differs from the Modbus naming convention.

USART2 AF7: PD5/pad119 TX, PD6/pad122 RX, PD4/pad118 active-high hardware DE.
DE and /RE are tied, with a 10k pull-down (reset = receive, driver disabled).
TX/RX have 10k pull-ups. Existing +3V3_STM32/GND_STM32 powers the logic side;
existing +5V_FIELD/-BATT powers the bus side. No extra converter or fuse.
RS-485 shares the field return; it is isolated from the STM32 logic domain.

JP160/161 are closed copper solder links enabling the two 560R bias resistors;
open BOTH if another device supplies bus bias. JP162 enables 120R/0.5W termination;
open when this board is not a cable end. Servo-end termination must be verified.
Firmware is not implemented. See `docs/PIVOT_MODBUS.md` for settings, power
allocation and bring-up checks. P5 places the Modbus parts on the carrier, with J22 facing the bottom edge.

Controller underside: TSW-115-07-S-D and TSW-110-07-S-D, 180 degrees.
Carrier top: SSW-115-01-S-D and SSW-110-01-S-D, 0 degrees.
Nominal board-face gap 12 mm; PCB thickness 1.6 mm; four M3 supports. Nominal
contact insertion is 5.02 mm. Supports are asymmetrical. Connectors are
unshrouded, so mark and check orientation before applying power.

Both outlines are 120 x 200 mm. All carrier components except stacking sockets
face outward below the carrier; reserve 17.5 mm plus tolerances below it.
STEP includes conservative converter envelopes, not a fully populated or
vendor-certified assembly. See `assembly/README.md` for dimensions and limitations.

## Firmware consequences

Port quadrature: TIM2 PA5/PB3. Star: TIM3 PC6/PC7. Z: PE4/PE3, EXTI4/3.
Use TIM5_CH1 on PA0 for Star STEP; TIM2 is reserved for Port quadrature.
Disable SWO on PB3: its STDC14 connection was removed while retaining SWD.
PC2_C/pad 28 needs the analog switch closed for Port SSI data.

Ethernet RMII, USB, PD8/PD9 debug UART and PE0/PG0 watchdog controls remain.
Status LEDs use PB0/PE1/PB14. Use the actual 8 MHz crystal in clock setup;
the Nucleo ST-LINK clock-source assumption does not apply. Implement TIM3 wrap
handling and slow temperature sampling/calibration without disrupting brake
current reads. No firmware was changed.

## Validation and review

Run `python tools/validate_stack.py` (Python + sexpdata and KiCad 9).
`tools/validate_pivot_schematic.py` forwards to the P4 checker.

Checks: zero ERC violations/exclusions on both schematics; 50 mating signals;
32 unique GPIOs; 144 explicit MCU pin dispositions; 27 retained internal MCU
connections; 191 preserved carrier net groups; unchanged retained carrier
component selections; nine field sheets with unchanged drawing/electrical
structure (BOM properties now populated); both PCB/netlist pairs;
50 physically registered pads and four clear support pairs. P4.1 additionally
checks UART routing, reset bias, bus polarity, termination paths and isolation.
Independent pre-Modbus evidence is in `docs/validation/p41_pre_modbus.json`.

Evidence: `outputs/p4_stack_validation.json`, `outputs/p4_*_erc.json`,
`outputs/p4_*_drc.json`. Full PCB DRC is not complete: unconnected nets are
expected; controller inherited footprint/library differences, fine-pitch/drill
constraints remain open. P5 resolved placement silkscreen findings. These inherited findings are not suppressed. Current placement reports are in `outputs/placement/` and `docs/validation/p5_placement_results.json`.

For schematics use `outputs/P4_Stack_Schematic_Review.pdf`; any older assembly cover is superseded by P5 assembly notes until re-exported. Separate exports:
`outputs/P4_Controller_Review.pdf`, `outputs/P4_Elevation_Review.pdf`.
Read `docs/CONTROLLER_STACK_P4.md` for rationale and sources.

## Remaining work

Review architecture and pin assignments. Confirm actual NEMA34 encoder model,
supply demand, maximum frequency and DE9 harness. Review the completed P5 placement,
then finish isolation spacing, stackup/impedance rules, routing, DRC and full component/cable
clearances. Verify startup defaults, watchdog, boot/debug, Ethernet/USB and
encoder capture on hardware. Temperature, thermal/vacuum and vibration
qualification are open; possible -50 C balloon operation is not qualified.

The original `Elevation_Control_STM32_Daughter-Board` remains the as-built
hardware, firmware and bench-test reference. P1-P3 docs are historical; P4
supersedes their Nucleo and unchanged-PCB statements.

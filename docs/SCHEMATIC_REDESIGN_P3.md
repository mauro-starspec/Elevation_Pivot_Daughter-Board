> Historical P3 reference. [P4 controller integration](CONTROLLER_STACK_P4.md) supersedes Nucleo, interface-header and unchanged-PCB statements below.

# P3 - passive onboard temperature and drawing cleanup

2026-10-03. Schematic only. Supersedes P2 temperature circuitry and header-label
presentation; retains its encoder interfaces and Port/Star channel mapping.
Subsequent drawing update: DE9 connectors and component-role captions, while
preserving the user's schematic presentation edits.

## Foundation reviewed

Reviewed the original elevation project's schematic and engineering README,
the original controller firmware's pin definitions and ADS1115 acquisition,
and the frozen baseline connectivity/component records at e0909c8.

- The daughter board carries control and feedback, not motor-phase wiring.
- Two SSI absolute-encoder channels remain; two motor A/B/Z interfaces supplement them.
- The original isolation domains are intentional: -BATT, GND_STM32, GND_BRAKE,
  GND_CAN, GND_FLOAT, and the filtered PS4 input return. GND_FLOAT returns through
  Q16; the PS4 input return must not bypass FL1. No domains are joined by this change.
- Original U21 is an ADS1115BQDGSRQ1 at 0x48, powered from +5V_BRAKE. U24 already
  isolates its bus from the MCU. AIN0/1 measure brake current; AIN2/3 were spare.
- The original firmware samples only AIN0/1, with a fixed +/-4.096 V scale.
  Passive sensors can use its spare inputs; another ADC, regulator and isolator
  are unnecessary for this function.
- Existing physical-header and MCU-unit signal ports are hierarchical labels
  with 1.27 mm text. New encoder ports now follow that convention at both ends.
- External systems measure battery/device current and voltage; PSRB controls
  device power. Those functions are not added to this daughter board.

## Two onboard thermistors

TH1 and TH2 are on ADS1115.kicad_sch, alongside the existing converter. The
separate temperature sheet and added U140/U141/U143/U144 are removed. The sensors
remain mounted on the board; there are no external temperature connectors.

| Function | Sensor | Divider / filter | ADC input |
|---|---|---|---|
| Board-temperature proxy | TH1 | R180 / R182 / C190 | U21 AIN2, pin 6 |
| Power-area temperature | TH2 | R181 / R183 / C191 | U21 AIN3, pin 7 |

Selected sensor: TDK B57621C5103J062, a 10 kohm NTC, +/-5% at 25 C, with R/T
characteristic 1010. The 1206 body is approximately 3.2 x 1.6 mm with two exposed
solder terminations, using the existing R_1206_3216Metric footprint. It has no
hidden thermal pad. Its specified operating range is -55 to +125 C; this does
not extend the rating of the existing ADC or the rest of the board.

Each circuit is +5V_BRAKE -> NTC -> 10 kohm, 0.1% -> GND_BRAKE, with 1 kohm
series resistance and 100 nF at the ADC input. Only eight passive parts are added
for both sensors. The divider output rises with temperature. At nominal 5 V:

| Temperature | Nominal ADC voltage, before small input loading |
|---|---|
| -40 C | 0.224 V |
| 25 C | 2.500 V |
| 85 C | 4.391 V |

Use R_NTC = R_fixed * (V_excitation / V_ADC - 1) and the manufacturer's curve
1010 to convert resistance. These are nominal values, not accuracy guarantees:
thermistor tolerance, excitation tolerance/drift, ADC loading and thermal
placement affect the result. Calibrate the excitation and temperature response.
Maximum nominal thermistor dissipation is 0.625 mW at R_NTC = 10 kohm; verify
self-heating under the actual enclosure/low-pressure conditions.

Both sensors electrically belong to GND_BRAKE even when placed near a heat
source in another domain. Preserve isolation clearances and do not bond a
sensor pad to unrelated copper. TH1 should be away from local heat sources;
TH2 should be near the selected power hot spot. Placement waits for layout.
Readings require the brake supply and are invalid when it is off.

## Firmware follow-through, not implemented here

Keep the existing brake channels at +/-4.096 V and their existing scaling.
Configure temperature channels for +/-6.144 V: nominal 187.5 microvolt/code.
The PGA range does not allow ADC pin voltages outside its supply rails.
Expand the two-channel scheduler and per-channel scale handling; sample
temperature slowly while retaining the required brake-current acquisition
cadence. Discard readings on supply loss and allow filter settling after power-up.
Detect near-rail sensor faults instead of converting them to plausible temperatures.
An open high-side NTC pulls the input low; a short pulls it near the supply.
Temperature accuracy and fault thresholds need bench calibration.

No firmware files were changed. No new I2C addresses, pull-ups or bus branches
are introduced. Existing U21 and U24 still communicate over the original I2C bus.

## Drawing and connectivity

All six motor-encoder signals now use matching hierarchical input labels at
the physical Nucleo sockets and MCU units. CN9 index labels align with the
adjacent SSI labels. Local labels remain appropriate for nets confined to a
sheet, such as the two thermistor outputs; they are not inter-sheet ports.
New local labels use the existing 1.27 mm text size. Supplies retain power symbols.

Validation compares original pin groups independently of their renamed net
names, and checks the exact Port/Star migration. Only the twelve allocated
MCU/socket pins and two formerly unused ADC pins are exempt from the frozen
baseline; their new connections are explicitly checked. All original component
values/footprints, the PCB hash, and the two inherited ERC exclusions are checked.
Header label type and size are checked to prevent the screenshot mismatch.

Run `python tools/validate_pivot_schematic.py`. Reports and the 11-page review
PDF are in outputs/. The pre-P3 files are recoverable in _work/before_p3/.
These checks establish schematic consistency, not hardware qualification.

Final P3 result: 304 original net groups preserved, 31 explicit connection checks
passed, and zero reported ERC findings with two inherited exclusions unchanged.
A separate comparison with the pre-P3 netlist preserved all 357 retained pin
groups, including the complete added encoder circuits. CN7/CN9 and the ADC
sheet were checked in the rendered PDF. The PCB SHA-256 is unchanged.

## Open encoder decisions

Actual NEMA34 encoder identity, supply consumption, A/B/Z electrical interface,
resolution, maximum frequency and existing D-sub harness remain unverified.
The custom DE9 pinout remains a proposal. NEMA frame size does not determine
encoder pinout or drive current. See the retained encoder sections in the P2
report and PIVOT_ENCODER_INTERFACE.md. Do not treat the earlier HT23/ZAA example
as the installed hardware. Existing SSI, brakes, CAN and drive-control circuits
remain intact; PCB and original firmware remain unchanged.

## DE9 and component descriptions

J20/J21 now use Connector:DE9_Socket_MountingHoles, with the same right-angle
DE9 footprint family as the existing connectors on this board. This updates
the schematic footprint assignment only; the PCB is unchanged. Existing pins
1-9 keep their assignments and the six unused HD15 contacts are removed.

| DE9 contact | Function |
|---|---|
| 1 | Dedicated +5 V motor-encoder supply |
| 2, 9 | Field return, -BATT |
| 3, 4 | A+, A- |
| 5, 6 | B+, B- |
| 7, 8 | Z+, Z- |
| Shell / pad 0 | PIVOT_CHASSIS |

The earlier HD15 cable reference does not establish DE9 harness compatibility.
The manufacturer's eventual connector and cable drawings must match this map.
No power supplies were consolidated in this update.

Forty-five short text captions identify the main receivers, isolators,
regulators, power converters, ADC, CAN transceiver, brake switches, protection
devices and filter. They are drawing text, not signal labels or part values.
The user's component positions and visual edits are retained; only connector
stub geometry changes where required by the DE9 symbol. A snapshot of the
user's files before this update is in _work/before_de9_names/.

Update verification: 2,913 pre-existing drawing items are unchanged, excluding
the intentional connector edits. All 347 retained net groups match the user's
saved schematic at the start of this update; only twelve unused HD15 contacts
were removed. The baseline checks still pass with zero reported ERC findings
and the PCB hash unchanged. The captions were checked in the rendered review.

## Shared six-channel encoder isolation

The latest update replaces U101/U111 ISO7730F with one ISO7760FDWR U101.
All six channels run from the field receivers toward the MCU: Port A/B/Z
use inputs 2/3/4 and outputs 15/14/13; Star A/B/Z use inputs 5/6/7 and
outputs 12/11/10. The MCU allocation and DE9 pinout remain unchanged.
The device retains the SOIC-16W footprint. The F variant defaults outputs
low on loss of field-side power while the MCU-side supply remains powered.

U105 now supplies both receivers, their bias networks, and U101's field side
on +3V3_MOTOR_ENC. U115 and C143/C144/C146/C147 are removed with U111.
U101 pins 1/8 use +3V3_MOTOR_ENC/-BATT; pins 16/9 use
+3V3_STM32/GND_STM32. These isolation domains remain separate. No regulator
outputs are paralleled. C115/C145 bypass the receivers and C116/C117 bypass
the two isolator supplies; C114 remains U105's output capacitor.

PS10 and PS11 remain separate 5 V encoder converters. PS10 also supplies
U105, so its loss disables both feedback paths even if PS11 remains powered.
Encoder current and converter margin still require the actual encoder data.

Star receiver outputs cross the hierarchy into U101 on the Port sheet.
All six MCU-side test points are together there. The user's six root-sheet
MCU wires are preserved. Source before this update is saved under
_work/before_shared_isolator/. Current validation: 304 baseline net groups,
42 explicit connection checks, zero reported ERC findings with the two
inherited exclusions unchanged, and unchanged PCB hash. The root and both
encoder sheets were inspected in the refreshed PDF.
Comparison against the user's saved schematic preserves 339 retained pin
groups after accounting for the intentional shared-rail merge and replaced
parts. All 35 original root wires are unchanged, and every other child sheet
is byte-identical to the snapshot.

## Primary component references

- [TI ISO7760 datasheet](https://www.ti.com/lit/ds/symlink/iso7760.pdf): six forward channels, pin map, supply range and F-variant default-low behavior.

- [TDK 1206 NTC datasheet, B57621C5, February 2019](https://product.tdk.cn/system/files/dam/doc/product/sensor/ntc/chip-ntc-thermistor/data_sheet/50/db/ntc/ntc_smd_standard_series_1206.pdf), pages 2 and 4: package, ordering code, ratings and curve 1010.
- [TI ADS1115-Q1 datasheet](https://www.ti.com/lit/ds/symlink/ads1115-q1.pdf): input limits, gain ranges and input impedance.

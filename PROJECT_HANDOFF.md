# Project handoff — Elevation Pivot Daughter Board

Last updated: 2026-10-03

## Purpose

Continue the hardware redesign in this repository without depending on the long
development chat that created the original elevation controller.

The immediate objective is a new STM32H723 Nucleo daughter board that preserves
the proven elevation-control functions while adding:

1. two Applied Motion `HT23-553D-ZAC` incremental-encoder interfaces;
2. board-routed power for two STR8 stepper drives;
3. independent current measurement for each STR8 supply using ACS725 sensors;
4. raw-battery voltage measurement, with optional protected-bus diagnostics;
5. useful board and system-temperature measurements.

This is currently a requirements-and-baseline repository. It is **not ready for
fabrication**.

## Repositories and folders

- New pivot-board repository:
  `https://github.com/mauro-starspec/Elevation_Pivot_Daughter-Board`
- Local working copy:
  `C:\Users\Mauro\Documents\KiCad\Elevation_Pivot_Daughter-Board`
- Original, tested elevation project:
  `C:\Users\Mauro\Documents\KiCad\Elevation_Control_STM32_Daughter-Board`

Keep the original project intact as the as-built firmware, UI, test-data, and
hardware-history reference. Make the redesign in this repository only.

## Baseline status

The complete KiCad 9 hardware source was copied from the working elevation
daughter board and renamed `Elevation_Pivot_Daughter-Board`.

Baseline validation with KiCad 9.0.7:

- schematic ERC: 0 findings;
- PCB unconnected pads: 0;
- PCB DRC: three inherited courtyard overlaps in the fixed Nucleo
  connector/mounting group: H3/CN9, H4/CN10, and H2/CN7.

Firmware, dashboards, build products, recordings, and test results were
intentionally excluded from this repository.

## Existing system that should be preserved

The original design and bench system contain:

- NUCLEO-H723ZG controller;
- two STR8 step/direction/enable/fault interfaces;
- two brake power/control/current-measurement channels;
- two 22-bit SSI elevation encoders;
- ADS1115-Q1 on I2C for brake current;
- protected battery input and local power conversion;
- CAN and the existing isolation architecture.

The original firmware and browser UI have successfully operated the brakes,
both STR8 drives, both motors, and both SSI encoders. Preserve working
interfaces unless a documented redesign requirement supersedes them.

## Naming convention

Use these human-facing names from this point forward:

- `Port (LH)` for the left-hand channel;
- `Star (RH)` for the right-hand channel.

Existing schematic nets may retain LH/RH temporarily during controlled
migration, but new documentation, UI labels, measurements, and requirements
should use Port and Star.

## Requirement 1 — two ZAC incremental encoders

Two motors are Applied Motion `HT23-553D-ZAC` units. The ZAC assembly uses the
Renco ZAA incremental encoder, legacy Applied Motion part `970-1001`, beneath an
encoder cover. Each encoder provides:

- 5 V ±10% supply;
- differential A+/A−, B+/B−, and Z+/Z− line-driver signals;
- 2,000 signal periods/revolution;
- 8,000 x4-decoded counts/revolution, or 0.045° per motor-shaft count;
- one Z index pulse per motor revolution.

The GBA values previously recorded in this handoff are superseded. The installed
ZAA encoder supply current and exact connector/cable pinout still require
verification against the physical hardware and cable drawing.

For two encoders provide:

- two keyed encoder connectors;
- six differential receiver channels total;
- proper receiver-end termination, ESD protection, decoupling, and shield
  strategy;
- two STM32 hardware encoder timers, each using CH1 and CH2 for A/B;
- two additional Z/index inputs;
- receiver outputs that are natively safe for 3.3 V STM32 inputs.

Do not connect the external differential pairs directly to STM32 GPIO. See
[`docs/PIVOT_ENCODER_INTERFACE.md`](docs/PIVOT_ENCODER_INTERFACE.md).

An incremental encoder loses its accumulated position on power loss. The final
system still needs an agreed reference method. Z is only one index per motor
revolution and may not identify a unique pivot angle after gearing.

## Requirement 2 — route and measure two raw-battery STR8 power branches

The present board communicates with the STR8 drives but does not carry their DC
power. The redesign will take both STR8 power branches directly from the raw
battery input, before the LTC4364 protected branch. Each STR8 branch has its own
current sensor. The LTC4364 does not carry STR8 current.

Preferred functional arrangement:

```text
raw battery + -> Port branch fuse/protection -> current sensor -> Port STR8
              `-> Star branch fuse/protection -> current sensor -> Star STR8

raw battery + -> LTC4364 -> protected board/load bus (separate path)
```

Use a bidirectional ACS725 variant (`AB`) unless analysis proves reverse current
cannot occur. Stepper drives can return energy to their DC bus during
deceleration, so reverse-current visibility and a safe regeneration path matter.

The exact ACS725 suffix is not selected. It determines range and sensitivity.
The 3.3 V ACS725 family offers ±5, ±10, ±20, ±30, ±40, and ±50 A variants. Pick
the range only after confirming measured STR8 DC input current, acceleration
peaks, regeneration, and fault/inrush requirements. Avoid excessive range
because it reduces current resolution.

ACS725 implementation constraints from the manufacturer datasheet include:

- 3.0–3.6 V supply;
- analog output;
- about 1.2 mΩ primary conduction resistance;
- primary current flows through pins 1/2 to pins 3/4;
- layout and copper area determine thermal performance;
- filter pin can trade bandwidth for lower output noise.

The two current sensors will produce analog voltages for two ADC channels.
ADS1115 AIN2 and AIN3 are currently unused and are the leading candidates.
AIN0 and AIN1 already measure Port and Star brake current. This is suitable for
monitoring and logging, but the ADS1115's multiplexed sample rate is not a
substitute for fuses, STR8 protection, or fast hardware overcurrent shutdown.

### Mandatory power-stage review

The STR8 branches intentionally bypass the LTC4364. Do not increase or redesign
the LTC4364 current limit merely to supply the drives. The independent raw-
battery branches still require calculation and validation of:

- worst-case simultaneous DC input current;
- startup/inrush and bulk capacitance at both drives;
- acceleration and stall demand;
- reverse/regenerative current path;
- branch and upstream fuse strategy;
- connector current and voltage ratings;
- copper width, thickness, vias, temperature rise, and voltage drop;
- fault containment if one STR8 or its cable shorts;
- separation from the LTC4364-protected branch so a drive fault cannot force
  current through that protected path.

Do not confuse the STR8's motor phase-current setting with its DC-bus input
current. They are related through drive power, duty cycle, motor speed, and
conversion losses, but they are not the same number.

## Requirement 3 — battery voltage

The required voltage measurement is the raw battery feeding the STR8 branches.
The user expects battery-voltage measurement to be retained. The copied design
contains `+BATT` and `+BATT_Prot` power nets, but the 2026-10-02 exported
netlist did not reveal a clearly named dedicated battery-voltage ADC signal.
Verify this in the schematic before claiming it already exists.

Preferred redesign provision:

- measure raw battery voltage at the STR8 branch source;
- optionally measure the LTC4364-protected bus as a second diagnostic;
- design the divider for worst-case surge/clamp voltage, not only nominal 48 V;
- use appropriately rated series resistors, RC filtering, input protection, and
  a documented ADC conversion ratio;
- do not accidentally bridge an existing isolation boundary with an ordinary
  divider. Confirm the ADC reference domain or use an isolated measurement
  architecture.

AIN2/AIN3 will likely be consumed by STR8 current, so battery voltage may need a
spare STM32 ADC input, another external ADC channel, or a larger-channel ADC.

## Requirement 4 — temperature

Add at least one real board-temperature sensor. The STM32 internal sensor mainly
indicates MCU die temperature and should not be treated as board ambient.

A good candidate for review is the TI TMP117 in its manufacturable WSON
package. It operates from −55 °C to +150 °C, supports I2C, has four selectable
addresses, low self-heating, and good accuracy. Do not use address 0x48 because
the existing ADS1115 is documented at 0x48; select and document another address.

Recommended temperature architecture:

1. **Board/ambient sensor:** near a board edge and away from power converters,
   current sensors, the Nucleo, and heavy copper.
2. **Power-area sensor:** optional second sensor or thermistor near the hottest
   protection/current-distribution region. This measures local stress rather
   than ambient.
3. **External temperature inputs:** reserve connectors for thermistors or
   digital probes on the brakes, motors, or enclosure. An onboard sensor cannot
   reveal brake-coil or motor winding temperature accurately.

Decide what each sensor is intended to measure before placement. One sensor
cannot simultaneously represent ambient air and a power-component hot spot.

## Environmental qualification warning

The discussion includes possible operation near −50 °C. Component limits must
be reviewed as a system:

- TMP117 is specified to −55 °C;
- the reviewed ACS725 L-grade family is specified to −40 °C;
- the Renco R35i/ZAA encoder family is specified to −30 °C, while the complete
  legacy motor assembly and all cabling still require application-level review;
- the Nucleo board, connectors, capacitors, DC/DC modules, brakes, motors, and
  STR8 drives also require individual review.

Do not infer −50 °C qualification from an onboard temperature reading. If the
electronics remain in a heated enclosure, document the minimum controlled
internal temperature and failure response. Otherwise select qualified parts or
obtain manufacturer approval and perform environmental testing.

## Strongly recommended additions

- Individual STR8 branch fuses and clearly rated power connectors
- Test points for both ACS725 outputs, battery-divider output, 3.3 V, 5 V,
  encoder receiver outputs, and STR8 control/fault signals
- Spare footprints or header access for unused ADC/GPIO resources
- Power-present LEDs placed so their current does not distort measurements
- Hardware-safe STR8 disable states during MCU reset and programming
- Reverse-polarity/miswiring analysis and connector keying
- Input/output bulk-capacitance and regeneration review
- Board revision ID and calibration storage for current/voltage offsets
- Independent external emergency-stop/power-removal architecture; firmware
  monitoring must not be the safety-rated stop

## Next engineering sequence

1. Confirm whether the two ZAC encoders supplement or replace any existing SSI
   encoder channels.
2. Confirm the actual pivot mechanics: gear ratios, travel, maximum RPM,
   required angular accuracy, and reference method.
3. Measure or obtain the STR8 DC-input current envelope at 48 V, including idle,
   steady motion, acceleration, stall/fault, and deceleration/regeneration.
4. Choose the ACS725 range and filtering from those measurements.
5. Complete an STM32 pin/timer allocation for two A/B timer pairs and two Z
   inputs without disturbing validated step generation, SSI, I2C, CAN, UART,
   and fault lines.
6. Choose the differential receiver, termination, ESD parts, and connectors.
7. Rework the complete high-current power path and protection calculations.
8. Decide the number, purpose, and placement of temperature sensors.
9. Implement schematic changes as new, clearly named hierarchical sheets.
10. Run ERC, net-parity review, power/thermal review, PCB DRC, harness review,
    BOM lifecycle review, and fabrication-preview review before ordering.

## Information the next chat should request if still unknown

- Verify both physical motor labels as `HT23-553D-ZAC` and identify the exact
  installed encoder cables/connectors.
- Are they additions to, or replacements for, the two existing SSI encoders?
- Pivot gearbox ratio and motor-to-output direction for each side
- Maximum expected motor RPM and cable lengths
- Whether the hardware itself sees −50 °C or sits in a conditioned enclosure
- Exact STR8 model and measured/expected 48 V input-current envelope
- Desired current accuracy and sampling rate
- Desired number and locations of temperature measurements
- Preferred field connectors and approximate board-size constraints

## Source documents

- [Applied Motion HT23-553D-ZAC product page](https://www.applied-motion.com/s/product/eolstep-motor-high-torqueht23553dzac/01t5i000000xz33AAA?name=HT23-553D-ZAC-NEMA-23-High-Torque-Stepper-Motor-w-Encoder-and-Cover)
- [Applied Motion 970-1001 ZAA encoder drawing](https://applied-motion.s3.amazonaws.com/documents/2D-Drawing/970-1001_RevC_Renco_ZAA_0.pdf)
- [Renco R35i encoder family data](https://www.renco.com/fileadmin/user_upload/renco/1319497-21_Drehgeber_RENCO_en.pdf)
- [Allegro ACS725 datasheet](https://www.allegromicro.com/-/media/files/datasheets/acs725-datasheet.pdf)
- [TI TMP117 product page and datasheet](https://www.ti.com/product/TMP117)

## Git state at handoff creation

The initial hardware baseline was pushed to `main` as commit `f2151c9`. Any
later handoff-document commit should appear after it. Always run `git status`
before editing because the user may also work on the repository from another
computer.

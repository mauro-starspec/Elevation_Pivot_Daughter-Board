# Project handoff — Elevation Pivot Daughter Board

Last updated: 2026-10-02

## Purpose

Continue the hardware redesign in this repository without depending on the long
development chat that created the original elevation controller.

The immediate objective is a new STM32H723 Nucleo daughter board that preserves
the proven elevation-control functions while adding:

1. two Applied Motion GBA incremental-encoder interfaces;
2. board-routed power for two STR8 stepper drives;
3. independent current measurement for each STR8 supply using ACS725 sensors;
4. battery/protected-bus voltage measurement;
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

## Requirement 1 — two GBA incremental encoders

Two motors will use the embedded encoder from the Applied Motion
`HT23-598D-GBA` family. Each encoder requires:

- 5 V ±0.5 V supply;
- up to 130 mA;
- differential A+/A−, B+/B−, and Z+/Z− reception;
- 1,000 lines/revolution and 4,000 x4-decoded counts/revolution;
- one Z index pulse per motor revolution;
- support for up to 60 kHz encoder output frequency.

For two encoders, budget at least 260 mA before supply margin and provide:

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

## Requirement 2 — route and measure two STR8 power branches

The present board communicates with the STR8 drives but does not carry their DC
power. The redesign is intended to accept the battery/protected-bus supply and
send separate power branches to the left and right STR8 drives, with one ACS725
sensor in each branch.

Preferred functional arrangement:

```text
battery input -> protection -> protected DC bus
                              |-> branch protection -> ACS725 L -> STR8 L
                              `-> branch protection -> ACS725 R -> STR8 R
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

The two unused ADS1115 inputs, AIN2 and AIN3, are natural candidates for the two
ACS725 outputs. AIN0 and AIN1 are already used for left and right brake current.
This is suitable for monitoring and logging, but the ADS1115's multiplexed
sample rate is not a substitute for fuses, STR8 protection, or a fast hardware
overcurrent shutdown.

### Mandatory power-stage review

The inherited LTC4364 sheet is annotated for a 10 mΩ sense resistor and an
approximately 5 A current limit. Supplying two STR8 drives through that path is
therefore not a simple connector addition. Recalculate and validate:

- worst-case simultaneous DC input current;
- startup/inrush and bulk capacitance at both drives;
- acceleration and stall demand;
- reverse/regenerative current path;
- LTC4364/MOSFET/shunt ratings and behavior;
- branch and upstream fuse strategy;
- connector current and voltage ratings;
- copper width, thickness, vias, temperature rise, and voltage drop;
- fault containment if one STR8 or its cable shorts.

Do not confuse the STR8's motor phase-current setting with its DC-bus input
current. They are related through drive power, duty cycle, motor speed, and
conversion losses, but they are not the same number.

## Requirement 3 — battery voltage

The user expects battery-voltage measurement to be retained. The copied design
contains `+BATT` and `+BATT_Prot` power nets, but the 2026-10-02 exported
netlist did not reveal a clearly named dedicated battery-voltage ADC signal.
Verify this in the schematic before claiming it already exists.

Preferred redesign provision:

- measure the protected bus used by the STR8 branches;
- consider measuring raw battery voltage as a second diagnostic if useful;
- design the divider for worst-case surge/clamp voltage, not only nominal 48 V;
- use appropriately rated series resistors, RC filtering, input protection, and
  a documented ADC conversion ratio;
- avoid loading or bypassing the existing protection/isolation boundaries.

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
- the Applied Motion GBA encoder datasheet specifies −20 °C to +85 °C;
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

1. Confirm whether the two GBA encoders supplement or replace any existing SSI
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

- Are both GBA encoders identical HT23-598D-GBA units?
- Are they additions to, or replacements for, the two existing SSI encoders?
- Pivot gearbox ratio and motor-to-output direction for each side
- Maximum expected motor RPM and cable lengths
- Whether the hardware itself sees −50 °C or sits in a conditioned enclosure
- Exact STR8 model and measured/expected 48 V input-current envelope
- Desired current accuracy and sampling rate
- Desired number and locations of temperature measurements
- Preferred field connectors and approximate board-size constraints

## Source documents

- [Applied Motion FBA/GBA/HBA encoder datasheet](https://applied-motion.s3.amazonaws.com/documents/Datasheets/925-0070_RevB_FBA-GBA-HBA_Encoder_Datasheet.pdf)
- [Allegro ACS725 datasheet](https://www.allegromicro.com/-/media/files/datasheets/acs725-datasheet.pdf)
- [TI TMP117 product page and datasheet](https://www.ti.com/product/TMP117)

## Git state at handoff creation

The initial hardware baseline was pushed to `main` as commit `f2151c9`. Any
later handoff-document commit should appear after it. Always run `git status`
before editing because the user may also work on the repository from another
computer.

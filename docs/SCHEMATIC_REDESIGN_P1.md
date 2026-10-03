# P1 schematic redesign

**Historical revision, superseded by P2 on 2026-10-03.** The user removed the
added STR8 power/current and voltage circuits because other
systems provide the required functions, including PSRB power control.
The current schematic adds motor encoders, retains both onboard temperature
sensors, and uses Port/Star throughout. External thermistor inputs are omitted.
See [P2](SCHEMATIC_REDESIGN_P2.md); do not use the P1 requirements below for new work.

Date: 2026-10-03. Scope: schematic only. The PCB is still the original baseline
and does not represent these circuits. P1 is an engineering review revision,
not a fabrication release.

## Decisions from this session

Mauro confirmed that both existing SSI channels must remain, with two motor
encoders added. D-sub connectors are preferred. He identified the motors as
NEMA34; that conflicts with the previous HT23-553D-ZAC identification. The actual
motor and encoder part numbers, resolution, supply demand and harness therefore
remain unverified. A NEMA frame size does not determine electrical current.

The new encoder circuits assume 5 V differential A/B/Z. Do not connect an
unverified encoder or legacy cable to the proposed connectors.

## What changed

| Sheet | Added circuitry |
|---|---|
| `Pivot_Encoder_Port` | HD15 connector, A/B/Z termination, bias and ESD protection; quad receiver; three-channel isolator; dedicated encoder supply |
| `Pivot_Encoder_Star` | Same circuit for Star |
| `Pivot_STR8_Power` | Main battery inlet, two fused raw-battery branches, two Hall current sensors, external regeneration-clamp connection, shield/chassis connection |
| `Pivot_Monitoring` | Field 3.3 V rail, isolated I2C, second ADC, raw and protected bus dividers and input protection |
| `Pivot_Temperature` | Two TMP117 sensors and two protected external thermistor inputs |

The STM32 sheet connects six previously unused connector positions to the new
encoder outputs. U21 AIN2/AIN3 now receive STR8 currents. The existing MCU I2C
bus also connects to the new monitoring circuits. Existing SSI, brake, step,
direction, disable, fault, CAN and supply-conversion circuits are retained.

J8 is the new main battery inlet. J1 pins 1/2 are intentionally disconnected
and marked NC; J1 pins 3/4 still accept the separate brake supply. This prevents
the old smaller connector from becoming the intended two-drive battery inlet.
The harness must change accordingly.

## MCU allocation

| New signal | Nucleo connection | MCU pin | Function |
|---|---|---|---|
| Port A | CN7 pin 10 / D13 | PA5 | TIM2_CH1, AF1 |
| Port B | CN7 pin 15 / D23 | PB3 | TIM2_CH2, AF1 |
| Port Z | CN9 pin 16 / D57 | PE4 | EXTI4 input |
| Star A | CN7 pin 1 / D16 | PC6 | TIM3_CH1, AF2 |
| Star B | CN7 pin 11 / D21 | PC7 | TIM3_CH2, AF2 |
| Star Z | CN9 pin 22 / D60 | PE3 | EXTI3 input |

Use SWD debugging and disable SWO trace on PB3. PA5 also connects to the
Nucleo D13 LED control circuit; its loading must be included in signal testing.
PE6 was deliberately avoided because it is used by the existing Star fault
input through CN10 pin 28. Nucleo alternate connector positions are not
independent MCU pins.

TIM2 is 32-bit and TIM3 is 16-bit. Firmware must extend the Star counter across
wraps and handle direction correctly. Maximum encoder frequency, digital input
filtering and index capture latency must be checked after motor speed and
encoder resolution are known. No firmware was changed.

Sources: [STM32H723 datasheet](https://www.st.com/resource/en/datasheet/stm32h723zg.pdf),
[MB1364 user manual](https://www.st.com/resource/en/user_manual/um2407-stm32h7-nucleo144-board-stmicroelectronics.pdf),
[H723 Nucleo schematic](https://www.st.com/resource/en/schematic_pack/mb1364-h723zg-e01_schematic.pdf).

## Encoder circuits and harness

Each channel uses AM26LV32EIDR followed by ISO7730FDWR. The receivers and encoder
power reference `-BATT`; the isolator outputs use `+3V3_STM32` and `GND_STM32`.
No encoder return connects directly to the MCU ground.

Each differential pair has a provisional 120 ohm termination and 560 ohm
pull-up/pull-down bias. Ignoring receiver loading, disconnected-cable bias is
3.3 x 120 / (560 + 120 + 560) = 0.319 V. At 3.0 V with adverse 1% resistor
tolerances it is about 0.285 V before receiver loading. The termination in
parallel with the bias path presents about 108 ohms differential load.
Validate bias margin with receiver loading and confirm cable impedance and
encoder drive capability before freezing values. A shorted pair is not a
guaranteed valid state or a detected cable fault.

The three ESD arrays per encoder are TPD2E2U06QDBZRQ1, with pins 1/2 on the
signals and pin 3 on `-BATT`. Their unidirectional clamps assume signals stay
near the supplied 0-to-5 V field domain. Test ESD and ground-offset behavior at
the complete connector; a component ESD rating is not a system test result.

Each encoder has a dedicated R-78HB5.0-0.5 supply from `+BATT_Prot`, a provisional
0.5 A output fuse, and a local 3.3 V receiver regulator. Input capacitance must
remain at least 3.3 uF at the maximum applied DC voltage. Check converter
minimum-load behavior, availability, output tolerance, cable voltage drop and
temperature derating. The converter's 72 V input limit constrains the protected
bus clamp. Budget up to roughly 5 W total output for these two supplies before
losses, although actual encoder consumption is unknown.

Proposed board connector pinout, J20/J21:

| Pin | Signal |
|---|---|
| 1 | Fused +5 V |
| 2 | Field return, -BATT |
| 3 / 4 | A+ / A- |
| 5 / 6 | B+ / B- |
| 7 / 8 | Z+ / Z- |
| 9 | Additional field return |
| 10-15 | NC |
| Shell | PIVOT_CHASSIS |

This is a proposed **custom harness** mapping, not the Applied Motion cable
pinout. Connector gender, mating view, footprint and exact MPN are release
holds. Do not substitute a two-row DA15 for the three-row HD15 symbol.
J12 provides the new shield/chassis termination. C188 couples it to field
return; R172 is a DNP direct-bond option. Confirm the system chassis bond and
compatibility with the retained connector shells, which use the old grounding
arrangement. Do not populate ground bonds without that review.

Sources: [receiver datasheet](https://www.ti.com/lit/ds/symlink/am26lv32e.pdf),
[isolator datasheet](https://www.ti.com/lit/ds/symlink/iso7730.pdf),
[ESD array datasheet](https://www.ti.com/lit/ds/symlink/tpd2e2u06-q1.pdf),
[RECOM supply datasheet](https://recom-power.com/pdf/Innoline/R-78HB-0.5.pdf).

## STR8 power and current measurement

Both branches start at raw `+BATT`, ahead of the LTC4364. Each branch passes
through a 7 A fast fuse and an ACS725LLCTR-20AB-T before its drive connector.
Both primary input pins and both primary output pins are connected. Drive
returns go directly to `-BATT`. The LTC4364 current limit has not been changed.

The 7 A fuse value follows the manufacturer's STR8 recommendation. It is not
a measurement of operating current. The manual also explains why phase
current and DC input current differ. Without the motor winding data, load,
speed and drive settings, actual average and peak supply currents cannot be
calculated reliably. Two 7 A branches give a provisional 14 A distribution
design basis, plus the protected board loads; a fuse does not clamp current to
its nominal rating.

The ±20 A range is provisional and gives more transient headroom than ±10 A.
At nominal 3.3 V the sensitivity is 66 mV/A and zero-current output is 1.65 V.
At 7 A, typical conductor dissipation is 7² x 0.0012 = 59 mW per sensor.
Fault/inrush pulse survival still needs the fuse let-through and Hall conductor
limits checked together. The board has no validated copper-current rating yet.

Sensor electronics use a new 3.3 V regulator in the existing brake ground
domain. Their isolation barriers separate the battery conductor from those
electronics. U21 remains at its existing 5 V supply and 0x48 I2C address.
AIN0/1 still measure brake currents; AIN2/3 measure Port/Star STR8 current.
The Hall FILTER capacitors are 10 nF and output RC filters are 4.7 kΩ/1 uF
(about 34 Hz). Use PGA ±4.096 V. Nominal conversion is:

`current_A = (signed_code * 0.000125 - calibrated_zero_V) / calibrated_sensitivity_V_per_A`

The nominal quantization step is about 1.89 mA; this is not sensor accuracy.
Hall offset/noise, supply tolerance and temperature dominate. A 1% change in
sensor supply alone moves the nominal zero by about 0.25 A equivalent.
Calibrate zero and gain, and do not use this multiplexed ADC as fast overcurrent
protection. The Hall supply is not independently measured in P1.

J8-J11 electrically select Phoenix 1714971 terminals, rated nominally 32 A.
Their manufacturer footprint remains unassigned pending mechanical review.
F20/F21 require exact fast-fuse and holder MPNs, a DC voltage rating of at least
125 V and adequate battery fault-current breaking capacity. Those footprints
are deliberately unassigned. Final fuse coordination, cable gauge, connector
derating and upstream pack protection remain open.

J11 is only a connection for an external regeneration clamp; a clamp is not
implemented on this board. Regeneration can flow back through each sensor and
fuse to the battery while the path is closed. A BMS or emergency disconnect
can remove that sink. Specify an energy-rated clamp and disconnect strategy
before energizing the redesign. The clamp threshold must exceed maximum charged
battery voltage and stay below the drive limit, including tolerances.
Reverse-polarity protection for these raw branches is external and mandatory;
the existing LTC4364 protection does not cover them. Added drive bulk capacitance
is deferred until inrush and regeneration energy are known.

Sources: [STR4/8 hardware manual, revision L](https://applied-motion.s3.amazonaws.com/documents/Manuals/STR4-8%20Hardware%20Manual%20920-0030L_0.pdf),
[ACS725 datasheet](https://www.allegromicro.com/-/media/files/datasheets/acs725-datasheet.pdf),
[Phoenix 1714971](https://www.phoenixcontact.com/us/products/1714971/pdf).

## Voltage and temperature measurement

U142 is an ADS1115 in the battery field domain. A separate ISO1540 links it to
the existing MCU I2C bus. ADDR connects to SDA for address 0x4A. U142 reads raw
battery, protected bus and the two thermistor inputs. U140 supplies the new
field 3.3 V rail. Existing MCU pull-ups remain; the new field bus has its own
4.7 kΩ pull-ups. Start at 100 kHz and verify bus capacitance and low-level
thresholds with both isolation branches connected. Do not assume arbitrary
multi-master or clock-stretching operation through parallel side-1 isolators.

Each voltage divider is three 100 kΩ, 0.1% upper resistors and a 10 kΩ, 0.1%
lower resistor. A further 10 kΩ and 100 nF filter precede the ADC. BAT54S
diodes clamp to the field rails. R192 bleeds the field rail when unpowered,
limiting back-power from the high-value dividers. The 90 V measurement envelope
is a provisional diagnostic range, not permission to apply 90 V to the drives
or converters. Upstream surge energy and clamp voltage still require review.

| Applied bus voltage | Ideal ADC voltage |
|---|---|
| 48 V | 1.548 V |
| 75 V | 2.419 V |
| 90 V | 2.903 V |

At PGA ±4.096 V, nominal bus voltage is `signed_code * 0.000125 * 31`.
Use at least 20 ms power-up settling. Calibrate the assembled divider: ADC input
loading, resistor tolerances, clamp leakage and temperature affect this ideal
ratio. In particular, BAT54S leakage can be material with a high-impedance
divider. The design does not claim precision voltage accuracy across temperature.

U143 is a TMP117 on MCU ground, with ADD0 tied high for 0x49. It measures board
temperature away from local heat sources. U144 is another TMP117 on field
ground, ADD0 tied to field SCL for 0x4B; it measures a power-area hot spot.
Both ALERT outputs are NC and software polls temperatures. The exposed-pad
ground connection assumes assembly followed by calibration; review TI's
mechanical-stress guidance before finalizing the paste/thermal-pad treatment.

J22/J23 accept insulated 10 kΩ NTC probes. Pull-ups, series resistors, shunt
capacitors, ESD protection and rail clamps are provided. An absent probe reads
high and a shorted probe reads low. Choose probe beta, accuracy and cable
length before writing conversion and plausibility limits. These inputs do not
measure motor winding temperature unless the probe installation supports it.

Sources: [ADS1115 datasheet](https://www.ti.com/lit/ds/symlink/ads1115.pdf),
[ISO1540 datasheet](https://www.ti.com/lit/ds/symlink/iso1540.pdf),
[TMP117 datasheet](https://www.ti.com/lit/ds/symlink/tmp117.pdf),
[TLV755P datasheet](https://www.ti.com/lit/ds/symlink/tlv755p.pdf).

## Verification and release holds

Run `python tools/validate_pivot_schematic.py`. The audit exports the current
netlist and ERC report, compares retained baseline net membership, checks new
interfaces and isolation-domain assignments, and verifies the PCB hash.
The baseline snapshot is tied to commit `e0909c8`. Generated reports and the
review PDF are in `outputs/` and are ignored by Git.

The project already contains two Nucleo ERC exclusions (missing unit and missing
power unit). They have not been added to or relaxed. KiCad CLI counts these
in its summary even when its detailed report contains zero reported findings.

Before schematic release, resolve:

1. Actual motor/encoder identity, supply current, cable pinout, resolution and maximum frequency.
2. Exact HD15 parts and mating harness; power-terminal, fuse and fuse-holder footprints.
3. Battery maximum voltage, available short-circuit current, upstream fuse, polarity protection and regeneration/disconnect behavior.
4. Measured STR8 input current, acceleration peaks and inrush; then finalize Hall range, filters and fuse coordination.
5. Minimum electronics temperature and thermal control. P1 is not qualified for -50 °C; several selected parts start at -40 °C.
6. Added protected-bus power budget, converter/clamp compatibility and temperature derating.
7. Required measurement accuracy, calibration and external-probe locations.

Layout, routing, PCB parity/DRC, thermal validation, harness testing and bench
qualification have not been performed. No claim of hardware safety or successful
operation follows from ERC or netlist checks.

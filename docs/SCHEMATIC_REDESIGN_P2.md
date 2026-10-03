# P2 schematic - motor encoders, onboard temperature, and Port/Star naming

**Historical revision:** P3 supersedes the temperature circuit, label
presentation, HD15 connector choice, and separate ISO7730F isolators below. See
[SCHEMATIC_REDESIGN_P3.md](SCHEMATIC_REDESIGN_P3.md) for the current DE9 map.
The encoder MCU pin allocations remain applicable.

Date: 2026-10-03. Schematic only; PCB and firmware unchanged.

## Scope

Two motor encoder interfaces supplement the retained SSI channels. External
systems already monitor battery voltage and device current; PSRB can remotely
switch device power. P1's STR8 power/current and voltage sheets have been
removed. Both onboard temperature sensors are retained; their earlier removal
was an assistant error, now corrected. J1 has its original supply connections. U21 still
measures brake currents on AIN0/1; AIN2/3 are unused. The previous current-sensor
range discussion is superseded by removal of those sensors.

F10/F11, the new one-shot encoder fuses, were also removed. Dedicated 5 V
converters now feed the encoder connectors directly. Verify converter overload
behavior, cable ratings, and upstream protection with the external system;
remote power cycling alone does not specify current limiting. Existing baseline
protection is retained.

## Whole-schematic naming and labels

| Previous name | P2 name |
|---|---|
| LH_* | PORT_* |
| RH_* | STAR_* |
| +5V_ENC_L / +5V_ENC_R | +5V_ENC_PORT / +5V_ENC_STAR |
| +6.5V_ENC_L / +6.5V_ENC_R | +6.5V_ENC_PORT / +6.5V_ENC_STAR |

The migration covers root sheet pins, child-sheet ports, local/global signal
labels, power-symbol instances, cached definitions, and the project power
library. It preserves references, part numbers, component values, and footprints.
KiCad's left/right text-alignment settings are unrelated to channel naming.

New encoder signals use hierarchical ports and local labels. Supplies use
arrow/ground power symbols. The longer preset labels were moved into open space
on the STM32 sheet. Electrical verification compares connected component pins
against the baseline independently of names, detecting swaps, splits, or merges.

## MCU allocation

| Signal | Nucleo connection | MCU function |
|---|---|---|
| PORT_ENC_A | CN7 pin 10 / PA5 | TIM2_CH1 AF1 |
| PORT_ENC_B | CN7 pin 15 / PB3 | TIM2_CH2 AF1 |
| PORT_ENC_Z | CN9 pin 16 / PE4 | EXTI4 |
| STAR_ENC_A | CN7 pin 1 / PC6 | TIM3_CH1 AF2 |
| STAR_ENC_B | CN7 pin 11 / PC7 | TIM3_CH2 AF2 |
| STAR_ENC_Z | CN9 pin 22 / PE3 | EXTI3 |

Disable SWO on PB3 and use SWD. Verify loading from the Nucleo PA5 LED-control
input. TIM2 is 32-bit; TIM3 is 16-bit and needs firmware wrap extension. PE6
remains the Star drive fault input. Maximum frequency, filtering, and index
latency depend on actual encoder resolution and motor speed.

## Encoder circuits

Each channel uses an AM26LV32EIDR receiver and ISO7730FDWR three-channel isolator.
Field electronics reference -BATT. The isolator output uses +3V3_STM32 and
GND_STM32; those grounds remain separate.

Each A/B/Z pair has a provisional 120 ohm, 1%, 0.5 W termination and two 560 ohm
bias resistors. Nominal disconnected-cable bias is about 0.319 V before receiver
loading. Confirm cable impedance, drive capability, and bias margin. A shorted
pair does not guarantee a defined logic state. TPD2E2U06QDBZRQ1 arrays provide
signal ESD protection at the connectors.

R-78HB5.0-0.5 converters supply the new encoders from +BATT_Prot. Their 5 V outputs
also feed TLV75533 regulators for the receiver and field side of each isolator.
The new rails are +5V_MOTOR_ENC_PORT/STAR and +3V3_MOTOR_ENC_PORT/STAR, distinct
from the retained SSI supplies. Verify effective input capacitance, total
protected-bus load, the converter's 72 V input limit, minimum-load behavior,
temperature derating, overload behavior, and actual encoder consumption.

Proposed custom J20/J21 HD15 socket mapping:

| Pin | Signal |
|---|---|
| 1 | Dedicated +5 V motor-encoder supply |
| 2, 9 | Field return, -BATT |
| 3 / 4 | A+ / A- |
| 5 / 6 | B+ / B- |
| 7 / 8 | Z+ / Z- |
| 10-15 | NC |
| Shell | PIVOT_CHASSIS |

The user identified NEMA34 motors; the older HT23/ZAA reference is unconfirmed.
This proposed mapping is not approved for direct mating to an existing cable.
Confirm actual hardware and both mating views.

J12 provides the chassis connection on the Port encoder sheet. C188 couples
the shell net to field return; R172 is an unpopulated direct-bond option. The
chassis power flag represents the external chassis connection at J12. Check
bonding against the retained connector-shell arrangement before assembly.

## Onboard temperature retained

U143 and U144 are TMP117AIDRVR devices, restored with their original electrical
roles. U143 is a board-ambient proxy on the MCU supply/ground, address 0x49
(ADD0 tied high). U144 measures the power area on field ground, address 0x4B
(ADD0 tied to field SCL). Both ALERT pins are unused; firmware polls temperatures.
The exposed pads connect to each sensor's local ground. Review assembly stress,
calibration, and thermal placement before layout.

The temperature sheet also contains U140 (TLV75533 field 3.3 V supply), U141
(ISO1540 isolated I2C), R180/R181 (field pull-ups), and local decoupling. The MCU
side shares the original I2C bus and R67/R68 pull-ups with the brake ADC at 0x48.
The field bus and MCU bus remain isolated. Begin at 100 kHz and verify rise time
and low-level margins on both isolation branches.

No voltage/current ADC, divider, or external thermistor input is restored.

## Verification

Run `python tools/validate_pivot_schematic.py`. It exports the KiCad netlist and
ERC report and checks retained pin groups, exact channel renaming, original
component values/footprints, six encoder signals, supplies, isolation domains,
restored J1/U21 connections, both temperature sensors and their addresses,
isolated field supply/bus, and absence of removed P1 components. It also checks
the unchanged PCB hash and the unchanged two inherited Nucleo ERC exclusions.
Baseline data is tied to commit e0909c8.

Final P2 audit: 306 retained baseline net groups preserved, 32 explicit
connection checks passed, original component values/footprints preserved,
zero reported ERC findings with the two existing exclusions unchanged, and
an unchanged PCB SHA-256.

Reports and the 12-sheet review PDF are in outputs/. P1 source before cleanup
is recoverable under _work/before_p2_cleanup/. Both folders are ignored by Git.
The cleanup does not establish layout parity, environmental qualification, or
successful operation on hardware.

## References

- [STM32H723](https://www.st.com/resource/en/datasheet/stm32h723zg.pdf)
- [Nucleo MB1364 manual](https://www.st.com/resource/en/user_manual/um2407-stm32h7-nucleo144-board-stmicroelectronics.pdf)
- [AM26LV32E](https://www.ti.com/lit/ds/symlink/am26lv32e.pdf)
- [ISO7730](https://www.ti.com/lit/ds/symlink/iso7730.pdf)
- [TPD2E2U06-Q1](https://www.ti.com/lit/ds/symlink/tpd2e2u06-q1.pdf)
- [RECOM R-78HB](https://recom-power.com/pdf/Innoline/R-78HB-0.5.pdf)
- [TLV755P](https://www.ti.com/lit/ds/symlink/tlv755p.pdf)
- [TMP117](https://www.ti.com/lit/ds/symlink/tmp117.pdf)
- [ISO1540](https://www.ti.com/lit/ds/symlink/iso1540.pdf)

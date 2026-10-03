# Project handoff - Elevation Pivot Daughter Board

Last updated: 2026-10-03. Current revision: **P3, encoders and passive onboard temperature**.

## Current scope

Retain the working controller and both existing SSI channels. Add two isolated
motor incremental-encoder interfaces and retain two onboard temperature
sensors as simple 1206 thermistors. Work is schematic only; the PCB and
firmware remain unchanged.

The user confirmed that other systems already measure battery voltage and
device current. PSRB can remotely switch device power off and on. P2 removes
the P1 STR8 power distribution, ACS725 sensors, and battery-voltage sensing.
The user explicitly retained the onboard temperature sensors; their earlier
removal was an assistant error, now corrected. External thermistor inputs remain
omitted. Do not restore the removed power/voltage/current functions from P1.

The new one-shot encoder fuses were also removed because they cannot be
replaced during balloon flight. Dedicated encoder supplies remain. Their
overload behavior and upstream protection still need system review; remote
cycling alone does not establish a current limit.

Existing brake current sensing, protection, supply conversion, CAN, stepper
controls/faults, preset signals, and both SSI interfaces are retained. J1 has
its original battery and separate brake-supply connections. U21 AIN2/3 are
now connected to TH1/TH2 on the ADC sheet.

## Naming throughout the schematic

Port replaces the former left/LH channel; Star replaces the former right/RH
channel. This covers all signal labels, hierarchical sheet pins, and supply
nets, including brakes, stepper drives, SSI, and preset circuitry.

Existing SSI supplies are +5V_ENC_PORT, +5V_ENC_STAR, +6.5V_ENC_PORT, and
+6.5V_ENC_STAR. New supplies use +5V_MOTOR_ENC_PORT/STAR and
the shared +3V3_MOTOR_ENC logic rail so they remain distinct from SSI.

The original project, firmware, and unchanged PCB retain historical naming.
Header and MCU-unit encoder signals both use the original hierarchical
label style and 1.27 mm text. Local labels identify internal sheet nets. Supplies use
conventional arrow/ground power symbols.

## Encoder assumptions and implementation

The user identified NEMA34 motors. Earlier notes identified HT23-553D-ZAC,
which conflicts with that description. Actual motor/encoder part numbers,
supply demand, resolution, and installed cable wiring remain unverified.
Earlier HT23/ZAA data is reference material only.

P3 retains the assumed 5 V differential A/B/Z encoders. The user selected DE9
sockets for J20/J21, matching the connector family already used on this board.
Do not assume the proposed pinout matches an existing cable.

DE9 pinout: 1 = +5 V; 2 and 9 = return; 3/4 = A+/A-; 5/6 = B+/B-;
7/8 = Z+/Z-; shell = PIVOT_CHASSIS. Pins 1-9 retain their previous assignments.
The latest drawing update preserves the user's visual edits and adds short,
plain-language role captions beside the main ICs, converters and filter.
The two 5 V converters remain separate; the 3.3 V receiver supply is now shared.

Each interface uses an AM26LV32E receiver, termination/bias, ESD protection,
and a dedicated R-78HB5.0-0.5 encoder supply. One ISO7760FDWR (U101) isolates
all six A/B/Z signals toward the MCU. U105 supplies both receivers and U101's
field side from PS10 through the shared +3V3_MOTOR_ENC rail. U111, U115 and
their redundant capacitors are removed. Losing PS10 disables feedback from
both motor encoders; PS11 still supplies the Star encoder itself.
Field electronics reference -BATT; MCU outputs reference GND_STM32. J12 and
its optional chassis bond are now on the Port encoder sheet.

| Signal | MCU pin | Nucleo connector | Function |
|---|---|---|---|
| Port A | PA5 | CN7 pin 10 | TIM2_CH1 AF1 |
| Port B | PB3 | CN7 pin 15 | TIM2_CH2 AF1 |
| Port Z | PE4 | CN9 pin 16 | EXTI4 |
| Star A | PC6 | CN7 pin 1 | TIM3_CH1 AF2 |
| Star B | PC7 | CN7 pin 11 | TIM3_CH2 AF2 |
| Star Z | PE3 | CN9 pin 22 | EXTI3 |

Disable SWO on PB3; SWD remains available. Verify the Nucleo PA5 LED input
loading. TIM3 is 16-bit and needs firmware counter-wrap handling. PE6 remains
the existing Star drive fault input.

## Files and validation

Onboard temperature: TH1 measures a board-temperature proxy and TH2 measures
the selected power hot spot. Both are two-pad 1206 NTCs (TDK B57621C5103J062),
on the existing ADS1115 sheet. U21 AIN2/3 read their dividers; U24 already provides
I2C isolation. No additional IC, regulator, isolator, address or bus branch is
needed. Both sensors use +5V_BRAKE/GND_BRAKE; readings require that supply.
The separate temperature sheet and U140/U141/U143/U144 have been removed.

Firmware currently reads only AIN0/1. It must add slow temperature sampling,
use +/-6.144 V for AIN2/3, preserve brake-channel gain/cadence, and convert with
TDK curve 1010 plus calibration. Firmware is not changed by this schematic work.

Open Elevation_Pivot_Daughter-Board.kicad_pro in KiCad 9. Read
[SCHEMATIC_REDESIGN_P3.md](docs/SCHEMATIC_REDESIGN_P3.md) for circuits, the proposed
connector pinout, and remaining checks. The local review export is
outputs/Pivot_Schematic_Review.pdf.

Run `python tools/validate_pivot_schematic.py`. It checks retained connectivity,
explicit channel renaming, original component values/footprints, encoder
interfaces, removed P1 circuits, inherited ERC exclusions, and the PCB hash.
Reports are in outputs/. Baseline data is tied to commit e0909c8.

Current verification results are generated in outputs/pivot_validation.json.
The checker preserves 304 baseline net groups; the twelve new encoder pins and
two formerly NC ADC inputs have separate explicit checks. It also checks header
label style, original component values/footprints, and the unchanged PCB hash.
The two inherited ERC exclusions are unchanged. P3 source before cleanup is
recoverable under _work/before_p3/.

P1 source before cleanup is recoverable under _work/before_p2_cleanup/.
That folder and generated outputs are ignored by Git. The historical P1 report
is superseded and must not be treated as active requirements.

## Remaining work

Confirm actual encoder identity and harness, maximum signal frequency, cable
impedance/bias margin, supply demand/overload behavior, chassis bonding, and
minimum electronics temperature. P3 is not qualified for the possible -50 C
flight environment. Layout, PCB parity/DRC, thermal work, and bench testing
remain future work.

The original project at
C:/Users/Mauro/Documents/KiCad/Elevation_Control_STM32_Daughter-Board remains
the as-built hardware, firmware, UI, and test-history reference.
Repository: https://github.com/mauro-starspec/Elevation_Pivot_Daughter-Board.
The unchanged baseline PCB has three known Nucleo courtyard overlaps.

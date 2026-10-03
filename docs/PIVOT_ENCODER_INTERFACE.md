# Dual pivot incremental encoder interfaces

## Selected motors and encoders

**P3 status, 2026-10-03:** the user now describes NEMA34 motors. The earlier
HT23/ZAA identification below is a reference, not a confirmed description of
the installed hardware. Both existing SSI channels are retained. The new
circuits assume 5 V differential A/B/Z. The user selected DE9 for J20/J21;
the custom pinout must
be verified against the actual encoder and cable. See
[`SCHEMATIC_REDESIGN_P3.md`](SCHEMATIC_REDESIGN_P3.md) for the current shared
ISO7760F isolation circuit. Both receivers now share PS10/U105 logic power;
the MCU allocation from P2 is unchanged.

- Motors: two Applied Motion Products `HT23-553D-ZAC` units
- Encoder: Renco ZAA type, Applied Motion legacy part `970-1001`, enclosed by
  the ZAC motor cover
- Motor product: [HT23-553D-ZAC](https://www.applied-motion.com/s/product/eolstep-motor-high-torqueht23553dzac/01t5i000000xz33AAA?name=HT23-553D-ZAC-NEMA-23-High-Torque-Stepper-Motor-w-Encoder-and-Cover)
- Encoder drawing: [Applied Motion 970-1001 Rev C](https://applied-motion.s3.amazonaws.com/documents/2D-Drawing/970-1001_RevC_Renco_ZAA_0.pdf)
- Encoder family data: [Renco R35i](https://www.renco.com/fileadmin/user_upload/renco/1319497-21_Drehgeber_RENCO_en.pdf)

The old motor page is marked end-of-life. Preserve the exact motor and encoder
part numbers in the schematic and BOM so a replacement is not assumed to have
the same connector, pinout, resolution, or temperature range.

## Electrical characteristics of the earlier reference assembly

| Property | Requirement |
|---|---|
| Supply | 5 V ±10% |
| Output format | Differential A+/A−, B+/B−, and Z+/Z− line-driver signals |
| Resolution | 2,000 signal periods/revolution |
| STM32 x4 resolution | 8,000 counts/revolution |
| Shaft resolution | 0.045° per decoded count |
| Index | One marker/index pulse per motor revolution |
| Encoder interface | Differential line driver compatible with RS-422 reception |
| Encoder family operating range | −30 °C to +115 °C |
| Applied Motion encoder | ZAA / legacy `970-1001` |
| Applied Motion extension cable | `3004-195-xx` family |

The previous GBA assumptions—4,000 counts/revolution, 60 kHz maximum, 130 mA,
and the 8-pin JST pinout—do not apply to this motor.

## Connector and harness warning

The ZAA encoder uses a 15-position connector system rather than the GBA's
8-position JST connector. Applied Motion identifies `3004-195-xx` as the WAA,
YAA, and ZAA extension-cable family, with a JAE connector at the encoder and a
high-density 15-pin D-sub at the drive end.

The encoder provides these electrical connections:

| Signal | Function |
|---|---|
| A+, A− | Quadrature channel A differential pair |
| B+, B− | Quadrature channel B differential pair |
| Z+, Z− | Index differential pair |
| +5 V | Encoder power |
| GND | Encoder power return |
| Shield/drain | Cable shield, terminated according to the final EMC plan |

Do not release the PCB or harness from an internet pin table alone. Verify the
actual installed encoder connector and the exact `3004-195-xx` cable drawing
from both mating viewpoints before assigning PCB connector pin numbers.

## Required PCB signal chain

```text
Port A+/A− -> differential receiver -> STM32 Port timer channel 1
Port B+/B− -> differential receiver -> STM32 Port timer channel 2
Port Z+/Z− -> differential receiver -> STM32 Port index/interrupt input

Star A+/A− -> differential receiver -> STM32 Star timer channel 1
Star B+/B− -> differential receiver -> STM32 Star timer channel 2
Star Z+/Z− -> differential receiver -> STM32 Star index/interrupt input
```

The external differential pairs must not be connected directly to normal STM32
GPIO inputs. Select six RS-422-compatible differential receiver channels whose
logic outputs are natively safe for the STM32H723's 3.3 V domain.

The completed dual-channel circuit should provide:

- receiver-end termination for all six differential pairs, derived from the
  encoder, receiver, and actual cable requirements;
- ESD/transient protection with sufficiently low capacitance;
- local receiver and encoder-supply decoupling;
- a filtered 5 V encoder supply sized from the verified ZAA supply-current
  requirement for two encoders plus design margin;
- twisted differential pairs and a documented cable-shield connection;
- labeled test points on the six receiver outputs;
- each encoder's A and B outputs on channels 1 and 2 of the same STM32 timer in
  hardware encoder mode;
- two Z signals on timer index-capable pins or interrupt inputs;
- canonical channel names `Port` and `Star`; P2 completes the channel and
  supply-net rename across the schematic. The original firmware and unchanged
  PCB retain their historical naming until those are separately updated.

## Position interpretation

With x4 quadrature decoding:

```text
motor_shaft_degrees = encoder_counts * 360 / 8000
motor_shaft_degrees = encoder_counts * 0.045
pivot_degrees = motor_shaft_degrees / mechanical_ratio
```

The final mechanical ratio and sign convention must be confirmed from the pivot
mechanism. The count direction can be reversed in firmware, but the schematic,
harness, and software must document one consistent convention.

## Reference limitation

This is an incremental encoder. Its accumulated count is lost when controller
power is removed. Z identifies one location per motor revolution, but it does
not necessarily identify a unique pivot angle after a gearbox. The system still
requires a startup reference strategy, such as a physical pivot reference
sensor, an operator-established zero, or another absolute measurement.

## Decisions still required

- Verify the two physical encoder labels and connectors
- Obtain the installed cable drawing; verify whether the older `3004-195-xx`
  reference applies at all to the NEMA34 assemblies
- Encoder supply current for the actual installed units
- Pivot mechanical reduction ratio and maximum motor speed
- Maximum encoder cable length and shield termination policy
- Verify P2 receiver, termination, and protection choices against the actual encoder
- Verify P2 TIM2/TIM3 and index allocation against required frequency and firmware
- Required behavior following power loss or motion while unpowered

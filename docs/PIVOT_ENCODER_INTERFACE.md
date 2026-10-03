# Pivot incremental encoder interface

## Selected motor and encoder

- Motor: Applied Motion Products `HT23-598D-GBA`
- Encoder family: GBA optical incremental encoder
- Manufacturer datasheet: [925-0070 Rev B](https://applied-motion.s3.amazonaws.com/documents/Datasheets/925-0070_RevB_FBA-GBA-HBA_Encoder_Datasheet.pdf)

## Confirmed electrical characteristics

| Property | Requirement |
|---|---|
| Supply | 5 V ±0.5 V |
| Maximum supply/load current | 130 mA |
| Output format | Differential A/B/Z square waves |
| Resolution | 1,000 lines/revolution; 4,000 quadrature counts/revolution |
| Shaft resolution | 0.09° per decoded count |
| Index | One Z pulse per motor revolution |
| Maximum output frequency | 60 kHz |
| Encoder connector | JST `SM08B-NSHSS-TB` |
| Mating housing | JST `NSHR-08V-S` |

## Encoder pinout

| Pin | Signal |
|---:|---|
| 1 | +5 V |
| 2 | GND |
| 3 | A+ |
| 4 | A− |
| 5 | B+ |
| 6 | B− |
| 7 | Z+ |
| 8 | Z− |

Verify pin numbering and connector viewing direction against the manufacturer
drawing before releasing a harness or PCB.

## Required PCB signal chain

```text
A+/A− -> differential receiver -> STM32 timer channel 1
B+/B− -> differential receiver -> STM32 timer channel 2
Z+/Z− -> differential receiver -> STM32 timer/index input
```

The external differential pairs must not be connected directly to normal STM32
GPIO inputs. Select a 3.3 V-powered RS-422-compatible receiver whose input range
accepts the encoder's 5 V differential driver and whose logic outputs are safe
for the STM32H723. A spare fourth receiver channel is acceptable.

The completed circuit should provide:

- receiver-end termination for A, B, and Z, selected from the encoder/receiver
  datasheets and verified for the actual cable;
- ESD/transient protection suitable for the signal levels and required
  bandwidth;
- local receiver and encoder-supply decoupling;
- a filtered 5 V encoder supply with at least 130 mA available plus design
  margin;
- twisted differential pairs in the harness;
- an intentional shield connection that does not create an uncontrolled return
  path;
- labeled test points on the receiver outputs, and preferably accessible
  differential-pair test locations;
- A and B assignments on channels 1 and 2 of the same STM32 timer configured
  for hardware encoder mode;
- Z on a timer index-capable pin or an interrupt input with documented reset
  behavior.

## Position interpretation

With x4 quadrature decoding:

```text
motor_shaft_degrees = encoder_counts * 360 / 4000
motor_shaft_degrees = encoder_counts * 0.09
pivot_degrees = motor_shaft_degrees / mechanical_ratio
```

The final mechanical ratio and sign convention must be confirmed from the pivot
mechanism. The count direction can be reversed in firmware or by exchanging the
logical A and B channels, but the schematic and harness should use one recorded
convention.

## Reference limitation

This is an incremental encoder. Its accumulated count is lost when controller
power is removed. Z identifies one location per motor revolution, but it does
not necessarily identify a unique pivot angle after a gearbox. The system still
requires a startup reference strategy, such as a physical pivot reference
sensor, an operator-established zero, or another absolute measurement.

## Decisions still required

- Pivot mechanical reduction ratio and maximum motor speed
- Maximum encoder cable length and shield termination policy
- Whether Z is mandatory in the first PCB revision
- Exact differential receiver and protection components
- STM32 timer and pin assignment after a whole-board pin-resource review
- Required behavior following power loss or motion while unpowered

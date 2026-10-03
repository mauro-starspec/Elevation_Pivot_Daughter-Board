# Elevation Pivot Daughter Board

KiCad 9 daughter board for the Starspec elevation/pivot controller.

## Current revision: P3

The schematic adds two isolated motor encoder interfaces while preserving both
SSI channels, two onboard 1206 thermistors, and all existing
controller functions. Port/Star names now apply
throughout the schematic, including brake, stepper, SSI, preset, and supply nets.
New signals use hierarchical labels; supplies use conventional power symbols.

One six-channel ISO7760F isolates both motor encoders' A/B/Z signals. Both
receivers share U105's 3.3 V supply from PS10; loss of PS10 disables both
feedback paths. The two 5 V encoder converters remain separate.

Device power switching belongs to external PSRB. Other systems already measure
battery voltage and device current. The P1 STR8 power/current and voltage
additions have been removed, along with the new one-shot encoder fuses and
external thermistor inputs. Existing brake current sensing is retained.

TH1 measures board temperature and TH2 the power area. Their passive dividers
use the existing U21 ADC's spare AIN2/3 inputs and U24 isolation. No extra sensor
ICs, regulator or I2C isolator are required. Temperature readings depend on the
brake supply. Firmware channel scheduling and conversion remain future work.

The PCB is unchanged and does not match the redesigned schematic. This is a
review revision, not a fabrication release. No firmware was changed.

## Open and review

Open [Elevation_Pivot_Daughter-Board.kicad_pro](Elevation_Pivot_Daughter-Board.kicad_pro)
in KiCad 9. Symbols and footprints are stored locally in the repository.

- [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md): scope and next-session context.
- [SCHEMATIC_REDESIGN_P3.md](docs/SCHEMATIC_REDESIGN_P3.md): foundation review and current circuits.
- [REDESIGN_PLAN.md](docs/REDESIGN_PLAN.md): remaining review sequence.
- outputs/Pivot_Schematic_Review.pdf: local review export, ignored by Git.

Run `python tools/validate_pivot_schematic.py` to check connectivity, channel
renaming, original component values/footprints, encoder interfaces, ERC, and
the unchanged PCB hash. The two inherited Nucleo ERC exclusions remain.

Actual NEMA34 motor/encoder identity, supply demand, maximum frequency, and the
proposed custom DE9 harness must be verified. J20/J21 now use DE9 sockets;
plain-language captions identify the main components. The earlier HT23/ZAA reference
is unconfirmed for this hardware.

The original elevation project remains the firmware and bench-test reference.
The unchanged baseline PCB retains three known courtyard overlaps: H3/CN9,
H4/CN10, and H2/CN7.

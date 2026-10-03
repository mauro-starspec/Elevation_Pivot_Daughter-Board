# Elevation Pivot Daughter Board

KiCad 9 hardware project for the redesigned Starspec elevation/pivot controller
daughter board.

This repository begins from the proven `Elevation_Control_STM32_Daughter-Board`
hardware baseline. The original repository remains unchanged and continues to
hold its firmware, browser tools, recordings, and test history. This repository
contains only the editable PCB design and the documentation needed for the new
hardware revision.

## Open the design

Open [`Elevation_Pivot_Daughter-Board.kicad_pro`](Elevation_Pivot_Daughter-Board.kicad_pro)
in KiCad 9. The hierarchical schematics, project-specific symbols, and custom
footprints are stored in this repository so that the design does not depend on
Mauro's workstation libraries.

## Current status

**Redesign baseline — not ready for fabrication.**

The copied schematic and PCB represent the working elevation-control board
before pivot-specific changes. They are a known starting point, not a released
pivot-board design. In particular, the new HT23-598D-GBA incremental-encoder
input has not yet been placed or routed.

KiCad 9.0.7 baseline validation on 2026-10-02 found **zero ERC findings** and
**zero unconnected PCB pads**. The PCB retains three known courtyard overlaps
between the fixed Nucleo connector/mounting group: H3/CN9, H4/CN10, and H2/CN7.
These must be rechecked against the actual mounting hardware during redesign.

## Redesign objectives

- Preserve the validated STM32, brake, STR8, SSI-encoder, power-protection, CAN,
  and isolation circuits where they remain applicable.
- Add a protected differential A/B/Z receiver interface for the pivot motor's
  embedded GBA incremental encoder.
- Add current measurement for the two external STR8 supplies if it remains part
  of the system architecture.
- Review available STM32 timer pins before assigning the incremental encoder.
- Keep field wiring, grounding, shielding, termination, serviceability, and
  connector keying explicit in the schematic.
- Complete ERC, PCB parity, DRC, fabrication preview, and first-article review
  before release.

See [`docs/PIVOT_ENCODER_INTERFACE.md`](docs/PIVOT_ENCODER_INTERFACE.md) for the
known encoder interface and [`docs/REDESIGN_PLAN.md`](docs/REDESIGN_PLAN.md) for
the controlled redesign sequence.

## Repository contents

```text
Elevation_Pivot_Daughter-Board.kicad_pro  KiCad project
Elevation_Pivot_Daughter-Board.kicad_sch  Top-level schematic
Elevation_Pivot_Daughter-Board.kicad_pcb  Starting PCB layout
*.kicad_sch                               Hierarchical schematic sheets
Project_Symbols/                          Project-local symbol libraries
footprints/                               Project-local footprint libraries
docs/                                     Design requirements and decisions
```

Firmware is deliberately excluded. It remains in the original elevation-control
repository until this board's pin assignment and hardware architecture are
stable enough to justify a dedicated firmware target.

## Source baseline

Imported from `mauro-starspec/Elevation_Control_STM32_Daughter-Board` on
2026-10-02. Preserve the original repository as the as-built and test-history
reference; make pivot redesign changes here.

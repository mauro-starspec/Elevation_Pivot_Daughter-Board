# Pivot daughter-board redesign plan

## 1. Freeze the requirements

- Confirm every retained interface: two brakes, STR8 controls and faults, two
  SSI elevation encoders, CAN, power rails, and any servo-related functions.
- Confirm whether the two pivot motor/encoder channels supplement or replace
  the existing SSI channels.
- Confirm the pivot gear ratio, travel, speed, cable length, connector, and
  reference strategy.
- Route two individually protected STR8 supply branches through appropriately
  ranged ACS725 current sensors.
- Confirm and implement battery/protected-bus voltage measurement.
- Define board-ambient, power-area, and optional external temperature sensing.

## 2. Allocate STM32 resources

- Inventory all used NUCLEO-H723ZG pins.
- Reserve two timers' CH1/CH2 pairs for hardware quadrature decoding.
- Reserve two appropriate Z/index inputs.
- Check conflicts with clocks, debug, UART, SSI, step generation, CAN, and Nucleo
  board functions.
- Record the allocation in a pin table before changing PCB routing.

## 3. Design the encoder front end

- Select and review six differential receiver channels.
- Complete termination, ESD protection, filtering, power, grounding, connector,
  test-point, and shield details.
- Check signal levels, common-mode range, fail-safe behavior, bandwidth, and
  startup state from primary datasheets.
- Add the circuit as its own hierarchical sheet if practical.

## 4. Update the rest of the hardware

- Redesign the complete STR8 power path, protection, current sensing,
  regeneration path, connectors, and copper for two powered branches.
- Add verified battery-voltage and temperature-monitoring circuits.
- Remove functions that are conclusively obsolete rather than leaving confusing
  unpopulated circuitry.
- Recheck power budgets, isolation boundaries, return-current paths, connector
  keying, clearances, and field-fault behavior.

## 5. Validate before layout release

- Schematic review and zero unexplained ERC findings
- Netlist/parity review against the known baseline
- Placement and return-path review
- PCB DRC and copper-current review
- Connector and harness cross-check from both mating viewpoints
- BOM lifecycle and sourcing review
- Fabricator Gerber, drill, BOM, and placement-preview inspection

## 6. Bring-up strategy

- Power-rail and current-limit checks without field loads
- Static differential-input tests using known A/B/Z patterns
- Slow manual shaft rotation with timer counts and direction displayed
- Index repeatability test
- Counts-per-revolution and gear-ratio verification
- Noise test with brakes and STR8 drives independently disabled/enabled
- Only then integrate pivot position into motion supervision

Do not treat the copied PCB as fabrication-ready until this sequence is closed.

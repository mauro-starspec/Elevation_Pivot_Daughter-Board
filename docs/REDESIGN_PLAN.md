> Historical P3 reference. [P4 controller integration](CONTROLLER_STACK_P4.md) supersedes Nucleo, interface-header and unchanged-PCB statements below.

# Pivot daughter-board review plan

Current scope: P3, 2026-10-03. Two motor encoders supplement the existing SSI
channels. Both onboard temperature sensors remain, now as passive 1206 thermistors. Port/Star naming
covers the entire schematic. PSRB handles external
device power control; voltage and device-current measurement exist elsewhere.
P1 power distribution, current/voltage monitoring, and external thermistor
inputs are superseded and removed. Onboard temperature remains in scope.

## Completed schematic work

- Add two protected, isolated differential A/B/Z receiver interfaces.
- Consolidate their six forward signals into U101 ISO7760F, with shared 3.3 V
  receiver power from PS10/U105; remove the second isolator and logic regulator.
- Allocate TIM2/TIM3 quadrature inputs and two index inputs.
- Preserve the controller, brake sensing, drive controls, SSI, and CAN.
- Restore the baseline J1 inlet; use spare ADC inputs for two onboard thermistors.
- Remove the added one-shot encoder fuses.
- Apply Port/Star names to all channel signals and power nets.
- Use hierarchical signal labels and conventional power symbols.
- Add TH1/TH2 on the existing ADC sheet, reusing its supply and isolation.

## Remaining schematic review

1. Identify the actual NEMA34 motor/encoder assemblies and installed cables.
2. Confirm DE9 parts, pinout, mating views, shield bonds, and cable impedance.
3. Check encoder current, converter overload behavior, protected-bus load,
   voltage limits, and temperature derating with the external power system.
4. Check maximum frequency, bias margin, input filtering, timer-wrap handling,
   and index/reference strategy.
5. Confirm minimum electronics temperature, enclosure thermal control, and
   placement/calibration of the two onboard sensors.

Run `python tools/validate_pivot_schematic.py` after schematic changes.
See [SCHEMATIC_REDESIGN_P3.md](SCHEMATIC_REDESIGN_P3.md) for implemented details.

PCB synchronization/layout requires a separate request. Later checks include
return paths, isolation spacing, connector mechanics, DRC, manufacturing outputs,
and first-article testing. Firmware must use the verified encoder resolution
and channel mapping. Temperature firmware must add AIN2/3 with per-channel
gain/scaling, curve 1010 conversion and calibration, retaining brake sampling cadence.

# P6 compact controller

Current revision: 80 x 130 mm, with the SSI and stepper interfaces now on this
board. Four DE9s, plus Ethernet, USB and SWD. Components use both faces.
Open `Elevation_Controller.kicad_pro`. Only mate with the P6 carrier.
See [current handoff](../PROJECT_HANDOFF.md) and [assembly notes](../assembly/README.md).

The following source-integration notes are historical P4/P5 context; the P6
manifest overrides their board split, connector locations and pinout.

---

# Elevation STM32H723 controller

Open `Elevation_Controller.kicad_pro` in KiCad 9. This is the upper board of the
P4 elevation/pivot stack. It uses shared Stack symbols/footprints in the parent
repository; keep that directory structure intact.

Derived from `mauro-starspec/stm32h723-controller` commit `2328ccb`. Core MCU,
Ethernet, USB-C, SWD/VCP, power and watchdog circuits are retained. Generic
expansion is replaced by the elevation interface on `07_stack_interface.kicad_sch`.

J30/J31 headers mount underneath. The carrier supplies isolated 5 V; this board
supplies shared 3.3 V logic. USB VBUS does not power it. Use an external ST-LINK
for SWD; there is no Nucleo ST-LINK processor on this board.

PCB: unrouted draft, not for manufacture. See the parent
[handoff](../PROJECT_HANDOFF.md), [integration review](../docs/CONTROLLER_STACK_P4.md)
and [assembly notes](../assembly/README.md).

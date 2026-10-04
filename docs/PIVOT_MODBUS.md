# Pivot servo Modbus - P4.1 schematic provision

The user requires Modbus for the pivot servo. This revision assumes **Modbus RTU
over two-wire, half-duplex RS-485**. The servo drive model has not been supplied,
so its electrical variant, cable assignment and register map are unconfirmed.
The circuit is on carrier sheet `Pivot_Modbus.kicad_sch` (page 12). CAN remains.

## Circuit and board interface

U160 ISO1410DWR combines the isolation barrier and RS-485 transceiver in a wide
SOIC-16. Its logic side uses existing +3V3_STM32 / GND_STM32; its bus side uses
existing +5V_FIELD / -BATT. No new supply or one-shot fuse is added. The cable
common shares battery field return, while the MCU stays in the isolated domain.
The selected part supports up to 500 kbit/s; the actual rate follows the drive.
See the [TI ISO1410 datasheet](https://www.ti.com/lit/ds/symlink/iso1410.pdf).

| Signal | J31 on both boards | STM32H723ZGT6 | Function |
|---|---|---|---|
| PIVOT_MODBUS_TX | 13 | PD5, pad 119 | USART2_TX, AF7 |
| PIVOT_MODBUS_RX | 14 | PD6, pad 122 | USART2_RX, AF7 |
| PIVOT_MODBUS_DE | 18 | PD4, pad 118 | USART2_RTS_DE, AF7 |

These three J31 contacts were ground in P4. Both boards must use P4.1.
Thirteen ground contacts remain; all power contacts and original signals stay.
Connectors, mounting holes and all existing PCB component positions are unchanged.
Pin functions and package pads follow the
[ST STM32H723 datasheet](https://www.st.com/resource/en/datasheet/stm32h723zg.pdf),
tables 7 and 9. PD8/PD9 debug serial remains independent.

DE and active-low /RE are tied. R162=10k pulls DE low during reset so the bus
driver is off and the receiver listens. R160/R161=10k pull TX/RX high; the RX
pull-up maintains UART idle while the receiver is disabled for transmission.
C160/C162=100n and C161/C163=1u provide local bypass on the two isolated domains.

## Cable, polarity and configuration

J22 is a DE9 female connector, following the two-wire pin assignment in section
3.5.1 of the [Modbus Serial Line V1.02 guide](https://www.modbus.org/file/secure/modbusoverserial.pdf).

| J22 contact | Connection |
|---|---|
| 1 | Common, -BATT |
| 5 | D1 (+), U160 A / pin 12 |
| 9 | D0 (-), U160 B / pin 13 |
| Shell / mounting pad 0 | PIVOT_CHASSIS |
| 2, 3, 4, 6, 7, 8 | Not connected |

The guide calls positive D1 "B"; TI calls its positive transceiver terminal "A".
Use D1(+)/D0(-) and the drive manual to avoid an A/B naming reversal. Use a twisted
pair plus a common conductor and shield. This connector does not provide power
and is not interchangeable with the motor-encoder or RS-232 wiring.

| Link | Closed, default | Open |
|---|---|---|
| JP160 and JP161 together | R163/R164=560 ohm bias pair enabled | Both open if another device supplies bias |
| JP162 | R165=120 ohm, 1%, 0.5 W termination enabled | Board is not a cable end |

These are copper-bridged solder links, with no removable shunts. Enable bias
at one location and termination at both physical cable ends. At nominal 5 V,
two 120-ohm terminations and the 560-ohm pair give about +0.254 V differential
idle bias before receiver loading. This is a point-to-point design calculation;
confirm the drive input loading and any installed bias/termination.

U160 includes bus ESD protection. Keep its isolation gap free of copper, place
the bypass capacitors at the supply pins, and route the differential pair with
short stubs. Actual cable EMC, chassis bonding and insulation spacing require
layout review and bench testing.

## Supply allocation and firmware work

Allocate approximately 170 mA extra from +5V_FIELD: U160's 160 mA maximum at
500 kbit/s with a 54-ohm load, plus bias/load allowance. Allocate 6 mA from the
3.3 V logic rail. These are design allocations, not measured operation. PS5 is
the existing nominal 5 V / 0.5 A converter; verify its total simultaneous load,
including the CAN supply, drive logic, temperature derating and startup before
layout release. [PS5 manufacturer data](https://www.we-online.com/components/products/datasheet/173950575.pdf).

Firmware has not been changed. Configure USART2 AF7 with active-high automatic
DE, and set assertion/deassertion delays to accommodate the transceiver. Wait
for UART transmission completion before releasing the bus; use the required RTU
silent interval and the drive's baud, framing, address, function codes, timeouts
and register map. Motor command scaling and communication-loss behavior must
come from the actual servo manual.

Before connecting a motor, verify idle polarity, reset and power-cycle behavior,
both terminations, a simple register read, and TX-to-RX turnaround with a scope.
Do not assume any motion command or fault-response register until the drive is known.

## Validation

`python tools/validate_stack.py` verifies both ERC reports, every stack contact,
the actual MCU pads, DE-/RE connection, default biases, supply separation,
connector polarity and termination/bias paths. It also compares pre-Modbus net
groups against `docs/validation/p41_pre_modbus.json` and confirms all nine original
field sheets are unchanged. Both draft PCBs match their netlists; the 15 added
parts are staged outside the carrier outline. Placement and routing remain open.

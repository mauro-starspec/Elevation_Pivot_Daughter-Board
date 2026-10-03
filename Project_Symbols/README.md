# Reviewed schematic symbols

`Electrical_Reviewed.kicad_sym` preserves the placed symbols' graphics, pin numbers, names and positions while correcting ERC electrical types. The schematic caches match this project-local library. It also preserves the PS1/PS5 and PS4 variants that previously differed from their library copies.

The September 2026 schematic cleanup checked these corrections against manufacturer documentation:

| Device | Correction and source |
|---|---|
| ISO6762 family | Ground pins 8/9 are power inputs. [TI](https://www.ti.com/lit/ds/symlink/iso6762-q1.pdf) |
| TPS7A2450 | Pins 1/2 are power inputs, 3 enable input, 4 NC, 5 power output. [TI](https://www.ti.com/lit/ds/symlink/tps7a24.pdf) |
| TPS1H100B | VS/GND inputs, control inputs, power outputs, CL/CS outputs and NC pins corrected. [TI](https://www.ti.com/lit/ds/symlink/tps1h100-q1.pdf) |
| LTC4364 | OUT is a voltage-sense input; FLT and ENOUT are open-drain outputs. [Analog Devices](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4364-1-4364-2.pdf) |
| R05CTE05S-R | Input/output supply types and DNC pin 10 corrected; SGND pins passive. One power-output pin represents each duplicated output rail, with its parallel pin passive. [RECOM](https://g.recomcdn.com/media/Datasheet/pdf/.fRwx-AHZ/.t138d12ed72264b8dfdd1/Datasheet-515/RxxCTExxS.pdf) |
| R-78HB6.5-0.5 | VIN/GND power inputs and VOUT power output. [RECOM](https://recom-power.com/pdf/Innoline/R-78HB-0.5.pdf) |
| SUM80090E, SSM3K361R | Passive discrete-MOSFET pin types. Pin numbering unchanged. [Vishay](https://www.vishay.com/docs/64434/sum80090e.pdf), [Toshiba](https://toshiba.semicon-storage.com/info/docget.jsp?did=36685&prodName=SSM3K361R) |
| STPS3H100, TPD1E10B09 | Passive diode/protection-device pin types. [ST](https://www.st.com/resource/en/datasheet/stps3h100.pdf), [TI](https://www.ti.com/lit/ds/symlink/tpd1e10b09.pdf) |
| J1, FL1 | Connector and common-mode choke pins are passive; neither generates power. |

In `NUCLEOH723ZG.kicad_sym`, hidden ground pins stacked on a visible power-input pin are passive to avoid unintended global aliases such as `GND_CN9`. Their visible counterpart remains a power input; pin numbering and connectivity are preserved.

The placed `NUCLEOH723ZG_Daughterboard_Interface` symbol represents CN7–CN11 only, in five contiguous units. CN12/CN3/CN4/CN15/CN16 are external Nucleo connectors outside this daughterboard interface. All 116 previously placed pins retain their electrical types, numbers, names and positions. Only symbols used by this project and their inherited bases are packaged; the original full-board symbol remains in Git history. The user confirmed the USB/E5V power-jumper arrangement; the schematic records it. No ERC exclusions or severity changes were introduced. Renumbering the five units changes the generated names of 67 unused U1 pin nets, with no connection changes.

Twelve added PWR_FLAGs declare the existing J1 supply/return entries, the protected battery rail, Q16-referenced GND_FLOAT, the filtered PS4 return, post-F1/F2 brake supplies and post-FB1/FB2/FB3 rails. They describe source paths for ERC; they do not bypass fuses, filters, isolation or Q16 and do not assert that switched supplies are always on.

Verification: ERC 61 → 0, identical membership of all 318 nets, zero PCB opens and zero schematic-parity findings. The PCB is unchanged. This review does not qualify power capacity, component stress or thermal behavior; the Nucleo jumper must match the selected power source.

Project library tables use relative paths. Used standard KiCad definitions and vendor libraries are included alongside the reviewed variants; unused symbols were omitted. Standard KiCad library sources: https://gitlab.com/kicad/libraries/kicad-symbols and https://gitlab.com/kicad/libraries/kicad-footprints. Optional 3D models are not bundled.

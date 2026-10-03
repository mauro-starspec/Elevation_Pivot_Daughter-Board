"""Audit P3 encoders and passive onboard temperature sensing; never edit the PCB.

Run: python tools/validate_pivot_schematic.py
Requires KiCad 9 kicad-cli (PATH or the standard Windows installation).
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "Elevation_Pivot_Daughter-Board"
OUT = ROOT / "outputs"
CLI = shutil.which("kicad-cli") or "C:/Program Files/KiCad/9.0/bin/kicad-cli.exe"


def run(*args):
    subprocess.run([CLI, *args], cwd=ROOT, check=True, capture_output=True, text=True)


def main():
    OUT.mkdir(exist_ok=True)
    run("sch", "export", "netlist", "--format", "kicadxml", "-o",
        str(OUT / "pivot_redesign.xml"), PROJECT + ".kicad_sch")
    run("sch", "erc", "--format", "json", "--severity-all", "-o",
        str(OUT / "pivot_erc.json"), PROJECT + ".kicad_sch")
    erc = json.loads((OUT / "pivot_erc.json").read_text())
    violations = [v for s in erc["sheets"] for v in s["violations"]]
    assert not violations, violations

    doc = ET.parse(OUT / "pivot_redesign.xml").getroot()
    nets = {n.attrib["name"]: {(p.attrib["ref"], p.attrib["pin"]) for p in n}
            for n in doc.find("nets")}
    by_pin = {p: name for name, pins in nets.items() for p in pins}
    baseline = json.loads((ROOT / "docs/validation/baseline_net_membership.json").read_text())
    baseline_pins = {tuple(p) for ps in baseline["nets"].values() for p in ps}
    allocations = {
        "PORT_ENC_A": ("CN7", "10", "CN7_10", "U101", "15"),
        "PORT_ENC_B": ("CN7", "15", "CN7_15", "U101", "14"),
        "STAR_ENC_A": ("CN7", "01", "CN7_1", "U101", "12"),
        "STAR_ENC_B": ("CN7", "11", "CN7_11", "U101", "11"),
        "PORT_ENC_Z": ("CN9", "16", "CN9_16", "U101", "13"),
        "STAR_ENC_Z": ("CN9", "22", "CN9_22", "U101", "10"),
    }
    allowed = set()
    for cn, pad, mpad, _, _ in allocations.values():
        allowed.update({(cn, pad), ("U1", mpad)})
    # These two formerly NC inputs now read onboard thermistors.
    allowed.update({("U21", "6"), ("U21", "7")})
    retained = baseline_pins - allowed
    checked = 0
    renamed = {}

    def port_star(name):
        return name.replace("LH_", "PORT_").replace("RH_", "STAR_").replace("ENC_L", "ENC_PORT").replace("ENC_R", "ENC_STAR")

    for old_name, ps in baseline["nets"].items():
        old = {tuple(p) for p in ps} & retained
        if not old:
            continue
        actual_names = {by_pin[p] for p in old}
        assert len(actual_names) == 1, ("split baseline net", old_name, actual_names)
        new_name = actual_names.pop()
        assert nets[new_name] & retained == old, ("merged baseline net", old_name, new_name)
        # Check the naming migration independently of connectivity. Automatic
        # Net-(...) names can change with symbol presentation; explicit names
        # must follow the exact Port/Star mapping.
        if port_star(old_name) != old_name:
            assert new_name == port_star(old_name), ("incorrect channel name", old_name, new_name)
            renamed[old_name] = new_name
        checked += 1

    checks = []

    def on(name, *pins):
        assert set(pins) <= nets[name], (name, set(pins) - nets[name])
        checks.append(name + ": " + ", ".join(f"{r}.{p}" for r, p in pins))

    for name, (cn, pad, mpad, isolator, opad) in allocations.items():
        actual = by_pin[(isolator, opad)]
        assert actual.rsplit("/", 1)[-1] == name, (name, actual)
        on(actual, (cn, pad), ("U1", mpad), (isolator, opad))
    for i, side in enumerate(("PORT", "STAR")):
        rx, iso = f"U{100+i*10}", "U101"
        enc = f"J{20+i}"
        for jp, rp in ((3, 2), (4, 1), (5, 6), (6, 7), (7, 10), (8, 9)):
            assert by_pin[(enc, str(jp))] == by_pin[(rx, str(rp))]
        for j, rp in enumerate((3, 5, 11)):
            ip = str(2 + i*3 + j)
            on(by_pin[(rx, str(rp))], (rx, str(rp)), (iso, ip))
        on("-BATT", (iso, "8"), (rx, "8"), (enc, "2"))
        on("GND_STM32", (iso, "9"))
        on("+3V3_STM32", (iso, "16"))
        on("+5V_MOTOR_ENC_" + side, (f"PS{10+i}", "3"), (enc, "1"))
        on("+3V3_MOTOR_ENC", ("U105", "5"), (rx, "16"), (iso, "1"))
        on("PIVOT_CHASSIS", (enc, "0"), ("J12", "1"), ("R172", "1"), ("C188", "1"))

    on("+BATT", ("J1", "1"))
    on("-BATT", ("J1", "2"), ("R172", "2"), ("C188", "2"))
    on("+BATT_Prot", ("PS10", "1"), ("PS11", "1"))
    on("+5V_MOTOR_ENC_PORT", ("U105", "1"), ("U105", "3"))
    on("+3V3_MOTOR_ENC", ("C114", "1"), ("C115", "1"), ("C116", "1"), ("C145", "1"))
    on("+3V3_STM32", ("C117", "1"))
    on("GND_STM32", ("C117", "2"))
    on("-BATT", ("C114", "2"), ("C115", "2"), ("C116", "2"), ("C145", "2"))
    assert "+3V3_MOTOR_ENC_PORT" not in nets and "+3V3_MOTOR_ENC_STAR" not in nets
    on("+24V_BRAKE", ("J1", "3"))
    on("GND_BRAKE", ("J1", "4"), ("U21", "3"))
    assert len({by_pin[p] for p in (("U21", "3"), ("J20", "2"), ("U101", "9"))}) == 3
    components = {c.attrib["ref"]: c for c in doc.find("components")}
    assert components["U101"].findtext("value") == "ISO7760FDWR"
    assert components["U101"].findtext("footprint") == "Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm"
    assert not {"U111", "U115", "C143", "C144", "C146", "C147"} & components.keys()
    for ref in ("J20", "J21"):
        assert components[ref].findtext("value") == "DE9 FEMALE", ref
        assert components[ref].findtext("footprint") == (
            "Connector_Dsub:DSUB-9_Socket_Horizontal_P2.77x2.84mm_"
            "EdgePinOffset7.70mm_Housed_MountingHolesOffset9.12mm"), ref
        assert {p for r, p in by_pin if r == ref} == {str(p) for p in range(10)}, ref
        assert by_pin[(ref, "9")] == "-BATT", (ref, "second return")
    removed = {"U130", "U131", "U132", "U140", "U141", "U142", "U143", "U144", "U145",
               "F10", "F11", "F20", "F21", "J8", "J9", "J10", "J11", "J22", "J23"}
    assert not removed & components.keys(), ("Removed P1 circuits remain", removed & components.keys())
    # Two passive thermistors, the original ADC, and its original isolation.
    for i, signal in enumerate(("TEMP_BOARD", "TEMP_POWER")):
        th, lower, series, cap = f"TH{i+1}", f"R{180+i}", f"R{182+i}", f"C{190+i}"
        assert components[th].findtext("value") == "10k NTC / 1206"
        assert components[th].findtext("footprint") == "Resistor_SMD:R_1206_3216Metric"
        assert components[lower].findtext("value") == "10k 0.1%"
        assert components[series].findtext("value") == "1k"
        assert components[cap].findtext("value") == "100n"
        on("+5V_BRAKE", (th, "1"), ("U21", "8"))
        on("GND_BRAKE", (lower, "2"), (cap, "2"), ("U21", "3"))
        divider = {(th, "2"), (lower, "1"), (series, "1")}
        assert nets[by_pin[(th, "2")]] == divider
        on(by_pin[(th, "2")], *sorted(divider))
        measured = {(series, "2"), (cap, "1"), ("U21", str(6+i))}
        name = by_pin[("U21", str(6+i))]
        assert name.rsplit("/", 1)[-1] == signal
        assert nets[name] == measured
        on(name, *sorted(measured))
    assert "+3V3_PIVOT_FIELD" not in nets
    assert not (ROOT / "Pivot_Temperature.kicad_sch").exists()
    # Prevent the exact screenshot regression: both representations of each MCU
    # signal must use the same hierarchical input labels and original text size.
    mcu = (ROOT / "STM32.kicad_sch").read_text()
    for name in allocations:
        assert not re.search(r'\((?:label|global_label)\s+"'+name+r'"', mcu), name
        pattern = (r'\(hierarchical_label\s+"'+name+r'"\s+\(shape input\)'
                   r'\s+\(at [^)]*\)\s+\(effects\s+\(font\s+\(size 1\.27 1\.27\)')
        assert len(re.findall(pattern, mcu)) == 2, (name, "header label style differs")
    for name in nets:
        assert not re.search(r"(?:LH_|RH_|ENC_L(?:$|/)|ENC_R(?:$|/))", name), name
    # Original component values and footprints must survive the cleanup.
    physical = ROOT / "docs/validation/baseline_components.json"
    for ref, expected in json.loads(physical.read_text()).items():
        c = components[ref]
        assert c.findtext("value", "") == port_star(expected["value"]), (ref, "value changed")
        assert c.findtext("footprint", "") == expected["footprint"], (ref, "footprint changed")

    # Baseline layout is deliberately not synchronized with this schematic revision.
    pcb = ROOT / (PROJECT + ".kicad_pcb")
    actual_hash = hashlib.sha256(pcb.read_bytes()).hexdigest()
    assert actual_hash == baseline["pcb_sha256"], "PCB changed since the frozen baseline"
    project = json.loads((ROOT / (PROJECT + ".kicad_pro")).read_text())
    assert project["erc"]["erc_exclusions"] == baseline["erc_exclusions"], "ERC exclusions changed"
    report = {
        "erc_reported_errors_and_warnings": len(violations),
        "inherited_erc_exclusions": len(baseline["erc_exclusions"]),
        "preserved_baseline_net_groups": checked,
        "renamed_nets": renamed,
        "explicit_checks": checks,
        "components": len(doc.find("components")),
        "pcb_sha256_unchanged": actual_hash,
        "status": "PASS - schematic connectivity; not hardware or fabrication qualification",
    }
    (OUT / "pivot_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS: {checked} baseline net groups preserved; {len(checks)} connection checks; "
          "0 reported ERC findings; PCB unchanged.")


if __name__ == "__main__":
    main()

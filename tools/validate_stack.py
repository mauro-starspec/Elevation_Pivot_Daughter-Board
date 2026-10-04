"""Export and audit the two P4 schematics, their preservation and PCB mating.

Run with ordinary Python: python tools/validate_stack.py
Requires KiCad 9, sexpdata and KiCad's bundled Python/pcbnew on Windows.
This is a schematic/mechanical check, not a fabrication release check.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

from kicad_sexp import read, kids, one, prop, library, pins, instance
from update_bom_fields import without_metadata, sx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
CLI = shutil.which('kicad-cli') or 'C:/Program Files/KiCad/9.0/bin/kicad-cli.exe'
PROJECTS = {'controller': 'controller/Elevation_Controller',
            'elevation': 'Elevation_Pivot_Daughter-Board'}


def netlist(path):
    d = ET.parse(path).getroot()
    comps = {c.get('ref'): {'value': c.findtext('value'),
             'footprint': c.findtext('footprint')} for c in d.find('components')}
    nets = {n.get('name'): {(p.get('ref'), p.get('pin')) for p in n}
            for n in d.find('nets')}
    by_pin = {p: name for name, ps in nets.items() for p in ps}
    return comps, nets, by_pin


def preserve_groups(old, new, retained):
    """Catch both splits and unintended shorts; net names may change with hierarchy."""
    projected = {frozenset(tuple(p) for p in ps if tuple(p) in retained)
                 for ps in old.values()}
    projected.discard(frozenset())
    actual = {frozenset(ps & retained) for ps in new.values()}
    actual.discard(frozenset())
    assert projected == actual, {'missing_groups': [sorted(s) for s in projected-actual],
                                 'unexpected_groups': [sorted(s) for s in actual-projected]}
    return len(projected)


def main():
    OUT.mkdir(exist_ok=True)
    data = json.loads((ROOT/'assembly/stack_interface.json').read_text())
    baseline = json.loads((ROOT/'docs/validation/p4_source_baselines.json').read_text())
    exports = {}
    report = {'revision': data['revision'], 'erc': {}, 'checks': []}
    for name, project in PROJECTS.items():
        for args in [('sch', 'export', 'netlist', '--format', 'kicadxml', '-o',
                      f'outputs/p4_{name}.xml', project+'.kicad_sch'),
                     ('sch', 'erc', '--format', 'json', '--severity-all', '-o',
                      f'outputs/p4_{name}_erc.json', project+'.kicad_sch')]:
            subprocess.run([CLI, *args], cwd=ROOT, check=True, capture_output=True)
        erc = json.loads((OUT/f'p4_{name}_erc.json').read_text())
        violations = [v for s in erc['sheets'] for v in s['violations']]
        assert not violations, (name, violations)
        pro = json.loads((ROOT/(project+'.kicad_pro')).read_text())
        assert not pro.get('erc',{}).get('erc_exclusions'), name
        report['erc'][name] = {'violations': 0, 'exclusions': 0}
        exports[name] = netlist(OUT/f'p4_{name}.xml')

    ec, en, ep = exports['elevation']
    cc, cn, cp = exports['controller']
    removed = {'U1','CN7','CN8','CN9','CN10','CN11','H1','H2','H3','H4'}
    retained_refs = set(baseline['elevation']['components']) - removed
    modbus_refs = {'U160','J22','R160','R161','R162','R163','R164','R165',
                   'C160','C161','C162','C163','JP160','JP161','JP162'}
    assert set(ec) == retained_refs | {'J30','J31','H30','H31','H32','H33','TP30'} | modbus_refs
    for ref in retained_refs:
        assert ec[ref] == baseline['elevation']['components'][ref], ref
    retained = {tuple(p) for ps in baseline['elevation']['nets'].values()
                for p in ps if p[0] in retained_refs}
    report['preserved_carrier_net_groups'] = preserve_groups(
        baseline['elevation']['nets'], en, retained)
    # BOM properties now live in the schematics. The drawing baseline was
    # captured only after checking all nine original byte hashes before migration.
    drawing = json.loads((ROOT/'docs/validation/bom_drawing_baseline.json').read_text())
    for file in baseline['field_sheet_sha256']:
        digest = hashlib.sha256(sx.dumps(without_metadata(read(ROOT/file))).encode()).hexdigest()
        assert digest == drawing['schematic_sha256'][file], file
    report['field_sheets_drawing_preserved'] = sorted(baseline['field_sheet_sha256'])

    # All original retained controller component selections, except these explicit edits.
    changed = {'C221': '1u', 'R104': '2.21k 1%', 'TP103': 'SYS_5V'}
    for ref in set(cc) & set(baseline['controller']['components']):
        expected = dict(baseline['controller']['components'][ref])
        if ref in changed: expected['value'] = changed[ref]
        assert cc[ref] == expected, (ref, cc[ref], expected)

    aliases = {'GND':'GND_STM32', 'B2B_5V_IN':'+5V_STM32',
               '3V3_DIG':'+3V3_STM32', 'NRST':'CTRL_NRST'}
    def short(name): return name.rsplit('/',1)[-1]
    contacts = 0
    for ref, conn in data['connectors'].items():
        for pin, signal in conn['pins'].items():
            assert short(cp[(ref,pin)]) == signal, (ref,pin,cp[(ref,pin)],signal)
            assert short(ep[(ref,pin)]) == aliases.get(signal, signal), (ref,pin,ep[(ref,pin)])
            contacts += 1
    assert contacts == 50
    assert len({s['mcu_pad'] for s in data['application_signals']}) == 32
    for signal in data['application_signals']:
        assert short(cp[('U1',signal['mcu_pad'])]) == signal['signal'], signal
    report['matched_contacts'] = contacts
    report['application_gpio'] = len(data['application_signals'])

    # Independent P4 snapshot catches changes to any pre-existing circuit.
    pre_modbus = json.loads((ROOT/'docs/validation/p41_pre_modbus.json').read_text())
    report['pre_modbus_net_groups_preserved'] = {}
    for name, (components, nets, bypin) in exports.items():
        old = pre_modbus[name]
        for ref, selection in old['components'].items():
            assert components[ref] == selection, (name, ref)
        changed_pins = {('J31','13'), ('J31','14'), ('J31','18')}
        if name == 'controller':
            changed_pins |= {('U1','118'), ('U1','119'), ('U1','122')}
        preserved_pins = {tuple(p) for ps in old['nets'].values() for p in ps} - changed_pins
        report['pre_modbus_net_groups_preserved'][name] = preserve_groups(old['nets'], nets, preserved_pins)

    # End-to-end UART, reset behavior, bus polarity, power/isolation and cable.
    for contact, pad, signal, ic_pin in [('13','119','PIVOT_MODBUS_TX','6'),
            ('14','122','PIVOT_MODBUS_RX','3'), ('18','118','PIVOT_MODBUS_DE','5')]:
        assert cp[('U1',pad)] == cp[('J31',contact)] == signal
        assert ep[('U160',ic_pin)] == ep[('J31',contact)]
    assert ep[('U160','4')] == ep[('U160','5')] == ep[('R162','1')]
    assert ep[('R162','2')] == 'GND_STM32'
    for ref, pin in [('R160','6'),('R161','3')]:
        assert ep[(ref,'1')] == '+3V3_STM32'
        assert ep[(ref,'2')] == ep[('U160',pin)]
    assert ep[('U160','1')] == '+3V3_STM32'
    assert ep[('U160','16')] == '+5V_FIELD'
    assert ep[('U160','2')] == ep[('U160','8')] == 'GND_STM32'
    assert ep[('U160','9')] == ep[('U160','15')] == ep[('J22','1')] == '-BATT'
    plus, minus = ep[('U160','12')], ep[('U160','13')]
    assert plus != minus
    assert plus == ep[('J22','5')] == ep[('JP160','1')] == ep[('R165','1')]
    assert minus == ep[('J22','9')] == ep[('R164','1')] == ep[('JP162','1')]
    assert ep[('R163','1')] == '+5V_FIELD'
    assert ep[('JP161','1')] == '-BATT'
    for resistor, link in [('R163','JP160'),('R164','JP161'),('R165','JP162')]:
        assert ep[(resistor,'2')] == ep[(link,'2')]
    assert ep[('J22','0')] == ep[('J20','0')] == 'PIVOT_CHASSIS'
    for ref,rail,gnd in [('C160','+3V3_STM32','GND_STM32'),('C161','+3V3_STM32','GND_STM32'),
                         ('C162','+5V_FIELD','-BATT'),('C163','+5V_FIELD','-BATT')]:
        assert ep[(ref,'1')] == rail and ep[(ref,'2')] == gnd
    for ref,value in [('U160','ISO1410DWR'),('R160','10k'),('R161','10k'),('R162','10k'),
                      ('R163','560R 1%'),('R164','560R 1%'),('R165','120R 1% 0.5W')]:
        assert ec[ref]['value'] == value, ref
    assert sum(net=='GND' for c in data['connectors'].values() for net in c['pins'].values()) == 13
    mb = read(ROOT/'Pivot_Modbus.kicad_sch')
    nc_positions_mb = {tuple(one(n,'at')[1:3]) for n in kids(mb,'no_connect')}
    for ref, numbers in [('U160',['7','10','11','14']),('J22',['2','3','4','6','7','8'])]:
        inst=instance(mb,ref); pin_positions=pins(library(mb,inst),inst)
        for number in numbers: assert pin_positions[number] in nc_positions_mb, (ref,number)
    report['modbus'] = {'uart':'USART2 / AF7','tx':'PD5 / pad 119','rx':'PD6 / pad 122',
        'de':'PD4 / pad 118','transceiver':'ISO1410DWR','connector':'J22: 1=Common, 5=D1(+), 9=D0(-)',
        'new_components':len(modbus_refs),'remaining_stack_ground_contacts':13}

    # Remaining independent anchors protect field polarity, temperature and isolation.
    for ref in ['TH1','TH2','U21','U24','J20','J21','U100','U110','U101','PS10','PS11']:
        assert ref in ec
    assert ep[('U101','9')] == 'GND_STM32'
    assert ep[('U101','8')] == '-BATT'
    assert ep[('U21','6')] == ep[('R182','2')]
    assert ep[('U21','7')] == ep[('R183','2')]
    assert len({ep[('U101','9')],ep[('U101','8')],ep[('U21','3')]}) == 3
    assert cp[('J30','25')] == cp[('U101','5')] == 'B2B_5V_IN'
    assert cp[('U101','6')] == cp[('U202','2')] == 'SYS_5V'
    assert cp[('J30','29')] == cp[('U1','17')] == '3V3_DIG'
    assert cp[('U1','33')] == cp[('FB201','2')] == '3V3_ANA'
    assert cp[('FB201','1')] == '3V3_DIG'
    assert cp[('J31','19')] == cp[('U1','25')] == 'NRST'
    assert cp[('U1','133')] == 'PORT_ENC_B'  # PB3 must not drive SWO.
    assert 'R603' not in cc
    assert cc['R104']['value'] == '2.21k 1%'
    assert 'INA181' not in ' '.join(c['value'] for c in cc.values())
    assert not any(r in cc for r in ['J701','J801','U203','U204','U205','U206','U901','U903'])

    # Preserve source Ethernet, USB, crystals, reset, watchdog and SWD net identities at MCU.
    core_baseline = {tuple(p):n for n,ps in baseline['controller']['nets'].items() for p in ps}
    internal = ['23','24','8','9','25','138','35','36','27','43','44','45','126','128','74',
                '101','103','104','105','109','77','78','141','56','71','106','32']
    for pad in internal:
        assert cp[('U1',pad)] == core_baseline[('U1',pad)], (pad,cp[('U1',pad)],core_baseline[('U1',pad)])
    report['preserved_internal_mcu_connections'] = len(internal)

    # MCU pins must be explicitly connected or explicitly marked NC, never silently floating.
    doc = read(ROOT/'controller/03_mcu_core.kicad_sch')
    mcu = instance(doc,'U1')
    all_pins = pins(library(doc,mcu),mcu)
    assert len(all_pins) == 144
    names = {one(q,'number')[1]:one(q,'name')[1] for group in kids(library(doc,mcu),'symbol') for q in kids(group,'pin')}
    for signal in data['application_signals']:
        assert names[signal['mcu_pad']].startswith(signal['mcu_gpio']), signal
    nc_positions = {tuple(one(n,'at')[1:3]) for n in kids(doc,'no_connect')}
    for pad,pos in all_pins.items():
        assert ('U1',pad) in cp or pos in nc_positions, (pad,pos)
    assert data['board_gap_mm'] == 12
    insertion = 2.54+5.84+8.51+.13-data['board_gap_mm']
    assert 3.68 <= insertion <= 6.35
    report['connector_insertion_mm'] = round(insertion,2)
    report['checks'] += ['All 144 MCU pins accounted for', 'Field domains remain separate',
                         'Carrier component values and footprints preserved',
                         'Controller internal MCU functions preserved',
                         'No unused analog/digital expansion or current-monitor ICs']
    pcb_python = Path(CLI).parent/'python.exe'
    subprocess.run([str(pcb_python),str(ROOT/'tools/validate_stack_pcb.py')],cwd=ROOT,check=True)
    report['pcb'] = json.loads((OUT/'p4_pcb_validation.json').read_text())
    (OUT/'p4_stack_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    if json.loads((ROOT/'assembly/stack_interface.json').read_text()).get('revision')=='P6':
        import runpy
        runpy.run_path(str(ROOT/'tools/validate_compact_all.py'),run_name='__main__')
    else:main()

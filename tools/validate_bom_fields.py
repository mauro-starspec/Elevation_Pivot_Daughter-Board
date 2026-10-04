"""Validate native KiCad purchasing fields and preservation after the BOM pass.

Run validate_stack.py first to refresh the electrical exports and ERC reports.
The native schematic properties remain the BOM source of truth.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re

from kicad_sexp import read, kids, one
from update_bom_fields import fields, schematics, PROJECTS, ALIASES, without_metadata, sx, table_settings
from validate_stack import netlist

ROOT = Path(__file__).resolve().parents[1]


def main():
    baseline = json.loads((ROOT/'docs/validation/bom_drawing_baseline.json').read_text())
    report = {'schematics_checked': 0, 'boards': {}, 'pcb_geometry_unchanged': True}
    for filename, expected in baseline['schematic_sha256'].items():
        actual = hashlib.sha256(sx.dumps(without_metadata(read(ROOT/filename))).encode()).hexdigest()
        assert actual == expected, filename
        report['schematics_checked'] += 1
    # P5 explicitly authorizes board placement changes after the BOM pass.
    # Keep the historical byte-preservation assertion for pre-P5 geometry only.
    mechanical=json.loads((ROOT/'assembly/stack_interface.json').read_text())
    if mechanical.get('mechanical_revision','').startswith('P5'):
        report.pop('pcb_geometry_unchanged')
        report['pcb_geometry_scope']='P5 placement authorized; use validate_stack and validate_placement for PCB checks'
    else:
        for filename, expected in baseline['pcb_sha256'].items():
            assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest() == expected, filename
    for board, project in PROJECTS.items():
        records = {}
        for p in schematics(ROOT/(project+'.kicad_sch')):
            for n in kids(read(p), 'symbol'):
                f = fields(n)
                if f.get('Reference', '#').startswith('#'):
                    continue
                ref = f['Reference']
                assert ref not in records, (board, ref)
                records[ref] = f
                for key in ['Manufacturer', 'MPN', 'LCSC', 'Operating Temperature',
                            'Assembly', 'Function', 'BOM Status', 'Temp Status']:
                    assert f.get(key), (board, ref, key)
                for canonical, aliases in ALIASES.items():
                    for alias in aliases:
                        if alias in f:
                            assert f[canonical] == f[alias], (board, ref, alias)
                if f['Assembly'].startswith('PCB feature'):
                    assert str(one(n, 'in_bom')[1]) == 'no', (board, ref)
                if str(one(n, 'dnp')[1]) == 'yes':
                    assert f['Assembly'] == 'DNP - not purchased', (board, ref)
        pro = json.loads((ROOT/(project+'.kicad_pro')).read_text())
        assert pro['schematic']['bom_settings'] == table_settings()
        assert table_settings() in pro['schematic']['bom_presets']
        # This local snapshot additionally checks names/pins and all other
        # project settings against the state immediately before the migration.
        backup = ROOT/'_work/before_bom_fields_20261003'
        if backup.exists():
            original = json.loads((backup/(project+'.kicad_pro')).read_text())
            for cfg in (pro, original):
                for key in ('bom_settings', 'bom_presets'):
                    cfg.get('schematic', {}).pop(key, None)
            assert pro == original, board
            export = 'elevation' if board == 'Carrier' else 'controller'
            assert netlist(backup/(export+'.xml')) == netlist(ROOT/f'outputs/p4_{export}.xml'), board
        fitted = [f for f in records.values() if f['Assembly'] == 'FIT']
        report['boards'][board] = {
            'references': len(records),
            'assembly_counts': dict(Counter(f['Assembly'] for f in records.values())),
            'fitted_with_MPN': sum(not f['MPN'].startswith('NOT SELECTED') for f in fitted),
            'fitted_with_C_code': sum(bool(re.fullmatch(r'C\d+', f['LCSC'])) for f in fitted),
            'temperature_unverified': [f['Reference'] for f in fitted if f['Operating Temperature'] == 'UNVERIFIED'],
            'preset': 'Project BOM',
        }
    report['checks'] = ['All drawing/electrical structure preserved',
                        'PCB preservation check follows active mechanical revision',
                        'Native field aliases agree', 'PCB features excluded from purchasing',
                        'DNP flags retained', 'Native table presets configured']
    dest = ROOT/'docs/validation/bom_fields_review_results.json'
    dest.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

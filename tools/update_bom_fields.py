"""Populate the two projects' native KiCad Symbol Fields Tables.

No external BOM is the source of truth. This migration reads current symbol
fields and the reviewed supplement, then edits only properties and PCB-feature
BOM membership. It preserves the rest of each schematic byte for byte.
Run without arguments for a dry run; --apply writes after making a snapshot.
"""
from pathlib import Path
from collections import Counter
import argparse
import copy
import hashlib
import json
import re
import shutil

from kicad_sexp import sx, kids, one, prop

ROOT = Path(__file__).resolve().parents[1]
DATE = '2026-10-03'
BACKUP = ROOT / '_work' / 'before_bom_fields_20261003'
OUT = ROOT / 'outputs' / 'bom_fields'
PROJECTS = {'Carrier': 'Elevation_Pivot_Daughter-Board',
            'Controller': 'controller/Elevation_Controller'}
CORE = ('Reference', 'Value', 'Footprint')
ALIASES = {'MPN': ('MPN', 'MANUFACTURER_PART_NUMBER', 'Manufacturer_Part_Number', 'MP'),
           'Manufacturer': ('Manufacturer', 'Manufacturer_Name', 'MANUFACTURER', 'MF'),
           'LCSC': ('LCSC', 'LCSC Part #')}
COPY_FIELDS = ['Manufacturer', 'LCSC', 'Datasheet', 'Operating Temperature',
               'Temp Min (degC)', 'Temp Max (degC)', 'Temp Basis', 'Temp Source',
               'JLCPCB Library', 'JLCPCB Stock Snapshot', 'DigiKey Part #',
               'DigiKey Status', 'Supplier Data Checked', 'Dielectric', 'Voltage',
               'Tolerance', 'Power', 'TCR', 'Height']


def fields(node):
    return {p[1]: str(p[2]) for p in kids(node, 'property')}


def alias(f, key):
    return next((f[k] for k in ALIASES[key] if f.get(k) not in (None, '', 'N/A', 'None')), '')


def spans(text):
    """Immediate child expressions of one S-expression, respecting strings."""
    level = 0
    quoted = escaped = False
    start = None
    for i, c in enumerate(text):
        if quoted:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == '"':
                quoted = False
            continue
        if c == '"':
            quoted = True
        elif c == '(':
            if level == 1:
                start = i
            level += 1
        elif c == ')':
            level -= 1
            if level == 1:
                yield start, i + 1
    assert level == 0 and not quoted


def schematics(root):
    paths = []
    def visit(p):
        if p in paths:
            return
        paths.append(p)
        d = sx.loads(p.read_text(encoding='utf-8-sig'))
        for sheet in kids(d, 'sheet'):
            visit(p.parent / prop(sheet, 'Sheetfile')[2])
    visit(root)
    return paths


def pcb_feature(f):
    fp = f.get('Footprint', '')
    return fp.startswith(('TestPoint:TestPoint_Pad_', 'Jumper:SolderJumper',
                          'MountingHole:', 'Connector_Wire:SolderWire-'))


def normalize(f, n, board, catalog, cfg):
    result = {}
    for key in ALIASES:
        result[key] = alias(f, key)
    ref = f['Reference']
    is_dnp = bool(kids(n, 'dnp') and str(one(n, 'dnp')[1]) == 'yes')
    if pcb_feature(f):
        result.update({'MPN': 'N/A', 'Manufacturer': 'N/A', 'LCSC': 'N/A',
                       'Assembly': 'PCB feature - no purchased component',
                       'Function': 'PCB mounting hole' if ref.startswith('H') else
                                   'Wire solder pad; wire belongs to harness BOM' if ref == 'J12' else
                                   'PCB solder jumper' if ref.startswith('JP') else 'PCB test pad',
                       'Operating Temperature': 'N/A', 'Temp Min (degC)': 'N/A',
                       'Temp Max (degC)': 'N/A', 'Temp Basis': 'PCB feature',
                       'Temp Status': 'N/A', 'BOM Status': 'PCB FEATURE',
                       'JLCPCB Status': 'N/A'})
        if ref.startswith('H3'):
            result['BOM Review'] = 'Hole only. Four shared 12 mm supports per stack; support material, screws and washers are not selected here.'
        return result

    selected = cfg['selections'].get(board, {}).get(ref)
    if selected:
        assert not result['MPN'] or result['MPN'] == selected, (board, ref, result['MPN'], selected)
        result['MPN'] = selected
    mpn = result['MPN']
    donor = catalog.get(mpn, {})
    for key in COPY_FIELDS:
        if not f.get(key) and donor.get(key):
            result[key] = donor[key]
    if not result['Manufacturer']:
        result['Manufacturer'] = donor.get('Manufacturer', '')
    if not result['LCSC']:
        result['LCSC'] = donor.get('LCSC', '')

    supplement = cfg['parts'].get(mpn, {})
    result.update(supplement)
    combined = f | result
    if mpn.startswith(('TSW-', 'SSW-')):
        result.update({'Manufacturer': 'Samtec', 'Datasheet': 'https://suddendocs.samtec.com/productspecs/tsw-ssw.pdf',
                       'Temp Min (degC)': '-55', 'Temp Max (degC)': '125',
                       'Temp Basis': 'Operating with gold contacts',
                       'Temp Source': 'https://suddendocs.samtec.com/productspecs/tsw-ssw.pdf',
                       'Temp Checked': DATE, 'Temp Status': 'Manufacturer rating recorded; system requirement pending',
                       'Function': ('Male' if mpn.startswith('TSW') else 'Female') + ' stacking connector, ' + ('30' if '-115-' in mpn else '20') + ' contacts',
                       'Footprint Status': 'Paired geometry checked; physical mating approval pending',
                       'BOM Review': 'Verify 12 mm stack engagement and soldering process. TSW is not specified for lead-free wave soldering; review hand-solder process or HTSW equivalent before assembly.' if mpn.startswith('TSW') else 'Verify physical mating at the planned 12 mm stack gap.'})
    if supplement.get('Temp Min (degC)'):
        result.update({'Temp Source': supplement.get('Temp Source', supplement['Datasheet']), 'Temp Checked': DATE,
                       'Temp Status': supplement.get('Temp Status', 'Manufacturer rating recorded; system requirement pending')})
    if supplement.get('Supplier Source'):
        result['Supplier Data Checked'] = DATE
        result['JLCPCB Status'] = ('Exact catalog match; stock not verified' if 'jlcpcb.com' in supplement['Supplier Source']
                                   else 'LCSC exact match; JLC assembly availability unverified')
        result.setdefault('JLCPCB Library', 'UNVERIFIED')
    else:
        result['JLCPCB Status'] = ('Historical ID; recheck exact part and assembly availability' if re.fullmatch(r'C\d+', result['LCSC'])
                                  else 'No verified JLCPCB ID; source or consign')
        result.setdefault('Supplier Data Checked', combined.get('Supplier Data Checked') or 'UNDATED legacy record')
        result.setdefault('Supplier Source', combined.get('Supplier Source') or 'Legacy schematic record; exact supplier listing verification pending')
    combined = f | result
    mn, mx = combined.get('Temp Min (degC)', ''), combined.get('Temp Max (degC)', '')
    if not re.fullmatch(r'-?\d+(?:\.\d+)?', mn):
        m = re.search(r'(-?\d+)\s*to\s*\+?(\d+)', combined.get('Operating Temperature', ''))
        if m:
            mn, mx = m.groups()
            result.update({'Temp Min (degC)': mn, 'Temp Max (degC)': mx,
                           'Temp Basis': combined.get('Temp Basis') or 'Legacy rating; ambient/junction basis unverified',
                           'Temp Source': combined.get('Temp Source') or 'Legacy schematic field; primary-source verification pending'})
    if re.fullmatch(r'-?\d+(?:\.\d+)?', mn) and re.fullmatch(r'-?\d+(?:\.\d+)?', mx):
        result['Operating Temperature'] = f'{mn} to +{mx} C'
        if 'Junction' in (f | result).get('Temp Basis', ''):
            result['Operating Temperature'] += ' (Tj)'
        if 'derating' in (f | result).get('Temp Basis', '').lower():
            result['Operating Temperature'] += ' (derated)'
        result.setdefault('Temp Status', 'Inherited rating; system requirement pending')
    else:
        result.setdefault('Operating Temperature', 'UNVERIFIED' if not is_dnp else 'NOT SELECTED - DNP')
        result.setdefault('Temp Min (degC)', 'UNVERIFIED' if not is_dnp else 'N/A')
        result.setdefault('Temp Max (degC)', 'UNVERIFIED' if not is_dnp else 'N/A')
        result.setdefault('Temp Basis', 'Primary-source verification pending')
        result.setdefault('Temp Status', 'UNVERIFIED' if not is_dnp else 'NOT_EVALUATED_DNP')
    result['Assembly'] = 'DNP - not purchased' if is_dnp else 'FIT'
    result.setdefault('LCSC', '')
    if not result['LCSC']:
        result['LCSC'] = 'UNVERIFIED' if mpn else 'NOT SELECTED'
    if not mpn:
        result['MPN'] = 'NOT SELECTED - DNP' if is_dnp else 'NOT SELECTED'
        result['Manufacturer'] = 'NOT SELECTED'
    result.setdefault('Function', combined.get('Function') or f.get('Description') or
                      ('Capacitor' if ref.startswith('C') else 'Resistor' if ref.startswith('R') else f['Value']))
    result.setdefault('BOM Status', 'DNP' if is_dnp else 'REVIEW: missing MPN' if not mpn else
                      'REVIEW: temperature evidence' if 'UNVERIFIED' in result.get('Temp Status', '') else
                      'PART IDENTIFIED; sourcing/footprint review pending')
    result.setdefault('Footprint Status', combined.get('Footprint_Status') or 'Assigned; drawing/pad verification pending')
    if selected and not supplement.get('Function'):
        # Donor data are part-specific. Its old application notes are not copied.
        result['Function'] = f.get('Description') or ('Decoupling capacitor' if ref.startswith('C') else 'Resistor')
    if mpn == '5747844-4':
        result['Description'] = '9-pin D-SUB connector, socket (female), right angle, mounting holes'
    if board == 'Carrier' and ref == 'PS5':
        result['BOM Status'] = 'HOLD: 5 V supply architecture review'
    if board == 'Carrier' and ref in ('F1', 'F2'):
        result['BOM Status'] = 'REVIEW: legacy brake fuse versus no-fuse preference'
        result['BOM Review'] = 'Existing brake fuse retained. Resolve against user preference for recoverable power protection before procurement.'
    if board == 'Carrier' and ref == 'U14':
        result['BOM Status'] = 'REVIEW: -CT procurement suffix versus -R value'
        result['BOM Review'] = 'Keep current procurement field R05CTE05S-CT and schematic value R05CTE05S-R distinct until packaging equivalence is verified.'
    if is_dnp:
        result['BOM Status'] = 'DNP'
    # Preserve existing consumers while making MPN and LCSC the visible columns.
    for canonical, aliases in ALIASES.items():
        for key in aliases:
            if key in f:
                result[key] = result[canonical]
    return {k: str(v) for k, v in result.items()}


def patch_symbol(text, updates, feature):
    node = sx.loads(text)
    positions = {}
    edits = []
    for a, b in spans(text):
        sub = sx.loads(text[a:b])
        if str(sub[0]) == 'property':
            positions[sub[1]] = (a, b)
        elif feature and str(sub[0]) == 'in_bom' and str(sub[1]) != 'no':
            edits.append((a, b, '(in_bom no)'))
    for key, value in updates.items():
        if key in CORE:
            raise ValueError('Drawing/electrical field change forbidden: ' + key)
        if key in positions:
            a, b = positions[key]
            sub = text[a:b]
            match = re.match(r'(\(property\s+"(?:\\.|[^"\\])*"\s+)("(?:\\.|[^"\\])*")', sub)
            assert match, key
            if sx.loads(sub)[2] != value:
                edits.append((a + match.start(2), a + match.end(2), json.dumps(value, ensure_ascii=False)))
        else:
            x, y = one(node, 'at')[1:3]
            s = '\n  (property ' + json.dumps(key) + ' ' + json.dumps(value, ensure_ascii=False)
            s += f' (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))'
            edits.append((len(text)-1, len(text)-1, s))
    for a, b, replacement in sorted(edits, key=lambda e: (e[0], e[1]), reverse=True):
        text = text[:a] + replacement + text[b:]
    # Inserting before the original closing parenthesis can leave its indent
    # on an otherwise empty line; remove only that insertion artifact.
    text = re.sub(r'\n[ \t]+\n(?=  \(property )', '\n', text)
    return text


def without_metadata(doc):
    d = copy.deepcopy(doc)
    for n in kids(d, 'symbol'):
        n[:] = [p for p in n if not (isinstance(p, list) and p and
               (str(p[0]) == 'in_bom' or str(p[0]) == 'property' and p[1] not in CORE))]
    return d


def table_settings():
    visible = ['Reference', '${QUANTITY}', 'Value', 'Function', 'Manufacturer', 'MPN',
               'LCSC', 'Operating Temperature', 'Assembly', 'BOM Status', 'Footprint',
               'Datasheet', 'BOM Review']
    details = ['Temp Min (degC)', 'Temp Max (degC)', 'Temp Basis', 'Temp Source', 'Temp Checked',
               'Temp Status', 'JLCPCB Library', 'JLCPCB Status', 'Supplier Source',
               'Supplier Data Checked', 'Voltage', 'Dielectric', 'Tolerance', 'Power',
               'TCR', 'Height', 'Footprint Status', 'BOM Notes', 'DigiKey Part #',
               '${DNP}', '${EXCLUDE_FROM_BOM}']
    group = {'Value', 'MPN', 'Manufacturer', 'Footprint', 'Assembly', 'LCSC', 'BOM Status',
             'Operating Temperature', 'Function', 'BOM Review'}
    return {'name': 'Project BOM', 'exclude_dnp': False, 'include_excluded_from_bom': False,
            'group_symbols': True, 'filter_string': '', 'sort_asc': True, 'sort_field': 'Reference',
            'fields_ordered': [{'name': k, 'label': 'Qty' if k == '${QUANTITY}' else k,
                                'show': k in visible, 'group_by': k in group}
                               for k in visible + details]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    cfg = json.loads((ROOT/'docs/bom_field_updates.json').read_text())
    inventory = {}
    catalog = {}
    for board, project in PROJECTS.items():
        for p in schematics(ROOT/(project+'.kicad_sch')):
            raw = p.read_bytes().decode('utf-8-sig')
            doc = sx.loads(raw)
            inventory[p] = (board, raw, doc)
            for n in kids(doc, 'symbol'):
                f = fields(n)
                mpn = alias(f, 'MPN')
                if mpn:
                    item = catalog.setdefault(mpn, {})
                    for key in COPY_FIELDS:
                        value = alias(f, key) if key in ALIASES else f.get(key, '')
                        if value and not item.get(key):
                            item[key] = value
    changed, summary = {}, {}
    all_records = []
    for p, (board, raw, doc) in inventory.items():
        edits = []
        for a, b in spans(raw):
            if not re.match(r'\(symbol\s', raw[a:b]):
                continue
            node = sx.loads(raw[a:b]); f = fields(node)
            if f.get('Reference', '#').startswith('#'):
                continue
            update = normalize(f, node, board, catalog, cfg)
            result = patch_symbol(raw[a:b], update, pcb_feature(f))
            if result != raw[a:b]:
                edits.append((a, b, result))
            all_records.append({'Board': board, 'Reference': f['Reference'],
                                'Value': f['Value'], 'Footprint': f.get('Footprint', ''), **update})
        edited = raw
        for a, b, replacement in reversed(edits):
            edited = edited[:a] + replacement + edited[b:]
        assert without_metadata(doc) == without_metadata(sx.loads(edited)), p
        if edited != raw:
            changed[p] = edited
    for board, project in PROJECTS.items():
        p = ROOT/(project+'.kicad_pro')
        pro = json.loads(p.read_text())
        settings = table_settings()
        pro.setdefault('schematic', {})['bom_settings'] = settings
        presets = pro['schematic'].setdefault('bom_presets', [])
        presets[:] = [v for v in presets if v.get('name') != settings['name']] + [settings]
        # Other project configuration, including board rules, is preserved.
        changed[p] = json.dumps(pro, indent=2, ensure_ascii=False) + '\n'
        records = [r for r in all_records if r['Board'] == board]
        fitted = [r for r in records if r.get('Assembly') == 'FIT']
        summary[board] = {'references': len(records), 'fitted_parts': len(fitted),
                          'fitted_with_MPN': sum(r['MPN'] != 'NOT SELECTED' for r in fitted),
                          'fitted_with_C_code': sum(bool(re.fullmatch(r'C\d+', r['LCSC'])) for r in fitted),
                          'temperature_unverified': [r['Reference'] for r in fitted if r['Operating Temperature'] == 'UNVERIFIED'],
                          'holds': {r['Reference']: r['BOM Status'] for r in fitted if 'HOLD' in r['BOM Status']},
                          'assembly_counts': dict(Counter(r['Assembly'] for r in records))}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'proposed_fields.json').write_text(json.dumps(all_records, indent=2), encoding='utf-8')
    if args.apply:
        if not BACKUP.exists():
            BACKUP.mkdir(parents=True)
            for p in list(inventory) + [ROOT/(v+'.kicad_pro') for v in PROJECTS.values()]:
                target = BACKUP/p.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target)
            for label in ('controller', 'elevation'):
                shutil.copy2(ROOT/f'outputs/p4_{label}.xml', BACKUP/f'{label}.xml')
            hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in [ROOT/(v+'.kicad_pcb') for v in PROJECTS.values()]}
            (BACKUP/'pcb_hashes.json').write_text(json.dumps(hashes, indent=2))
        for p, contents in changed.items():
            p.write_bytes(contents.encode('utf-8'))
    summary['mode'] = 'APPLIED' if args.apply else 'DRY RUN'
    summary['changed_files'] = len(changed)
    (OUT/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()

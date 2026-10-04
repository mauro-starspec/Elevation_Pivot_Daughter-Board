"""Independent P6 assembled-netlist preservation audit (including stack wiring)."""
from pathlib import Path
import json,collections,xml.etree.ElementTree as ET
from validate_stack import netlist
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'_work/p6_baseline';OUT=ROOT/'outputs/compact'
from prepare_compact_baseline import ensure_baseline
ensure_baseline()
m=json.loads((ROOT/'assembly/compact_manifest.json').read_text())
lookup={(x['source_board'],x['source_ref']):(x['board'],x['ref']) for x in m['reference_mapping']}
old={b:netlist(BASE/(b+'.xml')) for b in ['controller','elevation']}
new={b:netlist(OUT/(b+'.xml')) for b in old}
def groups(data,remap=False):
    parent={}
    def find(x):
        parent.setdefault(x,x)
        if parent[x]!=x:parent[x]=find(parent[x])
        return parent[x]
    for b,(_,ns,_) in data.items():
        for n in ns:find((b,n))
    for r,count in [('J30',30),('J31',20)]:
        for i in range(1,count+1):
            a=('controller',data['controller'][2][r,str(i)]);b=('elevation',data['elevation'][2][r,str(i)])
            parent[find(a)]=find(b)
    out=collections.defaultdict(set)
    for b,(_,ns,_) in data.items():
        for n,ps in ns.items():
            for ref,pin in ps:
                if ref in ['J30','J31']:continue
                dest=lookup[b,ref] if remap else (b,ref)
                out[find((b,n))].add((*dest,pin))
    return {frozenset(v) for v in out.values() if v}
expected=groups(old,True);actual=groups(new)
missing=expected-actual;extra=actual-expected
if missing or extra:
    (OUT/'net_difference.json').write_text(json.dumps({'missing':[sorted(g) for g in missing],'extra':[sorted(g) for g in extra]},indent=2))
assert not missing and not extra,('assembled nets changed',len(missing),len(extra),'see outputs/compact/net_difference.json')
for (b,r),(nb,nr) in lookup.items():
    a=old[b][0][r];z=dict(new[nb][0][nr]);z['footprint']=z['footprint'].removeprefix('Field_')
    assert a==z,(b,r,a,z)
oldxml={b:{c.get('ref'):c for c in ET.parse(BASE/(b+'.xml')).getroot().find('components')} for b in old}
newxml={b:{c.get('ref'):c for c in ET.parse(OUT/(b+'.xml')).getroot().find('components')} for b in old}
for (b,r),(nb,nr) in lookup.items():
    def fields(c):
        return {q.get('name'):(q.text or '') for q in c.findall('fields/field') if q.get('name') not in ['Reference','Footprint','Sheetname','Sheetfile']}
    assert fields(oldxml[b][r])==fields(newxml[nb][nr]),(b,r,'BOM metadata changed')
report={'revision':'P6 compact','preserved_checkpoint':'29b4387','preserved_assembled_net_groups':len(actual),
        'all_503_component_values_and_footprints_preserved':True,'native_BOM_metadata_preserved':True,'erc':{},'moved_parts':sum(x['source_board']!=x['board'] for x in m['reference_mapping'])}
for pr in ['controller/Elevation_Controller','Elevation_Pivot_Daughter-Board']:
    before=json.loads((BASE/(pr+'.kicad_pro')).read_text())
    now=json.loads((ROOT/(pr+'.kicad_pro')).read_text())
    for key in ['bom_settings','bom_presets']:assert before['schematic'][key]==now['schematic'][key],(pr,key)
report['native_BOM_presets_preserved']=True
for b in new:
    erc=json.loads((OUT/(b+'_erc.json')).read_text());v=[v for s in erc['sheets'] for v in s['violations']]
    assert not v,(b,v)
    report['erc'][b]={'violations':0,'parts':len(new[b][0])}
(ROOT/'docs/validation/p6_electrical_results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

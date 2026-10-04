"""Independent P5 placement audit, using KiCad's bundled Python.

No routing/fabrication approval is implied by these geometry and identity checks.
"""
from pathlib import Path
import json, hashlib, collections, math, sys
import pcbnew as p
sys.path.insert(0,'C:/Users/Mauro/AppData/Roaming/Python/Python314/site-packages')
from kicad_sexp import read, kids, one

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/placement'
SNAP=ROOT/'_work/before_placement_20261003'
PROJECTS={'controller':'controller/Elevation_Controller','elevation':'Elevation_Pivot_Daughter-Board'}
data=json.loads((ROOT/'assembly/stack_interface.json').read_text())
report={'mechanical_revision':'P5 placement only','board_dimensions_mm':[120,200],'boards':{}}

def xy(v):return (p.ToMM(v.x),p.ToMM(v.y))
def box(f):
    b=f.GetBoundingBox(False,False) if isinstance(f,p.FOOTPRINT) else f.GetBoundingBox()
    return tuple(p.ToMM(v) for v in (b.GetLeft(),b.GetTop(),b.GetRight(),b.GetBottom()))
def overlap(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
def signature(f):
    return {'value':f.GetValue(),'footprint':f.GetFPIDAsString(),'attributes':f.GetAttributes(),
            'pads':sorted((q.GetNumber(),q.GetNetname(),tuple(sorted(xy(q.GetSize()))),
                           tuple(sorted(xy(q.GetDrillSize()))),q.GetAttribute()) for q in f.Pads())}

boards={}
for boardname,project in PROJECTS.items():
    board=p.LoadBoard(str(ROOT/(project+'.kicad_pcb')));boards[boardname]=board
    fps={f.GetReference():f for f in board.GetFootprints()}
    before=p.LoadBoard(str(SNAP/(project+'.kicad_pcb')))
    original={f.GetReference():f for f in before.GetFootprints()}
    assert set(fps)==set(original),boardname
    for ref,f in fps.items():assert signature(f)==signature(original[ref]),(boardname,ref,'component/pad identity changed')
    assert not list(board.GetTracks()),boardname
    assert not list(board.Zones()),boardname
    doc=read(ROOT/(project+'.kicad_pcb'))
    edge=[g for g in kids(doc,'gr_rect') if one(g,'layer')[1]=='Edge.Cuts']
    assert len(edge)==1 and one(edge[0],'start')[1:]==[20,20] and one(edge[0],'end')[1:]==[140,220],boardname
    rectangles={r:box(f) for r,f in fps.items()}
    collisions=[(r,s) for i,(r,a) in enumerate(rectangles.items()) for s,b in list(rectangles.items())[i+1:] if overlap(a,b)]
    assert not collisions,(boardname,collisions)
    for ref,f in fps.items():
        if not ref.startswith('J'):
            x0,y0,x1,y1=rectangles[ref]
            assert x0>=20 and y0>=20 and x1<=140 and y1<=220,(boardname,ref,'body outside outline')
        for q in f.Pads():
            x0,y0,x1,y1=box(q)
            assert x0>=20 and y0>=20 and x1<=140 and y1<=220,(boardname,ref,q.GetNumber(),'pad outside outline')
    supports={r:xy(f.GetPosition()) for r,f in fps.items() if r.startswith('H')}
    for ref,(x,y) in supports.items():
        for other,bb in rectangles.items():
            if other!=ref:assert not overlap((x-4,y-4,x+4,y+4),bb),(boardname,ref,other,'support envelope')
    drc=json.loads((OUT/(boardname+'_drc.json')).read_text())
    allowed={'lib_footprint_mismatch','drill_out_of_range','clearance'} if boardname=='controller' else set()
    # The only residual clearances are internal to inherited TPS25947 footprint.
    for v in drc['violations']:
        assert v['type'] in allowed,(boardname,v)
        if v['type']=='clearance':
            assert all('of U101 ' in item['description'] for item in v['items']),v
        if v['type']=='drill_out_of_range':
            assert all('of U401' in item['description'] for item in v['items']),v
    report['boards'][boardname]={'footprints':len(fps),'tracks_and_vias':0,'copper_zones':0,
         'footprint_envelope_overlaps':0,'support_clearance_mm':8,
         'drc_findings':dict(collections.Counter(v['type'] for v in drc['violations'])),
         'unconnected_items':len(drc.get('unconnected_items',[])),
         'all_pads_within_outline':True,'original_parts_pad_nets_and_DNP_preserved':True}

fps={f.GetReference():f for f in boards['controller'].GetFootprints()}
def distance_to_pad(ref,pin,cap):
    source=next(q for q in fps[ref].Pads() if q.GetNumber()==pin)
    candidates=[q for q in fps[cap].Pads() if q.GetNetname()==source.GetNetname()]
    assert candidates,(ref,pin,cap)
    x,y=xy(source.GetPosition())
    return min(math.hypot(x-xy(q.GetPosition())[0],y-xy(q.GetPosition())[1]) for q in candidates)
checks={}
for ref,pin,cap,limit in [('U202','2','C212',3),('U202','7','C214',4),('U202','8','C214',4),
                         ('U1','71','C20',4),('U1','106','C21',4),
                         ('U401','7','R407',5),('U401','8','R406',5),
                         ('U401','11','R408',5),('U401','14','R409',5)]:
    d=distance_to_pad(ref,pin,cap);assert d<=limit,(ref,pin,cap,d,limit)
    checks[f'{ref}.{pin} to {cap}']=round(d,3)
report['critical_pin_to_component_distances_mm']=checks
def pin_y(ref,number):
    return xy(next(q for q in fps[ref].Pads() if q.GetNumber()==number).GetPosition())[1]
# The two critical buck capacitors face their corresponding pins without
# requiring the two future connections to cross one another.
assert (pin_y('U202','2')-pin_y('U202','1'))*(pin_y('C212','1')-pin_y('C212','2'))>0
assert (pin_y('U202','7')-pin_y('U202','8'))*(pin_y('C214','1')-pin_y('C214','2'))>0
report['buck_capacitor_pin_order_for_direct_connections']=True

snapshot=json.loads((SNAP/'schematic_hashes.json').read_text())
for filename,digest in snapshot.items():assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==digest,filename
report['schematic_files_byte_preserved']=len(snapshot)
report['stack_contract']='50 mating pads and four support pairs independently checked by validate_stack.py'
report['limits']=['Unrouted: unconnected items are intentional at this stage.',
                  'Controller retains 117 library mismatches and inherited U101 clearance / U401 thermal-hole rule findings; no exclusions added.',
                  'Exact footprint release, final isolation/routing, impedance, thermal/vacuum design and cable/enclosure fit remain open.']
(ROOT/'docs/validation/p5_placement_results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

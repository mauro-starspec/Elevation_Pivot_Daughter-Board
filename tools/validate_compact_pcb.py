"""P6 physical audit, using native KiCad data rather than placement reports."""
from pathlib import Path
import sys,json,collections,math
sys.path.insert(0,'C:/Users/Mauro/AppData/Roaming/Python/Python314/site-packages')
import pcbnew as p
from validate_stack import netlist
from kicad_sexp import read,kids,one
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/compact'
m=json.loads((ROOT/'assembly/compact_manifest.json').read_text())
projects={'controller':'controller/Elevation_Controller','elevation':'Elevation_Pivot_Daughter-Board'}
def xy(v):return tuple(round(p.ToMM(t),6) for t in (v.x,v.y))
def box(f):
    z=f.GetBoundingBox(False,False) if isinstance(f,p.FOOTPRINT) else f.GetBoundingBox()
    return tuple(p.ToMM(v) for v in (z.GetLeft(),z.GetTop(),z.GetRight(),z.GetBottom()))
def overlap(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
boards={};fs={};report={'revision':'P6','size_mm':[80,130],'boards':{}}
for board,pr in projects.items():
    b=p.LoadBoard(str(ROOT/(pr+'.kicad_pcb')));boards[board]=b;f={q.GetReference():q for q in b.GetFootprints()};fs[board]=f
    comp,nets,pins=netlist(OUT/(board+'.xml'));assert set(f)==set(comp)
    checked=0
    for r,fp in f.items():
        assert fp.GetValue()==comp[r]['value'] and fp.GetFPIDAsString()==comp[r]['footprint'],r
        for pad in fp.Pads():
            assert pad.GetNetname()==pins.get((r,pad.GetNumber()),''),(board,r,pad.GetNumber(),pad.GetNetname(),pins.get((r,pad.GetNumber())))
            checked+=1
            bb=box(pad);assert bb[0]>=20 and bb[1]>=20 and bb[2]<=100 and bb[3]<=150,(board,r,'pad outside',bb)
        if not r.startswith('J'):
            bb=box(fp);assert bb[0]>=20 and bb[1]>=20 and bb[2]<=100 and bb[3]<=150,(board,r,'body outside',bb)
    assert not list(b.GetTracks()) and not list(b.Zones())
    assert p.ToMM(b.GetDesignSettings().GetBoardThickness())==1.6
    d=read(ROOT/(pr+'.kicad_pcb'));edge=[n for n in kids(d,'gr_rect') if one(n,'layer')[1]=='Edge.Cuts']
    assert len(edge)==1 and one(edge[0],'start')[1:]==[20,20] and one(edge[0],'end')[1:]==[100,150]
    collisions=[]
    for i,(r,a) in enumerate(f.items()):
        for rr,z in list(f.items())[i+1:]:
            if a.IsFlipped()==z.IsFlipped() and overlap(box(a),box(z)):collisions.append((r,rr))
            if a.IsFlipped()!=z.IsFlipped():
                for aa,zz in [(a,z),(z,a)]:
                    for pad in aa.Pads():
                        if (pad.GetDrillSize().x or pad.GetDrillSize().y) and overlap(box(pad),box(zz)):collisions.append((aa.GetReference(),zz.GetReference(),'tail'))
    assert not collisions,(board,collisions)
    for r,a in f.items():
        if r.startswith('H'):
            x,y=xy(a.GetPosition());bb=(x-4,y-4,x+4,y+4)
            for rr,z in f.items():
                if rr!=r:assert not overlap(bb,box(z)),(board,r,rr,'hardware clearance')
    iso=({'U1018':(3,5.6),'U1010':(3,5.6),'U1016':(3,5.6),'U1007':(3,5.6)} if board=='controller' else
         {'U2':(3,6),'U13':(3,6),'U101':(6,3),'U160':(6,3),'U24':(1,3.2)})
    for r,(dx,dy) in iso.items():
        x,y=xy(f[r].GetPosition());bb=(x-dx,y-dy,x+dx,y+dy)
        for rr,z in f.items():
            if rr!=r:
                for pad in z.Pads():assert not overlap(bb,box(pad)),(board,r,rr,'copper in isolation corridor')
    report['boards'][board]={'footprints':len(f),'pads_checked':checked,'tracks_vias_zones':0,
       'body_and_tail_collisions':0,'isolation_corridors_clear_of_other_pads':len(iso),'mounting_envelope_mm':8,
       'front_parts':sum(not q.IsFlipped() for q in f.values()),'back_parts':sum(q.IsFlipped() for q in f.values())}
for r,n in [('J30',30),('J31',20)]:
    a=fs['controller'][r];b=fs['elevation'][r]
    assert a.IsFlipped() and not b.IsFlipped()
    for pin in map(str,range(1,n+1)):
        pa=next(q for q in a.Pads() if q.GetNumber()==pin);pb=next(q for q in b.Pads() if q.GetNumber()==pin)
        assert xy(pa.GetPosition())==xy(pb.GetPosition()),(r,pin,xy(pa.GetPosition()),xy(pb.GetPosition()))
        ca=m['pinout'][r][pin];cb={v:k for k,v in m['supply_aliases'].items()}.get(ca,ca)
        assert pa.GetNetname()==ca and pb.GetNetname()==cb,(r,pin,ca,pa.GetNetname(),cb,pb.GetNetname())
for r in m['supports_xy_mm']:assert xy(fs['controller'][r].GetPosition())==xy(fs['elevation'][r].GetPosition())
report['matching_contacts']=50;report['matching_support_pairs']=4
def distance(ref,pin,cap):
    f=fs['controller'];a=next(q for q in f[ref].Pads() if q.GetNumber()==pin)
    options=[q for q in f[cap].Pads() if q.GetNetname()==a.GetNetname()]
    assert options,(ref,pin,cap)
    return min(math.dist(xy(a.GetPosition()),xy(q.GetPosition())) for q in options)
report['critical_distances_mm']={}
for ref,pin,cap,limit in [('U202','2','C212',4),('U202','7','C214',4),('U202','8','C214',4),('U1','71','C20',4),('U1','106','C21',4),('U401','7','R407',5),('U401','8','R406',5),('U401','11','R408',5),('U401','14','R409',5)]:
    d=distance(ref,pin,cap);assert d<=limit,(ref,pin,cap,d);report['critical_distances_mm'][ref+'.'+pin+' to '+cap]=round(d,3)
for board in projects:
    path=OUT/(board+'_drc.json')
    if path.exists():
        d=json.loads(path.read_text());report['boards'][board]['drc']=dict(collections.Counter(v['type'] for v in d['violations']))
        report['boards'][board]['unconnected_items']=len(d.get('unconnected_items',[]))
        for v in d['violations']:
            if board=='elevation' and v['type']=='lib_footprint_mismatch' and all(z['description']=='Footprint J1' for z in v['items']):
                # Intentional instance-only move of edge-clipped terminal-block
                # silkscreen to fabrication layer; original pads are unchanged.
                continue
            assert board=='controller' and v['type'] in ['lib_footprint_mismatch','drill_out_of_range','clearance'],v
            if v['type']=='clearance':assert all('of U101 ' in z['description'] for z in v['items']),v
            if v['type']=='drill_out_of_range':assert all('of U401' in z['description'] for z in v['items']),v
(ROOT/'docs/validation/p6_placement_results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

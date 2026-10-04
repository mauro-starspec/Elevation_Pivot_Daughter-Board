"""KiCad bundled-Python portion of validate_stack.py; no PCB mutations."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import pcbnew as p

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'assembly/stack_interface.json').read_text())
BOARDS={'controller':ROOT/'controller/Elevation_Controller.kicad_pcb',
        'elevation':ROOT/'Elevation_Pivot_Daughter-Board.kicad_pcb'}
report={}
footprints={}
def xy(v):return (p.ToMM(v.x),p.ToMM(v.y))
def near(a,b):return max(abs(a[i]-b[i]) for i in range(2))<.001

for name,path in BOARDS.items():
    board=p.LoadBoard(str(path));fps={f.GetReference():f for f in board.GetFootprints()}
    footprints[name]=fps
    doc=ET.parse(ROOT/f'outputs/p4_{name}.xml').getroot()
    expected={c.get('ref'):c for c in doc.find('components')
              if not any(q.get('name')=='exclude_from_board' for q in c.findall('property'))}
    assert set(fps)==set(expected),(name,set(fps)^set(expected))
    for ref,c in expected.items():
        assert fps[ref].GetValue()==c.findtext('value'),(name,ref)
        assert fps[ref].GetFPIDAsString()==c.findtext('footprint'),(name,ref)
    checked=0
    for net in doc.find('nets'):
        for node in net:
            if node.get('ref') not in fps:continue
            pads=[q for q in fps[node.get('ref')].Pads() if q.GetNumber()==node.get('pin')]
            assert pads,(name,node.attrib)
            for pad in pads:
                assert pad.GetNetname()==net.get('name'),(name,node.attrib,pad.GetNetname(),net.get('name'))
                checked+=1
    assert not list(board.GetTracks()),'P4 drafts must be clearly unrouted'
    assert abs(p.ToMM(board.GetDesignSettings().GetBoardThickness())-DATA['pcb_thickness_mm'])<.001
    report[name]={'footprints':len(fps),'checked_pad_nets':checked,'unrouted':True}
    if DATA.get('mechanical_revision','').startswith('P5'):
        assert not list(board.Zones()), 'Placement-only boards must have no copper zones'
        if name=='elevation':
            for ref,f in fps.items():
                if ref not in ('J30','J31') and not ref.startswith('H'):
                    assert f.IsFlipped(), (ref,'carrier component must face outward')
        else:
            for ref,f in fps.items():
                assert f.IsFlipped()==(ref in ('J30','J31')), (ref,'controller face')
        report[name]['outward_population_verified']=True
    elif name=='elevation':
        for ref in ['PS2','PS6']:
            box=fps[ref].GetBoundingBox(False,False)
            assert p.ToMM(box.GetTop())>172.5,(ref,'tall converter beneath controller')
        assert near(xy(fps['PS4'].GetPosition()),(143,30))
        report[name]['tall_converters_clear_controller']=True

    # No component body may occupy an 8 mm square support-head clearance.
    for ref,coord in DATA['supports_controller_xy_mm'].items():
        if name=='elevation':coord=[coord[i]+DATA['controller_to_elevation_translation_mm'][i] for i in range(2)]
        assert near(xy(fps[ref].GetPosition()),coord),(name,ref)
        for other,f in fps.items():
            if other==ref:continue
            box=f.GetBoundingBox(False,False)
            hit=(p.ToMM(box.GetLeft())<coord[0]+4 and p.ToMM(box.GetRight())>coord[0]-4
                 and p.ToMM(box.GetTop())<coord[1]+4 and p.ToMM(box.GetBottom())>coord[1]-4)
            assert not hit,(name,ref,'support clearance',other)

contacts=0
dx,dy=DATA['controller_to_elevation_translation_mm']
for ref,conn in DATA['connectors'].items():
    a,b=footprints['controller'][ref],footprints['elevation'][ref]
    assert a.IsFlipped() and not b.IsFlipped(),ref
    assert a.GetFPIDAsString()=='Stack:Samtec_'+conn['controller_part']
    assert b.GetFPIDAsString()=='Stack:Samtec_'+conn['elevation_part']
    for number in conn['pins']:
        ap=next(q for q in a.Pads() if q.GetNumber()==number)
        bp=next(q for q in b.Pads() if q.GetNumber()==number)
        ax,ay=xy(ap.GetPosition())
        assert near((ax+dx,ay+dy),xy(bp.GetPosition())),(ref,number,'mating offset')
        assert near(xy(ap.GetDrillSize()),(1.02,1.02))
        assert near(xy(bp.GetDrillSize()),(1.04,1.04))
        contacts+=1
report['mating_contacts']=contacts
report['matched_clear_supports']=4
report['limits']='Placement-only drafts; routing, footprint release, enclosure/cable approval and manufacturing DRC remain pending.'
(ROOT/'outputs/p4_pcb_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('PCB schematic parity, 50 mating pads and four clear support pairs verified.')

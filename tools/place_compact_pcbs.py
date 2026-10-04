"""P6 80 x 130 mm, two-face placement attempt. No routed copper.

Run with KiCad Python. Reads immutable P5 snapshot and P6 netlists. Explicit
functional anchors; preserve the MCU cluster; local pin-aware passive packing.
"""
from pathlib import Path
import sys,json,copy,math,collections,xml.etree.ElementTree as ET
sys.path.insert(0,'C:/Users/Mauro/AppData/Roaming/Python/Python314/site-packages')
from kicad_sexp import read,save,kids,one,prop,S
from validate_stack import netlist
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'_work/p6_baseline';OUT=ROOT/'outputs/compact'
from prepare_compact_baseline import ensure_baseline
ensure_baseline()
PROJECTS={'controller':'controller/Elevation_Controller','elevation':'Elevation_Pivot_Daughter-Board'}
M=json.loads((ROOT/'assembly/compact_manifest.json').read_text())
INV=json.loads((BASE/'inventory.json').read_text())
SOURCE={(b,f['ref']):f for b,fs in INV.items() for f in fs}
PARTS={(x['board'],x['ref']):x for x in M['reference_mapping']}
DOCS={b:read(BASE/(pr+'.kicad_pcb')) for b,pr in PROJECTS.items()}
FPS={(b,prop(f,'Reference')[2]):f for b,d in DOCS.items() for f in kids(d,'footprint')}
SUPPORTS={'H30':(25,25),'H31':(95,25),'H32':(25,145),'H33':(95,145)}
HEADERS={'J30':(40,85),'J31':(40,97)}
def pt(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def xy(v):return p.ToMM(v.x),p.ToMM(v.y)
def box(f):
    z=f.GetBoundingBox(False,False) if isinstance(f,p.FOOTPRINT) else f.GetBoundingBox()
    return tuple(p.ToMM(v) for v in (z.GetLeft(),z.GetTop(),z.GetRight(),z.GetBottom()))
def overlap(a,b,gap=.25):return a[0]<b[2]+gap and a[2]>b[0]-gap and a[1]<b[3]+gap and a[3]>b[1]-gap
def move(f,x,y,a,back):
    if f.IsFlipped()!=back:f.Flip(f.GetPosition(),False)
    f.SetOrientationDegrees(a);f.SetPosition(pt(x,y));f.SetLocked(False)
def rect(b,a,z,layer):
    n=p.PCB_SHAPE();n.SetShape(p.SHAPE_T_RECT);n.SetStart(pt(*a));n.SetEnd(pt(*z));n.SetLayer(layer);n.SetWidth(p.FromMM(.05));b.Add(n)
def text(b,s,x,y,layer,size=1):
    t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(pt(x,y));t.SetTextSize(pt(size,size));t.SetTextThickness(p.FromMM(.13));t.SetLayer(layer);t.SetMirrored(layer==p.B_SilkS);b.Add(t)
inventory=json.loads((OUT/'inventory.json').read_text()) if (OUT/'inventory.json').exists() else {}
report=json.loads((OUT/'placement_build.json').read_text()) if (OUT/'placement_build.json').exists() else {}
for board,project in PROJECTS.items():
    if len(sys.argv)>1 and sys.argv[1]!=board:continue
    comps,nets,pins=netlist(OUT/(board+'.xml'));xml=ET.parse(OUT/(board+'.xml')).getroot()
    cx={c.get('ref'):c for c in xml.find('components')};netids={n:i+1 for i,n in enumerate(sorted(nets))}
    doc=copy.deepcopy(DOCS[board]);doc[:]=[n for n in doc if not(isinstance(n,list) and n and (str(n[0]) in ('footprint','net','segment','via','arc','zone') or str(n[0]).startswith('gr_')))]
    doc.append([S('net'),0,''])
    for n,i in netids.items():doc.append([S('net'),i,n])
    old={}
    for (dest,ref),m in PARTS.items():
        if dest!=board:continue
        src=(m['source_board'],m['source_ref']);f=copy.deepcopy(FPS[src]);old[ref]=SOURCE[src]
        prop(f,'Reference')[2]=ref;f[1]=comps[ref]['footprint']
        comp=cx[ref];one(f,'path')[1]=comp.find('sheetpath').get('tstamps')+comp.findtext('tstamps')
        if not kids(f,'sheetname'):f.append([S('sheetname'),''])
        one(f,'sheetname')[1]=comp.find('sheetpath').get('names')
        sheetfile=next((n.get('value') for n in comp.findall('property') if n.get('name')=='Sheetfile'),'')
        if not kids(f,'sheetfile'):f.append([S('sheetfile'),''])
        one(f,'sheetfile')[1]=sheetfile
        for pad in kids(f,'pad'):
            pad[:]=[x for x in pad if not(isinstance(x,list) and x and str(x[0])=='net')]
            name=pins.get((ref,str(pad[1])),'')
            if name:pad.append([S('net'),netids[name],name])
        # Project-relative vendor models on transferred field footprints.
        if m['source_board']!=board:
            for model in kids(f,'model'):model[1]=model[1].replace('${KIPRJMOD}/','${KIPRJMOD}/../')
        doc.append(f)
    tmp=OUT/(board+'_input.kicad_pcb');save(tmp,doc);b=p.LoadBoard(str(tmp));fps={f.GetReference():f for f in b.GetFootprints()}
    rect(b,(20,20),(100,150),p.Edge_Cuts)
    fixed={};owner={};target={};face={};regions={}
    def anchor(ref,x,y,a=0,back=False):
        move(fps[ref],x,y,a,back);fixed[ref]=box(fps[ref]);face[ref]=back
    for ref,(x,y) in SUPPORTS.items():anchor(ref,x,y)
    for ref,(x,y) in HEADERS.items():anchor(ref,x,y-2.54 if board=='controller' else y,270 if board=='controller' else 90,board=='controller')
    if board=='controller':
        # Retain the complete validated MCU / decoupling / crystal geometry,
        # reflected as one group onto the inward face.
        cluster=[r for r,o in old.items() if o['sheet']=='/STM32 core clocks and reset/' and r not in ['SW1','SW2']]+['FB201','C221','C222']
        for r in cluster:
            f=fps[r];f.Flip(pt(85,79),False);v=f.GetPosition();f.SetPosition(pt(xy(v)[0]-25,xy(v)[1]-17));f.SetLocked(False)
            fixed[r]=box(f);face[r]=True
        for r,y in [('J1003',54),('J1006',107)]:anchor(r,30,y+5.54,270,False)
        for r,y in [('J1002',54),('J1004',107)]:anchor(r,90,y-5.54,90,False)
        poses={
          'J401':(65.715,37.3,180,False),'J501':(35,23.67,180,False),
          'U401':(59,46,0,False),'Y401':(51.5,46,270,False),'U402':(74,45.5,0,False),'U403':(70,49,0,False),
          'U501':(35,33,0,False),'D501':(39,30,0,False),
          'U202':(56,125,0,True),'L201':(66,123,0,True),'U101':(61,111,180,True),
          'C212':(51,126.25,270,True),'C214':(61.5,126.25,270,True),
          'U902':(68,105,0,True),'J601':(60,105,0,False),'U601':(72,100,0,False),'U602':(65,112,0,False),
          'SW1':(36,135,0,False),'SW2':(52,135,0,False),
          'U1018':(45,74.5,180,False),'U1010':(45,108,180,False),
          'U1016':(79,33,0,False),'U1007':(77,108,0,False),
          'Q1003':(35.5,48,0,False),'Q1004':(35.5,58,0,False),'Q1005':(35.5,68,0,False),
          'Q1013':(35.5,97,0,False),'Q1001':(35.5,108,0,False),'Q1002':(35.5,119,0,False),
          'Q1007':(84,66,0,False),'Q1006':(84,116,0,False),
          'U1020':(30,76,90,False),'U1019':(30,80,90,False),'D1004':(30,85,90,False),
          'U1011':(30,126,90,False),'U1012':(30,130,90,False),'D1001':(30,135,90,False),
          'U1008':(91,75,0,False),'U1009':(91,81,0,False),'D1002':(91,86,90,False),'U1027':(85,72,90,False),
          'U1003':(91,127,0,False),'U1006':(91,133,0,False),'D1003':(91,138,90,False),'U1026':(85,125,90,False),
          'C9':(54.5,48,90,True),'R4':(40.5,67.5,90,True),
        }
        for r,v in poses.items():anchor(r,*v)
        for r,x in [('D901',62),('D902',70),('D903',78),('D904',86)]:anchor(r,x,141,0,False)
        for r,x,y,a in [('R407',54.5,50.5,270),('R406',58,53.5,270),('R408',62.5,51.5,270),('R409',65,47,0),('C405',59,50.5,0),('C406',54.75,47,270)]:anchor(r,x,y,a,False)
    else:
        # Extra enclosure holes stay as PCB features at distinct clear locations.
        for r,x,y in [('H7',25,80),('H5',95,80),('H8',36,145),('H6',84,145)]:anchor(r,x,y)
        for r,y in [('J20',53),('J7',106)]:anchor(r,30,y-5.54,90,True)
        for r,y in [('J21',53),('J5',106)]:anchor(r,90,y+5.54,270,True)
        anchor('J22',54.46,140,180,True)
        poses={
         'J1':(68,23,0,True),'PS4':(60,53,270,True),
         'L1':(60,74,0,True),'FL1':(60,34,0,True),'Q14':(41,33.5,270,True),'Q15':(79,33.5,90,True),'R7':(40,42,0,True),'U4':(47,30,90,False),
         'D5':(81.5,42,0,True),'D12':(78,62,0,True),'Q16':(82,54,270,True),'D6':(84,60,90,True),
         'PS1':(47,116,0,True),'PS2':(45,75,180,True),'PS6':(77,75,180,True),'PS5':(68,116,0,True),
         'PS10':(44,131,0,True),'PS11':(82,129,180,True),
         'U25':(44.5,66,0,True),'U23':(78,66,0,True),
         'U100':(45,53,180,False),'U110':(75,53,0,False),'U101':(60,54,90,False),
         'U102':(34.5,43,0,False),'U103':(34.5,53,0,False),'U104':(34.5,63,0,False),
         'U112':(85.5,43,180,False),'U113':(85.5,53,180,False),'U114':(85.5,63,180,False),
         'U105':(60,35,0,False),'J12':(80,138,0,False),
         'U13':(77,109,0,False),'U15':(83,122,0,False),'U17':(91,125,0,False),'U14':(84,85,90,False),
         'U2':(47,109,180,False),'IC1':(39,122,0,False),'IC2':(34,132,0,False),'U5':(30,125,270,True),
         'D10':(30,132,90,True),'D11':(37,133,90,True),
         'U24':(60,108,180,False),'U21':(60,119,180,False),'TH1':(33,88,0,False),'TH2':(69,136,0,False),
         'U160':(60,132,270,False),
        }
        for r,v in poses.items():anchor(r,*v)

    # Associate each passive to its functional parent, using the preserved P5
    # same-sheet geometry. Selected special cases override physical proximity.
    explicit=({'C211':'U202','C212':'U202','C213':'U202','C214':'U202','R211':'U202','R212':'U202',
               'C215':'L201','C216':'L201','C217':'L201','C218':'L201',
               'R911':'D901','R912':'D902','R913':'D903','R914':'D904'} if board=='controller' else
              {'C110':'PS10','C111':'PS10','C140':'PS11','C141':'PS11','C116':'U101','C117':'U101',
               'C160':'U160','C161':'U160','C162':'U160','C163':'U160','R160':'U160','R161':'U160','R162':'U160',
               'JP160':'U160','JP161':'U160','JP162':'U160','R163':'U160','R164':'U160','R165':'U160',
               'C113':'U105','C114':'U105','C13':'PS4','C14':'PS4','C20':'PS4','C188':'J12','R172':'J12',
               'R180':'TH1','R181':'TH2','R182':'U21','R183':'U21','C190':'U21','C191':'U21'})
    for r in fps:
        if r in fixed:continue
        o=old[r];candidates=[a for a in fixed if old[a]['sheet']==o['sheet'] and a.startswith(('U','IC','PS','Q','L','FL'))]
        if not candidates:candidates=[a for a in fixed if a.startswith(('U','PS'))]
        a=explicit.get(r,min(candidates,key=lambda a:(old[a]['x']-o['x'])**2+(old[a]['y']-o['y'])**2))
        owner[r]=a;f=fps[a];dx=o['x']-old[a]['x'];dy=o['y']-old[a]['y']
        if abs(dx)>15 or abs(dy)>15:dx=dy=0
        target[r]=(xy(f.GetPosition())[0]+dx,xy(f.GetPosition())[1]+dy)
        face[r]=f.IsFlipped()
        # Do not force support/power bulk components onto the inward face.
        if o['ref'].startswith(('C','L','FL','F')) and (o['box'][2]-o['box'][0])*(o['box'][3]-o['box'][1])>40:face[r]=board=='elevation'

    obstacles=[]
    def occupy(r,f):
        bb=box(f);obstacles.append((r,f.IsFlipped(),bb))
        for q in f.Pads():
            if q.GetDrillSize().x or q.GetDrillSize().y:obstacles.append((r,not f.IsFlipped(),box(q)))
        if r.startswith('H'):
            x,y=xy(f.GetPosition());obstacles.extend([(r,s,(x-4,y-4,x+4,y+4)) for s in [False,True]])
    for r in fixed:occupy(r,fps[r])
    # Copper-free isolation corridors on both faces; keep opposite-face parts
    # and PTH tails out of the space between isolated pin banks.
    iso=({'U1018':(3,5.6),'U1010':(3,5.6),'U1016':(3,5.6),'U1007':(3,5.6)} if board=='controller' else
         {'U2':(3,6),'U13':(3,6),'U101':(6,3),'U160':(6,3),'U24':(1,3.2)})
    overlaps=[]
    for i,(r,s,bb) in enumerate(obstacles):
        for rr,ss,zz in obstacles[i+1:]:
            if r!=rr and s==ss and overlap(bb,zz,0):
                overlaps.append((r,rr));print('overlap',r,rr,s,bb,zz)
    if overlaps:
        (OUT/(board+'_anchor_overlaps.json')).write_text(json.dumps(sorted(set(overlaps)),indent=2))
        print(board,'anchor overlaps',sorted(set(overlaps)))
        # Save a diagnostic inventory before refusing to legalize over collisions.
        (OUT/(board+'_anchors.json')).write_text(json.dumps({r:{'box':box(fps[r]),'back':face[r]} for r in fixed},indent=2))
        raise RuntimeError('Resolve fixed anchors first')
    for r,(dx,dy) in iso.items():
        x,y=xy(fps[r].GetPosition());bb=(x-dx,y-dy,x+dx,y+dy)
        # An opposite-face moulded body may project over the corridor; copper
        # pads and drilled tails may not. Same-face body checks ran above.
        conflicts=[rr for rr in fixed if rr!=r for q in fps[rr].Pads() if overlap(box(q),bb,0)]
        if conflicts:raise RuntimeError(('isolation corridor',board,r,sorted(set(conflicts))))
        for side in [False,True]:obstacles.append((r,side,bb))
        rect(b,(x-dx,y-dy),(x+dx,y+dy),p.Dwgs_User)
    geometry={}
    for r,f in fps.items():
        if r in fixed:continue
        geometry[r]={}
        for angle in [0,90,180,270]:
            move(f,0,0,angle,face[r]);geometry[r][angle]=(box(f),[(q.GetNetname(),*xy(q.GetPosition())) for q in f.Pads()])
    netanchors=collections.defaultdict(list)
    for r in fixed:
        for q in fps[r].Pads():
            if q.GetNetname():netanchors[q.GetNetname()].append((r,*xy(q.GetPosition())))
    remaining=[r for r in fps if r not in fixed]
    remaining.sort(key=lambda r:(2 if r.startswith('TP') else 0 if r.startswith('C') else 1,-((geometry[r][0][0][2]-geometry[r][0][0][0])*(geometry[r][0][0][3]-geometry[r][0][0][1]))))
    displacements=[]
    for r in remaining:
        tx,ty=target[r];links=[];a=owner[r]
        for net in {q.GetNetname() for q in fps[r].Pads() if q.GetNetname()}:
            options=[q for q in netanchors[net] if q[0]==a]
            if options:
                q=min(options,key=lambda q:(q[1]-tx)**2+(q[2]-ty)**2);links.append((net,q[1],q[2]))
        if r.startswith('C') and links:
            live=[q for q in links if q[0] not in ['GND','GND_STM32','GND_BRAKE','GND_CAN','-BATT']]
            if live:tx=sum(q[1] for q in live)/len(live);ty=sum(q[2] for q in live)/len(live)
        tx=max(22,min(98,tx));ty=max(22,min(148,ty));best=None
        for radius in [6,12,24,60,130]:
            candidates=[]
            for ix in range(max(42,math.floor((tx-radius)*2)),min(198,math.ceil((tx+radius)*2))+1):
                for iy in range(max(42,math.floor((ty-radius)*2)),min(298,math.ceil((ty+radius)*2))+1):
                    x=ix/2;y=iy/2;dist=(x-tx)**2+(y-ty)**2
                    if dist<=radius**2:candidates.append((dist,x,y))
            candidates.sort()
            for dist,x,y in candidates:
                if best and dist*.7>best[0]:break
                for angle,(rel,pads) in geometry[r].items():
                    bb=(rel[0]+x,rel[1]+y,rel[2]+x,rel[3]+y)
                    if bb[0]<21 or bb[1]<21 or bb[2]>99 or bb[3]>149:continue
                    if any(s==face[r] and overlap(bb,zz) for rr,s,zz in obstacles):continue
                    cost=dist*.7
                    for net,px,py in links:
                        opts=[(qx+x,qy+y) for nn,qx,qy in pads if nn==net]
                        if opts:cost+=min((qx-px)**2+(qy-py)**2 for qx,qy in opts)*.25
                    if best is None or cost<best[0]:best=(cost,x,y,angle)
            if best:break
        if best is None:raise RuntimeError((board,r,'cannot fit',face[r]))
        _,x,y,angle=best;move(fps[r],x,y,angle,face[r]);occupy(r,fps[r]);displacements.append((r,round(math.hypot(x-tx,y-ty),2)))

    # Reference text stays on assembly layer first; add clear connector legends.
    for r,f in fps.items():
        f.Value().SetVisible(False);ref=f.Reference();ref.SetVisible(True);ref.SetLayer(p.B_Fab if f.IsFlipped() else p.F_Fab)
        ref.SetTextSize(pt(.7,.7));ref.SetTextThickness(p.FromMM(.1));ref.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));ref.SetMirrored(f.IsFlipped());ref.SetPosition(f.GetPosition())
        if r.startswith(('J','H')):f.SetLocked(True)
    text(b,'P6 80 x 130 | UNROUTED',60,152,p.Dwgs_User,1.2)
    for r,(x,y) in SUPPORTS.items():rect(b,(x-4,y-4),(x+4,y+4),p.Dwgs_User)
    pro=ROOT/(project+'.kicad_pro');raw=pro.read_bytes()
    try:p.SaveBoard(str(ROOT/(project+'.kicad_pcb')),b)
    finally:pro.write_bytes(raw)
    inventory[board]=[{'ref':r,'value':f.GetValue(),'footprint':f.GetFPIDAsString(),'sheet':cx[r].find('sheetpath').get('names'),
       'x':xy(f.GetPosition())[0],'y':xy(f.GetPosition())[1],'angle':f.GetOrientationDegrees(),'back':f.IsFlipped(),'box':box(f),
       'pads':[{'pin':q.GetNumber(),'net':q.GetNetname(),'x':xy(q.GetPosition())[0],'y':xy(q.GetPosition())[1],'size':xy(q.GetSize()),'drill':xy(q.GetDrillSize())} for q in f.Pads()]} for r,f in fps.items()]
    report[board]={'footprints':len(fps),'largest_displacements':sorted(displacements,key=lambda x:-x[1])[:20],
       'front':sum(not f.IsFlipped() for f in fps.values()),'back':sum(f.IsFlipped() for f in fps.values()),'tracks':len(list(b.GetTracks())),'zones':len(list(b.Zones()))}
    (OUT/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n');(OUT/'placement_build.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n');(OUT/'placement_build.json').write_text(json.dumps(report,indent=2)+'\n')
M['supports_xy_mm']=SUPPORTS;M['header_origins_carrier']=HEADERS;(ROOT/'assembly/compact_manifest.json').write_text(json.dumps(M,indent=2)+'\n')
print(json.dumps(report,indent=2))

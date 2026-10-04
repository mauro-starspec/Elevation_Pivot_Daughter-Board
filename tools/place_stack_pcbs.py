"""P5 placement-only build. Run with KiCad 9's bundled Python.

Starts from the immutable local pre-placement snapshot, never from a routed
board. Explicit functional anchors plus pin-aware passive placement. No tracks,
vias or copper pours are generated. Review with validate_placement.py and DRC.
"""
from pathlib import Path
import json, math, shutil, hashlib, collections, sys
sys.path.insert(0,'C:/Users/Mauro/AppData/Roaming/Python/Python314/site-packages')
from kicad_sexp import read, save
import pcbnew as p

ROOT=Path(__file__).resolve().parents[1]
SNAP=ROOT/'_work/before_placement_20261003'
OUT=ROOT/'outputs/placement'; OUT.mkdir(parents=True,exist_ok=True)
PROJECTS={'controller':'controller/Elevation_Controller','elevation':'Elevation_Pivot_Daughter-Board'}
ORIGIN=(20,20); SIZE=(120,200)
SUPPORTS={'H30':(43,26),'H31':(112,26),'H32':(56,213),'H33':(103,213)}
HEADERS={'J30':(78,100),'J31':(80,143)}

def pt(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def xy(v): return (p.ToMM(v.x),p.ToMM(v.y))
def box(f):
    b=f.GetBoundingBox(False,False)
    return tuple(p.ToMM(v) for v in (b.GetLeft(),b.GetTop(),b.GetRight(),b.GetBottom()))
def overlaps(a,b,gap=.25):
    return a[0]<b[2]+gap and a[2]>b[0]-gap and a[1]<b[3]+gap and a[3]>b[1]-gap
def move(f,x,y,a,back=False):
    if f.IsFlipped()!=back: f.Flip(f.GetPosition(),False)
    f.SetOrientationDegrees(a); f.SetPosition(pt(x,y)); f.SetLocked(False)
def addtext(b,s,x,y,layer,size=1):
    t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(pt(x,y));t.SetTextSize(pt(size,size));t.SetTextThickness(p.FromMM(.15));t.SetLayer(layer)
    t.SetMirrored(layer==p.B_SilkS);b.Add(t)
def rectangle(b,a,z,layer,width=.1):
    s=p.PCB_SHAPE();s.SetShape(p.SHAPE_T_RECT);s.SetStart(pt(*a));s.SetEnd(pt(*z));s.SetLayer(layer);s.SetWidth(p.FromMM(width));b.Add(s)

if not SNAP.exists():
    SNAP.mkdir(parents=True)
    paths=[ROOT/(v+ext) for v in PROJECTS.values() for ext in ('.kicad_pcb','.kicad_pro')]
    paths += [ROOT/'assembly/stack_interface.json',ROOT/'assembly/README.md',ROOT/'PROJECT_HANDOFF.md']
    for src in paths:
        dst=SNAP/src.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    (SNAP/'schematic_hashes.json').write_text(json.dumps({str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in list(ROOT.glob('*.kicad_sch'))+list((ROOT/'controller').glob('*.kicad_sch'))},indent=2))
original=json.loads((ROOT/'_work/placement_inventory.json').read_text())
report={}; final={}

for boardname,project in PROJECTS.items():
    doc=read(SNAP/(project+'.kicad_pcb'))
    doc[:]=[n for n in doc if not (isinstance(n,list) and n and
             (str(n[0]) in ('segment','arc','via','zone') or str(n[0]).startswith('gr_')))]
    temp=OUT/(boardname+'_placement_input.kicad_pcb');save(temp,doc)
    b=p.LoadBoard(str(temp))
    fps={f.GetReference():f for f in b.GetFootprints()}
    old={f['ref']:f for f in original[boardname]}
    rectangle(b,ORIGIN,(140,220),p.Edge_Cuts,.05)
    fixed={}; targets={}; bounds={}; binding={}
    def anchor(ref,x,y,a=None,back=None):
        f=fps[ref]
        if a is None:a=old[ref]['angle']
        if back is None:back=boardname=='elevation'
        move(f,x,y,a,back);fixed[ref]=box(f)
        return f
    for ref,(x,y) in SUPPORTS.items():anchor(ref,x,y,0,False)
    for ref,(x,y) in HEADERS.items():anchor(ref,x+2.54 if boardname=='controller' else x,y,180 if boardname=='controller' else 0,boardname=='controller')

    if boardname=='controller':
        # Keep the MCU/clock and PHY clusters compact; edge connectors above.
        shifts={'/STM32 core clocks and reset/':(27.5,0), '/Ethernet/':(27,0),
                '/USB-C/':(38,0), '/3.3 V power and VDDA filter/':(20,10),
                '/5 V input protection/':(-12,9), '/SWD and VCP/':(53,-56),
                '/Watchdog and status/':(27.5,0)}
        for ref,o in old.items():
            dx,dy=shifts.get(o['sheet'],(0,0));targets[ref]=(o['x']+dx,o['y']+dy)
        for ref in ['U1','Y1','Y2','U401','Y401','U402','U403','J401','J501','U501','U101','U202','L201','U902','J601','U601','U602']:
            anchor(ref,*targets[ref],back=False)
        anchor('L201',73,127,0,False)
        anchor('C212',58,128,90,False)
        anchor('C214',68.5,128.5,90,False)
        # RMII source termination is owned by the transmitter; do not place it
        # halfway along the future net merely to minimize total ratsnest length.
        anchor('Y401',64.5,50,-90,False)
        for ref,x,y,a in [('R407',67.5,54.5,270),('R406',71,57.5,270),
                          ('R408',75.5,55.5,270),('R409',78,51,0),
                          ('C405',72,54.5,0),('C406',67.75,51,270),
                          ('R404',65.5,84.5,180),('R606',99,85,180),
                          ('R503',103,72,180),('R504',103,74.5,180)]:anchor(ref,x,y,a,False)
        anchor('SW1',40,91,0,False);anchor('SW2',40,103,0,False)
        for ref,x in [('D901',108),('D902',116),('D903',124),('D904',132)]:anchor(ref,x,114,0,False)
        for ref,x in [('R911',108),('R912',116),('R913',124),('R914',132)]:targets[ref]=(x,110.5)
        # VDDA filter belongs at the MCU analogue supply, not in the buck block.
        anchor('FB201',64,92,0,False)
        targets.update({'C221':(69,92),'C222':(69,95),'C20':(94,93),
                        'R503':(101,74),'R504':(101,71),'R507':(102,78),'C501':(105,78),
                        'R404':(69,90),'R401':(83,64),'R402':(99,85),'R403':(89,64),
                        'R606':(101,94), 'TP910':(106,99), 'TP909':(109,33),
                        'TP905':(117,97),'TP907':(105,120),'TP908':(130,120)})
        binding.update({'C211':'U202','C212':'U202','C213':'U202','C214':'U202',
                        'R211':'U202','R212':'U202','C102':'U101','C105':'U101',
                        'C20':'U1','C21':'U1','C222':'FB201','C221':'FB201'})
        # Critical buck loop: input ceramics at VIN/PGND, bootstrap at SW/BOOT,
        # feedback and VCC bypass at their own pins; output caps by the inductor.
        targets.update({'C211':(56.5,128),'C212':(58,126),'C213':(69,130),
                        'C214':(69,125.5),'R211':(68,134),'R212':(64,134),
                        'C215':(75,131.5),'C216':(76,126),'C217':(78,131.5),'C218':(75,135)})
    else:
        for ref,x,y in [('H7',26,26),('H5',134,26),('H8',26,214),('H6',134,214)]:anchor(ref,x,y,0,False)
        # Connector faces point outward. The carrier is populated on its bottom.
        for ref,y in [('J3',64),('J5',106),('J7',148),('J20',190)]:anchor(ref,30,y-5.54,90)
        for ref,y in [('J2',64),('J4',106),('J6',148),('J21',190)]:anchor(ref,130,y+5.54,270)
        anchor('J22',74.46,210,180)
        anchors={
            'J1':(76,24,0),'Q14':(47,38,-90),'Q15':(68,38,90),'R7':(79,46,0),
            'D5':(51,29.5,0),'U4':(61,48,90),'FL1':(116,39,0),'L1':(98,38,0),'PS4':(83,62,270),
            'C5':(85,37,180),'C10':(108.5,48,270),
            'D12':(105,56.5,0),'Q16':(102,51,-90),'D6':(117,53,90),
            'U18':(62,64,180),'Q3':(43,57,180),'Q4':(43,64,180),'Q5':(43,71,180),
            'U20':(36,56,90),'U19':(36,71,-90),'D4':(36,76,-90),
            'U16':(104,64,0),'Q7':(119,71,0),'U8':(124,58,180),'U9':(124,72,180),'U27':(123,54,90),'D2':(123,76,-90),
            'U25':(114,79,0),'PS2':(115,87,180),
            'U13':(62,106,180),'U15':(47,106,180),'U17':(36,106,180),'U14':(49,118,90),
            'U7':(98,106,0),'Q6':(119,114,0),'U6':(124,114,0),'U3':(124,100,0),'U26':(123,96,90),'D3':(124,118,0),
            'U22':(116,97,0),'U23':(111,121,0),'PS6':(115,129,180),
            'U2':(70,148,180),'IC1':(44,141,0),'IC2':(44,155,0),
            'D10':(36,136,90),'D11':(36,163,90),'U5':(36,148,-90),'PS1':(49,133,0),
            'U10':(98,148,0),'Q13':(119,141,0),'Q1':(119,148,0),'Q2':(119,155,0),
            'U11':(124,142,0),'U12':(124,154,0),'D1':(120,160,0),'PS5':(115,172,0),
            'U24':(70,166,180),'U21':(55,174,180),'TH1':(45,179,0),'TH2':(61,183,0),
            'U100':(49,190,180),'U110':(111,190,0),'U101':(75,178,90),'U160':(94,178,270),
            'U102':(36,184,0),'U103':(36,190,0),'U104':(36,196,0),
            'U112':(124,184,180),'U113':(124,190,180),'U114':(124,196,180),
            'U105':(67,199,0),'PS10':(41,211,0),'PS11':(121,211,180),'J12':(61,205,0),
        }
        for ref,pose in anchors.items():anchor(ref,*pose)
        anchor('TP9',56,140,0);anchor('TP10',61,160,0)
        for ref,x,y in [('TP2',35,44),('TP3',98,27),('TP5',104,165),
                        ('TP6',134,126),('TP7',134,84.5),('TP8',35,35)]:anchor(ref,x,y,0)
        # Binding describes local functional ownership, not a change to nets.
        for ref,parent in {
            'C110':'PS10','C111':'PS10','C112':'U100','C113':'U105','C114':'U105','C115':'U100','C116':'U101','C117':'U101',
            'C140':'PS11','C141':'PS11','C142':'U110','C145':'U110',
            'C160':'U160','C161':'U160','C162':'U160','C163':'U160',
            'R160':'U160','R161':'U160','R162':'U160','R163':'J22','R164':'J22','R165':'J22',
            'JP160':'J22','JP161':'J22','JP162':'J22','C188':'J12','R172':'J12',
            'R180':'TH1','R181':'TH2','R182':'U21','R183':'U21','C190':'U21','C191':'U21',
            'R2':'U7','C99':'U22','C47':'PS6','C48':'PS6','C74':'PS2',
            'C87':'U24','C88':'U24','C90':'U24','R67':'U24','R68':'U24',
            'C89':'U21','C91':'U21','R65':'U21','R66':'U21',
            'C93':'U14','C94':'U14','C95':'U14','C92':'U14',
            'C100':'U23','C101':'U23','C102':'U25','C103':'U25',
            'FB1':'PS6','C49':'PS6','C50':'PS6','C61':'PS6','C35':'PS6','C44':'PS6','C46':'PS6',
            'FB2':'PS2','C73':'PS2','C75':'PS2','C76':'PS2','C77':'PS2','C78':'PS2','C54':'PS2','C55':'PS2','C86':'PS2',
            'FB3':'PS5','C79':'PS5','C80':'PS5','C81':'PS5','C82':'PS5','C83':'PS5','C84':'PS5','C85':'PS5',
            'R9':'IC1','R5':'IC1','R11':'IC2','R3':'IC1','R22':'IC2','R25':'U2',
        }.items():binding[ref]=parent
        for r in list(range(100,109)):binding['R'+str(r)]='U100'
        for r in list(range(130,139)):binding['R'+str(r)]='U110'
        # For retained passives preserve their local association with the closest
        # original IC/module in that sheet. Staged additions have explicit owners.
        for ref,o in old.items():
            if ref in fixed:continue
            parent=binding.get(ref)
            if not parent:
                same=[a for a in fixed if old[a]['sheet']==o['sheet'] and not a.startswith(('J','H','TP','D','Q'))]
                if not same:same=[a for a in fixed if not a.startswith(('J','H','TP'))]
                parent=min(same,key=lambda a:(old[a]['x']-o['x'])**2+(old[a]['y']-o['y'])**2)
                binding[ref]=parent
            px,py=xy(fps[parent].GetPosition())
            dx=o['x']-old[parent]['x'];dy=o['y']-old[parent]['y']
            if abs(dx)>20 or abs(dy)>20:dx=dy=0
            targets[ref]=(px+dx,py+dy)
        # Side/domain fences keep passives on their own side of each isolator.
        for ref,o in old.items():
            if ref in fixed:continue
            ns={q['net'] for q in o['pads']}
            if 'GND_STM32' in ns or '+3V3_STM32' in ns or '+5V_STM32' in ns:
                bounds[ref]=(68.5,74,92,174)
                if binding.get(ref) in ('U2','U24'):bounds[ref]=(76,127,92,174)
            elif 'GND_BRAKE' in ns or '+5V_BRAKE' in ns or '+24V_BRAKE' in ns:
                bounds[ref]=(31,125,67,186)
            else:
                owner=binding.get(ref,'');ox,oy=xy(fps[owner].GetPosition()) if owner else (80,120)
                if owner in ('U100','U110','PS10','PS11','U105','J12','J22') or o['sheet'].startswith('/Pivot_'):
                    bounds[ref]=(32,182,128,217)
                elif owner in ('U18',):bounds[ref]=(32,49,58,83)
                elif owner in ('U16','U25'):bounds[ref]=(110,49,128,94)
                elif owner=='PS2':bounds[ref]=(102,78,136,96)
                elif owner in ('U7','U23','PS6','U22'):bounds[ref]=(104,92,128,138)
                elif owner in ('U10',):bounds[ref]=(104,133,128,170)
                elif owner=='PS5':bounds[ref]=(102,158,132,182)
                elif owner in ('U13','U15'):bounds[ref]=(32,90,58,117)
                elif owner in ('U2','IC1','IC2','U21','U24','PS1'):bounds[ref]=(32,125,67,186)
                elif owner=='U14':bounds[ref]=(34,113,61,130)
                elif owner in ('U4','Q14','Q15','PS4','FL1','L1'):bounds[ref]=(32,29,127,80)
        # PS4 clean output capacitors are at its bottom-side output bank.
        for ref in ('C13','C14','C20'):bounds[ref]=(68,73,100,87);binding[ref]='PS4';targets[ref]=(83,78)
        # Explicit service pads and bus bias/termination close to the bus socket.
        targets.update({'JP160':(72,201),'JP161':(83,201),'JP162':(94,201),
                        'R163':(73,205),'R164':(85,205),'R165':(95,205),
                        'C116':(70,185),'C117':(70,170),'C160':(91,170),'C161':(95,170),
                        'C162':(91,185),'C163':(96,185),'C112':(52,183),'C115':(52,198),
                        'C142':(108,183),'C145':(108,198),'C113':(60,201),'C114':(69,201),
                        'R180':(45,175),'R181':(57,176),'C190':(48,176),'C191':(51,177),
                        'C110':(39,204),'C111':(47,208),'C140':(122,203),'C141':(114,208)})
        for r in ['C116','C162','C163']:bounds[r]=(66,182,102,195)
        # Cross-domain TVS/filter parts retain their explicit circuit placement.
        for r in ['C16']:bounds[r]=(67,76,109,97);targets[r]=(86,86)
        service={'TP1':((86,93),(69,80,97,174),'J30'),
                 'TP2':((39,47),(32,29,127,80),'J1'),
                 'TP3':((89,28),(32,29,127,80),'R7'),
                 'TP4':((94,137),(69,80,97,174),'J30'),
                 'TP5':((109,169),(108,160,129,180),'PS5'),
                 'TP6':((128,136),(110,122,138,139),'PS6'),
                 'TP7':((128,92),(110,81,138,95),'PS2'),
                 'TP8':((37,37),(32,30,58,50),'J1'),
                 'TP9':((36,171),(31,124,59,183),'IC1'),
                 'TP10':((36,177),(31,124,59,183),'IC2'),
                 'TP30':((91,167),(69,80,98,174),'J31')}
        for i in range(6):service['TP'+str(20+i)]=((65+5*(i%3),190+6*(i//3)),(60,187,82,200),'U100' if i<3 else 'U110')
        for ref,(target,limit,owner) in service.items():targets[ref]=target;bounds[ref]=limit;binding[ref]=owner

    # Native footprint geometry at each allowable rotation, computed once.
    geometry={}
    for ref,f in fps.items():
        if ref in fixed:continue
        geometry[ref]={}
        back=boardname=='elevation'
        for angle in (0,90,180,270):
            move(f,0,0,angle,back)
            geometry[ref][angle]=(box(f),[(q.GetNumber(),q.GetNetname(),*xy(q.GetPosition())) for q in f.Pads()])

    placed=dict(fixed)
    # Full body reservations also protect the opposite face from through-hole
    # leads, and protect the stacking sockets from carrier bottom components.
    occupied=list(placed.items())
    for ref in [r for r in fixed if r.startswith('H')]:
        x,y=xy(fps[ref].GetPosition());placed[ref]=(x-4,y-4,x+4,y+4)
    occupied=list(placed.items())
    netanchors=collections.defaultdict(list)
    for ref in fixed:
        for q in fps[ref].Pads():
            if q.GetNetname():netanchors[q.GetNetname()].append((ref,*xy(q.GetPosition())))

    def legal(bb,ref):
        limit=bounds.get(ref,(22,22,138,218))
        if bb[0]<limit[0] or bb[1]<limit[1] or bb[2]>limit[2] or bb[3]>limit[3]:return False
        return not any(overlaps(bb,v) for rr,v in occupied)

    def preference(ref):
        tx,ty=targets.get(ref,(80,120)); parent=binding.get(ref)
        links=[]
        ns={q['net'] for q in old[ref]['pads'] if q['net']}
        for net in ns:
            options=netanchors.get(net,[])
            if parent:
                owned=[v for v in options if v[0]==parent]
                if owned:options=owned
            if not options:continue
            # Avoid pulling local decouplers across the board along shared rails.
            if len(options)>5 and not parent:continue
            best=min(options,key=lambda v:(v[1]-tx)**2+(v[2]-ty)**2)
            links.append((net,best[1],best[2]))
        if ref in binding and ref.startswith('C') and links:
            # Prioritize the non-ground supply pin for local bypass placement.
            sig=[v for v in links if not v[0].startswith(('GND','-BATT'))]
            if sig:
                tx=sum(v[1] for v in sig)/len(sig);ty=sum(v[2] for v in sig)/len(sig)
        return tx,ty,links

    remaining=[r for r in fps if r not in fixed]
    # Decoupling and bulky passives get first claim; test pads are last.
    remaining.sort(key=lambda r:(2 if r.startswith('TP') else 0 if r.startswith('C') else 1,
                                   -((geometry[r][0][0][2]-geometry[r][0][0][0])*(geometry[r][0][0][3]-geometry[r][0][0][1])),r))
    moved=[]
    for ref in remaining:
        tx,ty,links=preference(ref);limit=bounds.get(ref,(22,22,138,218))
        tx=max(limit[0]+2,min(limit[2]-2,tx));ty=max(limit[1]+2,min(limit[3]-2,ty))
        best=None
        for radius in (8,18,35,70):
            # A 0.5 mm placement grid, with all four rotations evaluated.
            candidates=[]
            for ix in range(max(-radius*2,math.ceil((limit[0]-tx)*2)),min(radius*2,math.floor((limit[2]-tx)*2))+1):
                for iy in range(max(-radius*2,math.ceil((limit[1]-ty)*2)),min(radius*2,math.floor((limit[3]-ty)*2))+1):
                    x=round(tx*2)/2+ix*.5;y=round(ty*2)/2+iy*.5
                    distance=(x-tx)**2+(y-ty)**2
                    if distance>radius*radius:continue
                    candidates.append((distance,x,y))
            candidates.sort()
            for dist,x,y in candidates:
                if best and dist*.55>best[0]:break
                for angle,(rel,pads) in geometry[ref].items():
                    bb=(rel[0]+x,rel[1]+y,rel[2]+x,rel[3]+y)
                    if not legal(bb,ref):continue
                    cost=dist*.55
                    for net,px,py in links:
                        matching=[(qx+x,qy+y) for _,nn,qx,qy in pads if nn==net]
                        if matching:cost+=min((qx-px)**2+(qy-py)**2 for qx,qy in matching)*.2
                    if angle==old[ref]['angle']%360:cost-=.05
                    if best is None or cost<best[0]:best=(cost,x,y,angle,bb)
            if best:break
        if best is None:
            (OUT/'failed_placement.json').write_text(json.dumps({'board':boardname,'ref':ref,'box':geometry[ref][0][0],'target':[tx,ty],'limits':limit,'placed':placed},indent=2))
            raise RuntimeError(('No legal position',boardname,ref,targets.get(ref),limit))
        _,x,y,angle,bb=best;move(fps[ref],x,y,angle,boardname=='elevation');placed[ref]=bb;occupied.append((ref,bb))
        moved.append((ref,round(math.hypot(x-tx,y-ty),2)))

    # Keep reference text off component lands and neighbouring legends. In dense
    # areas retain the reference on the assembly layer instead of printing an
    # ambiguous or overlapping silkscreen label.
    legends=[];fab_only=[]
    function_labels=([('STAR STEP',27,45.5),('CAN',27,87.5),('BRAKES',27,129.5),('PORT MOTOR',27,171.5),
                      ('STAR SSI',133,45.5),('PORT SSI',133,87.5),('PORT STEP',133,129.5),('STAR MOTOR',133,171.5),
                      ('MODBUS',104,206),('POWER IN',90,23)] if boardname=='elevation' else
                     [('RESET',40,86),('BOOT',40,98)])
    for label,x,y in function_labels:
        # Reserve nominal bounds before placing reference designators.
        half=len(label)*.8*.35
        legends.append((x-half,y-.5,x+half,y+.5))
        addtext(b,label,x,y,p.B_SilkS if boardname=='elevation' else p.F_SilkS,.8)
    text_order=sorted(fps,key=lambda r:(r.startswith(('C','R','TP')),r))
    for ref in text_order:
        f=fps[ref]
        f.Value().SetVisible(False);r=f.Reference();r.SetVisible(True)
        r.SetTextSize(pt(.8,.8));r.SetTextThickness(p.FromMM(.12));r.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
        r.SetLayer(p.B_SilkS if f.IsFlipped() else p.F_SilkS);r.SetMirrored(f.IsFlipped())
        bb=box(f);cx=(bb[0]+bb[2])/2;cy=(bb[1]+bb[3])/2
        candidates=[]
        for d in (.8,1.3,1.8,2.3,2.8,3.3):
            for offset in (0,-1,1,-2,2):
                candidates += [(cx+offset,bb[1]-d),(cx+offset,bb[3]+d),
                               (bb[0]-d-1.3,cy+offset),(bb[2]+d+1.3,cy+offset)]
        found=False
        for x,y in candidates:
            r.SetPosition(pt(x,y));z=r.GetBoundingBox();rb=tuple(p.ToMM(v) for v in (z.GetLeft(),z.GetTop(),z.GetRight(),z.GetBottom()))
            if rb[0]<20.5 or rb[1]<20.5 or rb[2]>139.5 or rb[3]>219.5:continue
            if any(overlaps(rb,q,.18) for _,q in occupied):continue
            if any(overlaps(rb,q,.18) for q in legends):continue
            legends.append(rb);found=True;break
        if not found:
            r.SetLayer(p.B_Fab if f.IsFlipped() else p.F_Fab);r.SetPosition(pt(cx,cy));fab_only.append(ref)
        if ref in SUPPORTS or ref in HEADERS or ref.startswith('J'):f.SetLocked(True)
    addtext(b,'P5 CONTROLLER | PLACEMENT ONLY' if boardname=='controller' else 'P5 CARRIER | PLACEMENT ONLY',80,217 if boardname=='controller' else 195,p.F_SilkS,1.1)
    addtext(b,'120 x 200 mm / 4 layers / NO ROUTING',80,223,p.Dwgs_User,1.3)
    addtext(b,'OUTWARD FACE: TOP' if boardname=='controller' else 'OUTWARD FACE: BOTTOM',80,227,p.Dwgs_User,1.3)
    # Assembly-only support clearance outlines (not board copper).
    for ref in [r for r in fixed if r.startswith('H')]:
        x,y=xy(fps[ref].GetPosition());rectangle(b,(x-4,y-4),(x+4,y+4),p.Dwgs_User)
    # SaveBoard can serialize the temporary board's project over the target
    # .kicad_pro, dropping schematic BOM presets. Preserve the live settings.
    project_path=ROOT/(project+'.kicad_pro')
    project_bytes=project_path.read_bytes()
    try:
        p.SaveBoard(str(ROOT/(project+'.kicad_pcb')),b)
    finally:
        project_path.write_bytes(project_bytes)
    records=[]
    for ref,f in fps.items():
        records.append({'ref':ref,'value':f.GetValue(),'footprint':f.GetFPIDAsString(),'sheet':old[ref]['sheet'],
                        'x':xy(f.GetPosition())[0],'y':xy(f.GetPosition())[1],'angle':f.GetOrientationDegrees(),
                        'back':f.IsFlipped(),'box':box(f),
                        'pads':[{'pin':q.GetNumber(),'net':q.GetNetname(),'x':xy(q.GetPosition())[0],'y':xy(q.GetPosition())[1],
                                 'size':xy(q.GetSize()),'drill':xy(q.GetDrillSize())} for q in f.Pads()]})
    final[boardname]=records
    collisions=[(a,c) for i,(a,ab) in enumerate(occupied) for c,cb in occupied[i+1:] if overlaps(ab,cb,0)]
    report[boardname]={'footprints':len(fps),'fixed_anchor_overlaps':collisions,
                       'references_on_assembly_layer':fab_only,
                       'largest_passive_displacements':sorted(moved,key=lambda q:-q[1])[:15],
                       'tracks':len(list(b.GetTracks())),'zones':len(list(b.Zones()))}

(OUT/'inventory.json').write_text(json.dumps(final,indent=2))
(OUT/'placement_build.json').write_text(json.dumps(report,indent=2))
data=json.loads((SNAP/'assembly/stack_interface.json').read_text())
data.update({'mechanical_revision':'P5 placement only','controller_origin_mm':list(ORIGIN),'elevation_origin_mm':list(ORIGIN),
             'interface_compatibility':'Electrical pinout P4.1; mate only the matching P5 mechanical pair. Earlier P4 board coordinates differ.',
             'controller_outline_mm':list(SIZE),'elevation_outline_mm':list(SIZE),
             'controller_to_elevation_translation_mm':[0,0],
             'supports_controller_xy_mm':{k:list(v) for k,v in SUPPORTS.items()},
             'carrier_population_face':'B.Cu except stacking sockets',
             'controller_population_face':'F.Cu except stacking headers'})
for ref,(x,y) in HEADERS.items():
    data['connectors'][ref]['controller_origin_xy_mm']=[x+2.54,y]
    data['connectors'][ref]['elevation_origin_xy_mm']=[x,y]
(ROOT/'assembly/stack_interface.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(report,indent=2))

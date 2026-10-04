"""Readable P6 silkscreen without changing components, pads or nets."""
from pathlib import Path
import sys,json,subprocess,re
sys.path.insert(0,'C:/Users/Mauro/AppData/Roaming/Python/Python314/site-packages')
from kicad_sexp import read,save,kids,one
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
def pt(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def box(x):
    z=x.GetBoundingBox(False,False) if isinstance(x,p.FOOTPRINT) else x.GetBoundingBox()
    return tuple(p.ToMM(v) for v in [z.GetLeft(),z.GetTop(),z.GetRight(),z.GetBottom()])
def overlap(a,b,g=.18):return a[0]<b[2]+g and a[2]>b[0]-g and a[1]<b[3]+g and a[3]>b[1]-g
for board,pr in [('controller','controller/Elevation_Controller'),('elevation','Elevation_Pivot_Daughter-Board')]:
    path=ROOT/(pr+'.kicad_pcb');doc=read(path)
    doc[:]=[n for n in doc if not(isinstance(n,list) and n and str(n[0])=='gr_text' and one(n,'layer')[1] in ['F.SilkS','B.SilkS'])]
    save(path,doc)
    b=p.LoadBoard(str(ROOT/(pr+'.kicad_pcb')));fps={f.GetReference():f for f in b.GetFootprints()};obs={False:[],True:[]};leg={False:[],True:[]}
    for r,f in fps.items():
        side=f.IsFlipped();obs[side].append(box(f))
        for q in f.Pads():
            if q.GetDrillSize().x or q.GetDrillSize().y:obs[not side].append(box(q))
        for g in f.GraphicalItems():
            if g.GetLayer() in [p.F_SilkS,p.B_SilkS]:
                bb=box(g)
                if (isinstance(g,p.PCB_TEXT) and g.GetText()=='*') or (r=='J1' and (bb[0]<20.5 or bb[1]<20.5 or bb[2]>99.5 or bb[3]>149.5)):
                    g.SetLayer(p.B_Fab if g.GetLayer()==p.B_SilkS else p.F_Fab)
    names=({'J1003':'STAR STEP','J1006':'PORT STEP','J1002':'STAR SSI','J1004':'PORT SSI','J401':'ETHERNET','J501':'USB','J601':'SWD',
            'SW1':'RESET','SW2':'BOOT','J30':'J30 CLEAN','J31':'J31 FIELD'} if board=='controller' else
           {'J20':'PORT MOTOR','J21':'STAR MOTOR','J7':'BRAKES','J5':'CAN','J22':'MODBUS','J1':'POWER IN','J30':'J30 CLEAN','J31':'J31 FIELD'})
    def locate(t,r,side):
        bb=box(fps[r]);cx=(bb[0]+bb[2])/2;cy=(bb[1]+bb[3])/2
        for delta in [.7,1.2,1.7,2.2,2.7,3.2,4.2]:
            for offset in [0,-1.5,1.5,-3,3]:
                for x,y in [(cx+offset,bb[1]-delta),(cx+offset,bb[3]+delta),(bb[0]-delta-2,cy+offset),(bb[2]+delta+2,cy+offset)]:
                    t.SetPosition(pt(x,y));rb=box(t)
                    if rb[0]<20.5 or rb[1]<20.5 or rb[2]>99.5 or rb[3]>149.5:continue
                    if any(overlap(rb,q) for q in obs[side]+leg[side]):continue
                    leg[side].append(rb);return True
        return False
    for r,s in names.items():
        f=fps[r];side=f.IsFlipped();t=p.PCB_TEXT(b);t.SetText(s);t.SetTextSize(pt(.8,.8));t.SetTextThickness(p.FromMM(.12));t.SetLayer(p.B_SilkS if side else p.F_SilkS);t.SetMirrored(side)
        if locate(t,r,side):b.Add(t)
    n=0
    for r in sorted(fps,key=lambda r:(r.startswith(('C','R','TP')),r)):
        f=fps[r];side=f.IsFlipped();t=f.Reference();t.SetTextSize(pt(.8,.8));t.SetTextThickness(p.FromMM(.12));t.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));t.SetMirrored(side)
        t.SetLayer(p.B_SilkS if side else p.F_SilkS)
        if not(board=='elevation' and r in ['FB2','C47','C101']) and locate(t,r,side):n+=1
        else:t.SetLayer(p.B_Fab if side else p.F_Fab);t.SetPosition(f.GetPosition())
    prfile=ROOT/(pr+'.kicad_pro');raw=prfile.read_bytes()
    try:p.SaveBoard(str(ROOT/(pr+'.kicad_pcb')),b)
    finally:prfile.write_bytes(raw)
    # KiCad's real solder-mask geometry can extend beyond our body envelopes.
    # Move only reported reference collisions to Fab, without repacking labels.
    report=ROOT/'outputs/compact'/(board+'_silk_check.json')
    subprocess.run(['C:/Program Files/KiCad/9.0/bin/kicad-cli.exe','pcb','drc','--format','json','--severity-all','-o',str(report),str(ROOT/(pr+'.kicad_pcb'))],check=True,capture_output=True)
    changed=False
    for v in json.loads(report.read_text())['violations']:
        if v['type'] not in ['silk_over_copper','silk_overlap']:continue
        for item in v['items']:
            match=re.fullmatch(r'Reference field of (\S+)',item['description'])
            if match:
                f=fps[match[1]];f.Reference().SetLayer(p.B_Fab if f.IsFlipped() else p.F_Fab);f.Reference().SetPosition(f.GetPosition());changed=True
    if changed:
        try:p.SaveBoard(str(ROOT/(pr+'.kicad_pcb')),b)
        finally:prfile.write_bytes(raw)
    print(board,n,'references on silk; remaining identifiers on assembly layer')

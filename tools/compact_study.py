"""Read-only area and interface study of the preserved P5 assembly."""
from pathlib import Path
import sys,json,collections
sys.path.insert(0,str(Path(__file__).resolve().parent))
from validate_stack import netlist
ROOT=Path(__file__).resolve().parents[1]
inv=json.loads((ROOT/'outputs/placement/inventory.json').read_text())
data={b:netlist(ROOT/f'outputs/p4_{b}.xml') for b in inv}
parent={}
def find(x):
    parent.setdefault(x,x)
    if parent[x]!=x:parent[x]=find(parent[x])
    return parent[x]
def join(a,b):parent[find(a)]=find(b)
for b,(_,ns,_) in data.items():
    for n in ns:find((b,n))
for r in ['J30','J31']:
    for pin in range(1,31 if r=='J30' else 21):
        join(('elevation',data['elevation'][2][r,str(pin)]),('controller',data['controller'][2][r,str(pin)]))
groups=collections.defaultdict(set)
for b,(_,ns,_) in data.items():
    for n,ps in ns.items():
        groups[find((b,n))].update((b,r,p) for r,p in ps if r not in ['J30','J31'])
for moved in [
    {'/SSI_Encoder/','/Stepper/'},
    {'/SSI_Encoder/','/Stepper/','/DC DC Step down/'},
    {'/SSI_Encoder/','/Stepper/','/DC DC Step down/','/ServoMotor/'},
    {'/SSI_Encoder/','/Stepper/','/ServoMotor/'}]:
    partition={(b,f['ref']):('controller' if b=='controller' or f['sheet'] in moved else 'elevation') for b,fs in inv.items() for f in fs}
    area=collections.Counter();count=collections.Counter();ports=collections.defaultdict(list)
    for b,fs in inv.items():
        for f in fs:
            bb=f['box'];target=partition[b,f['ref']];area[target]+=(bb[2]-bb[0])*(bb[3]-bb[1]);count[target]+=1
            if 'DSUB' in f['footprint'].upper():ports[target].append(f['ref'])
    crossing={k:v for k,v in groups.items() if len({partition[b,r] for b,r,p in v})==2}
    print(moved,'area',dict(area),'count',dict(count),'ports',dict(ports),'crossing',len(crossing))
    print(list(crossing))

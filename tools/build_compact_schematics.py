"""P6 board redistribution from preserved P5; never changes component selections.

Moves the complete SSI and stepper interface sheets to the controller. Keeps
their circuit drawings, UUIDs, properties and relative geometry. Ref numbers on
the moved sheets gain 1000 to avoid conflicts with controller references.
"""
from pathlib import Path
import copy,json,re,sys,collections,shutil
from kicad_sexp import *
from validate_stack import netlist
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'_work/p6_baseline'
from prepare_compact_baseline import ensure_baseline
ensure_baseline()
OUT=ROOT/'outputs/compact';OUT.mkdir(parents=True,exist_ok=True)
PROJECTS={'controller':'controller/Elevation_Controller','elevation':'Elevation_Pivot_Daughter-Board'}
MOVED={'Stepper.kicad_sch':'10_stepper_interfaces.kicad_sch','SSI_Encoder.kicad_sch':'11_ssi_interfaces.kicad_sch'}
ALIASES={'GND_STM32':'GND','+3V3_STM32':'3V3_DIG','+5V_STM32':'B2B_5V_IN','CTRL_NRST':'NRST'}
HIER={'PORT_ENC_PRESET':'PORT_ENC_PRESET_N','STAR_ENC_PRESET':'STAR_ENC_PRESET_N'}
inv=json.loads((BASE/'inventory.json').read_text())
roots={b:read(BASE/(p+'.kicad_sch')) for b,p in PROJECTS.items()}
root_ids={b:one(d,'uuid')[1] for b,d in roots.items()}
sheetids={prop(s,'Sheetfile')[2]:one(s,'uuid')[1] for d in roots.values() for s in kids(d,'sheet')}
mapping=[]
for b,fs in inv.items():
    for f in fs:
        moved=b=='elevation' and f['sheet'] in ['/Stepper/','/SSI_Encoder/']
        ref=f['ref'];new=re.sub(r'\d+',lambda m:str(int(m[0])+1000),ref) if moved else ref
        mapping.append({'source_board':b,'source_ref':ref,'board':'controller' if moved else b,'ref':new,'source_sheet':f['sheet']})
refmap={(x['source_board'],x['source_ref']):x['ref'] for x in mapping}

def setinstance(n,project,path,ref):
    n[:]=[x for x in n if not(isinstance(x,list) and x and str(x[0])=='instances')]
    n.append([S('instances'),[S('project'),project,[S('path'),path,[S('reference'),ref],[S('unit'),one(n,'unit')[1]]]]])

def globalize(d):
    for n in kids(d,'hierarchical_label'):
        n[0]=S('global_label');n[1]=HIER.get(n[1],n[1])
    names={n[1] for n in kids(d,'global_label')}
    # Existing service labels name the same net; make their scope explicit.
    for n in kids(d,'label'):
        if n[1] in names:
            n[0]=S('global_label');n.insert(2,[S('shape'),S('bidirectional')])

# Canonical controller supply symbols for the relocated sheets only.
powerlibs={}
for fn in ['03_mcu_core.kicad_sch','07_stack_interface.kicad_sch']:
    d=read(BASE/'controller'/fn)
    for n in kids(d,'symbol'):
        if prop(n,'Reference')[2].startswith('#'):
            powerlibs[prop(n,'Value')[2]]=copy.deepcopy(library(d,n))

for f in BASE.glob('*.kicad_sch'):
    if f.name==PROJECTS['elevation']+'.kicad_sch':continue
    d=read(f);globalize(d)
    if f.name in MOVED:
        lib=one(d,'lib_symbols')
        for n in kids(d,'symbol'):
            old=prop(n,'Reference')[2]
            ref=('#PWRP6'+old.lstrip('#PWR')) if old.startswith('#') else refmap['elevation',old]
            prop(n,'Reference')[2]=ref
            setinstance(n,'Elevation_Controller','/'+root_ids['controller']+'/'+sheetids[f.name],ref)
            val=prop(n,'Value')[2]
            if old.startswith('#') and val in ALIASES:
                canonical=ALIASES[val];template=powerlibs[canonical]
                prop(n,'Value')[2]=canonical;one(n,'lib_id')[1]=template[1]
                if not any(x[1]==template[1] for x in kids(lib,'symbol')):lib.append(copy.deepcopy(template))
            if not old.startswith('#'):
                fp=prop(n,'Footprint');fp[2]='Field_'+fp[2] if fp[2] else ''
        for n in kids(lib,'symbol'):
            if not n[1].startswith('Controller_Power:'):n[1]='Field_'+n[1]
        for n in kids(d,'symbol'):
            lid=one(n,'lib_id')
            if not lid[1].startswith('Controller_Power:'):lid[1]='Field_'+lid[1]
        dest=ROOT/'controller'/MOVED[f.name]
    else:dest=ROOT/f.name
    save(dest,d)

# Preserve non-carrier controller schematic sheets verbatim initially.
for f in (BASE/'controller').glob('*.kicad_sch'):
    if f.name!='Elevation_Controller.kicad_sch':(ROOT/'controller'/f.name).write_bytes(f.read_bytes())

# Rebuild root sheet overviews; circuit drawings remain on their child sheets.
for board,d in list(roots.items()):
    sheets=kids(d,'sheet')
    if board=='elevation':sheets=[s for s in sheets if prop(s,'Sheetfile')[2] not in MOVED]
    else:
        for s in kids(roots['elevation'],'sheet'):
            fn=prop(s,'Sheetfile')[2]
            if fn in MOVED:
                s=copy.deepcopy(s);prop(s,'Sheetfile')[2]=MOVED[fn];sheets.append(s)
    # roots['elevation'] isn't mutated until sheets have been copied below.
    roots[board+'_sheets']=sheets
for board in PROJECTS:
    d=roots[board];sheets=roots[board+'_sheets']
    keep={'version','generator','generator_version','uuid','paper','title_block','lib_symbols','sheet_instances','embedded_fonts'}
    d[:]=[x for x in d if not isinstance(x,list) or not x or str(x[0]) in keep]
    one(d,'paper')[1]='A3'
    for i,s in enumerate(sheets):
        s[:]=[x for x in s if not(isinstance(x,list) and x and str(x[0]) in ('pin','instances'))]
        x=25.4+(i%3)*129.54;y=60.96+(i//3)*45.72
        at=one(s,'at');dx=x-at[1];dy=y-at[2];translate(s,dx,dy)
        one(s,'size')[1:]=[111.76,25.4]
        for key,yy in [('Sheetname',y-1.27),('Sheetfile',y+27.94)]:one(prop(s,key),'at')[1:]=[x,yy,0]
        s.append([S('instances'),[S('project'),Path(PROJECTS[board]).name,[S('path'),'/'+root_ids[board],[S('page'),str(i+2)]]]])
        d.append(s)
    note(d,'p6-root-'+board,'P6 COMPACT STACK - 80 x 130 mm placement attempt',25.4,20.32,2.54)
    note(d,'p6-root-note-'+board,'P6 pinout only. J30: clean logic. J31: field power. Never mate with P4/P5 boards.\nCircuit functions and BOM selections retained; no routing.',25.4,30.48,1.524)
    save(ROOT/(PROJECTS[board]+'.kicad_sch'),d)

# Explicit domain-separated mating pinout, retaining the same purchased headers.
logic=['PORT_BRAKE_RELEASE_CMD','STAR_BRAKE_RELEASE_CMD','HOME_POS','E_STOP_OK',
       'PORT_ENC_A','PORT_ENC_B','PORT_ENC_Z','STAR_ENC_A','STAR_ENC_B','STAR_ENC_Z',
       'STM32_SCL','STM32_SDA','TX_CAN','RX_CAN','Silent_Mode',
       'PIVOT_MODBUS_TX','PIVOT_MODBUS_RX','PIVOT_MODBUS_DE','NRST']
# 19 logic signals + 2 x 5 V + 2 x 3.3 V + 7 grounds = 30.
j30=['GND','GND']+logic[:10]+['GND','GND']+logic[10:]+['GND','B2B_5V_IN','B2B_5V_IN','3V3_DIG','3V3_DIG','GND','GND']
assert len(j30)==30
j31=['-BATT']*4+['+5V_FIELD']*2+['-BATT']*2+['+6.5V_ENC_PORT']*2+['+5V_ENC_PORT']*2+['-BATT']*2+['+6.5V_ENC_STAR']*2+['+5V_ENC_STAR']*2+['-BATT']*2
pinout={'J30':{str(i+1):n for i,n in enumerate(j30)},'J31':{str(i+1):n for i,n in enumerate(j31)}}
for board,fn in [('controller','controller/07_stack_interface.kicad_sch'),('elevation','STM32.kicad_sch')]:
    d=read(BASE/fn)
    # Keep physical PCB features and full procurement fields, remove old wiring.
    symbols=[n for n in kids(d,'symbol') if not prop(n,'Reference')[2].startswith('#')]
    keep={'version','generator','generator_version','uuid','paper','title_block','lib_symbols','sheet_instances','embedded_fonts'}
    d[:]=[n for n in d if not isinstance(n,list) or not n or str(n[0]) in keep]
    one(d,'paper')[1]='A3'
    for n in symbols:
        ref=prop(n,'Reference')[2];at=one(n,'at');pos={'J30':(95.25,60.96),'J31':(292.1,60.96),'TP30':(81.28,200.66)}.get(ref)
        if ref.startswith('H'):pos=(90+(int(ref[1:])-30)*45,220)
        if pos:translate(n,pos[0]-at[1],pos[1]-at[2])
        d.append(n)
        if ref in pinout:
            for pin,(x,y) in pins(library(d,n),n).items():
                net=pinout[ref][pin]
                if board=='elevation':net={v:k for k,v in ALIASES.items()}.get(net,net)
                side=-1 if int(pin)%2 else 1
                end=(round(x+side*15.24,4),y)
                wire(d,f'p6-{board}-{ref}-{pin}',(x,y),end)
                label(d,f'p6-{board}-{ref}-{pin}-label',net,end,180 if side<0 else 0)
        elif ref=='TP30':
            x,y=next(iter(pins(library(d,n),n).values()));label(d,'p6-tp30','CTRL_NRST',(x,y))
    note(d,'p6-stack-'+board,'P6 STACK INTERFACE - incompatible with P4/P5 pinout',25.4,20.32,2.54)
    note(d,'p6-logic-'+board,'J30 CLEAN LOGIC / STM32 GROUND',35.56,35.56,1.524)
    note(d,'p6-field-'+board,'J31 FIELD SUPPLIES / -BATT RETURN\nSSI local 5 V and preregulator connections retained',233.68,35.56,1.524)
    note(d,'p6-stack-safety-'+board,'Keep J30 clean copper separate from J31 field copper. No field current on STM32 grounds.\nParallel supply contacts retained; confirm actual loads and derating before release.',25.4,175.26,1.27)
    # Connector pins are passive: mark only rails entering from the mate.
    flagdoc=read(BASE/'controller/03_mcu_core.kicad_sch')
    template=next(n for n in kids(flagdoc,'symbol') if prop(n,'Value')[2]=='PWR_FLAG')
    flaglib=copy.deepcopy(library(flagdoc,template))
    if not any(n[1]==flaglib[1] for n in kids(one(d,'lib_symbols'),'symbol')):one(d,'lib_symbols').append(flaglib)
    flag_nets=(['-BATT','+5V_FIELD','+6.5V_ENC_PORT','+5V_ENC_PORT','+6.5V_ENC_STAR','+5V_ENC_STAR'] if board=='controller' else ['+3V3_STM32'])
    for i,net in enumerate(flag_nets):
        n=copy.deepcopy(template);ref='#FLGP6'+str(i+1);x=40.64+50.8*i;y=152.4
        at=one(n,'at');translate(n,x-at[1],y-at[2]);prop(n,'Reference')[2]=ref;one(n,'uuid')[1]=uid(board+ref)
        setinstance(n,Path(PROJECTS[board]).name,'/'+root_ids[board]+'/'+sheetids[Path(fn).name],ref)
        d.append(n);label(d,'p6-flag-'+board+str(i),net,(x,y))
    save(ROOT/fn,d)

# Relocated symbols/footprints keep their existing project-local libraries.
for table,key in [('fp-lib-table','uri'),('sym-lib-table','uri')]:
    dst=read(BASE/'controller'/table);names={one(x,'name')[1] for x in kids(dst,'lib')}
    for lib in kids(read(BASE/table),'lib'):
        lib=copy.deepcopy(lib);one(lib,'name')[1]='Field_'+one(lib,'name')[1]
        uri=one(lib,'uri');uri[1]=uri[1].replace('${KIPRJMOD}/','${KIPRJMOD}/../');dst.append(lib)
    save(ROOT/'controller'/table,dst)
manifest={'revision':'P6 compact attempt','preserved_commit':'29b4387','size_mm':[80,130],
          'moved_sheets':MOVED,'reference_mapping':mapping,'pinout':pinout,'supply_aliases':ALIASES}
(ROOT/'assembly/compact_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for filename in MOVED:
    # Preserve inactive originals as well as the P5 Git checkpoint.
    source=ROOT/filename;dest=ROOT/'docs/archive'/filename
    if source.exists() and not dest.exists():
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(source,dest)
import runpy
runpy.run_path(str(ROOT/'tools/finish_compact_schematic_style.py'),run_name='__main__')
print('P6 schematics and explicit ref/pin migration manifest written.')

"""P6 drawing-only cleanup: outward header labels, hidden metadata and titles."""
from pathlib import Path
from kicad_sexp import *
ROOT=Path(__file__).resolve().parents[1]
for file in [*ROOT.glob('*.kicad_sch'),*(ROOT/'controller').glob('*.kicad_sch')]:
    d=read(file)
    if kids(d,'title_block'):
        tb=one(d,'title_block')
        if kids(tb,'rev'):one(tb,'rev')[1]='P6 COMPACT'
        else:tb.append([S('rev'),'P6 COMPACT'])
    if file.name in ['Elevation_Controller.kicad_sch','Elevation_Pivot_Daughter-Board.kicad_sch']:
        for sh in kids(d,'sheet'):
            for key in ['Sheetname','Sheetfile']:one(prop(sh,key),'at')[3]=0
    if file.name in ['STM32.kicad_sch','07_stack_interface.kicad_sch']:
        for sym in kids(d,'symbol'):
            for pr in kids(sym,'property'):
                if pr[1] in ['Reference','Value']:continue
                eff=one(pr,'effects')
                if not kids(eff,'hide'):eff.append([S('hide'),S('yes')])
        for lab in kids(d,'global_label'):
            at=one(lab,'at');x,y=at[1:3]
            if y<140:
                # Connector centres are 95.25 and 292.1; flags are below y=140.
                centre=95.25 if x<200 else 292.1
                angle=180 if x<centre else 0;at[3]=angle
                eff=one(lab,'effects');one(eff,'justify')[1:]=[S('left' if angle==0 else 'right')]
    save(file,d)
print('P6 schematic labels and revision titles checked')

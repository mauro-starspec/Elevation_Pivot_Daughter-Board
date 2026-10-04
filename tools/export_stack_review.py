"""Export both KiCad schematics with a concise architecture/assembly/pinout cover.

Requires PyMuPDF and KiCad 9. Output stays in the repository's ignored outputs/.
"""
from pathlib import Path
import json
import shutil
import subprocess
import pymupdf as pdf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)
DATA=json.loads((ROOT/'assembly/stack_interface.json').read_text())
REPORT=json.loads((OUT/'p4_stack_validation.json').read_text())
CLI=shutil.which('kicad-cli') or 'C:/Program Files/KiCad/9.0/bin/kicad-cli.exe'
for name,project in [('Controller','controller/Elevation_Controller'),('Elevation','Elevation_Pivot_Daughter-Board')]:
    subprocess.run([CLI,'sch','export','pdf','-o',str(OUT/f'P4_{name}_Review.pdf'),str(ROOT/(project+'.kicad_sch'))],check=True)

doc=pdf.open();W,H=1190.55,841.89
INK=(.08,.15,.20);TEAL=(.05,.40,.42);GRAY=(.37,.43,.47)
def text(page,x,y,s,size=12,color=INK,bold=False):
    page.insert_text((x,y),s,fontsize=size,fontname='hebo' if bold else 'helv',color=color)
def box(page,r,s,size=12,color=INK):
    result=page.insert_textbox(pdf.Rect(*r),s,fontsize=size,fontname='helv',color=color,lineheight=1.35)
    assert result>=0,(s,result)
def base(title,kicker):
    p=doc.new_page(width=W,height=H)
    p.draw_rect(pdf.Rect(0,0,W,14),color=TEAL,fill=TEAL)
    text(p,48,58,'STARSPEC  /  ELEVATION + PIVOT',11,TEAL,True)
    text(p,48,103,title,29,bold=True)
    text(p,48,132,kicker,12,GRAY)
    p.draw_line((48,777),(1142,777),color=(.78,.82,.83))
    text(p,48,801,'P4.1 ELECTRICAL / P5 PLACEMENT  |  2026-10-03  |  Routing and qualification remain open',10,GRAY)
    text(p,1090,801,str(len(doc)),10,GRAY)
    return p
def panel(p,r,title,lines,fill):
    p.draw_rect(pdf.Rect(*r),color=TEAL,fill=fill,width=1)
    text(p,r[0]+20,r[1]+30,title,17,TEAL,True)
    box(p,(r[0]+20,r[1]+48,r[2]-20,r[3]-12),lines,13)

p=base('Custom STM32H723 controller + elevation carrier','One repository, two matched KiCad projects. Both 120 x 200 mm PCBs placed; no routing or copper zones.')
panel(p,(48,175,535,380),'UPPER BOARD - CONTROLLER',
      'STM32H723 processor, clocks and reset\nEthernet, USB-C and external SWD / serial debug\nWatchdog, status LEDs and 5 V to 3.3 V conversion\nUnused ADC / expansion / monitoring circuits removed',(.93,.97,.97))
panel(p,(650,175,1142,380),'LOWER BOARD - ELEVATION CARRIER',
      'Field power, brakes, drive commands and faults\nBoth SSI channels + both DE9 motor encoders\nCAN + isolated pivot Modbus RTU / RS-485\nExisting ADC + two passive 1206 temperature sensors',(.96,.97,.95))
p.draw_line((535,257),(650,257),color=TEAL,width=2)
text(p,550,232,'J30 + J31',13,TEAL,True)
text(p,552,281,'50 contacts',11,TEAL)
text(p,48,421,'POWER PATH',13,TEAL,True)
box(p,(48,441,1142,503),'Carrier isolated PS4 -> 5 V across J30 -> controller automatic-retry input protection -> 3.3 V buck.\nThe 3.3 V rail returns through J30 to the carrier clean-side logic. Field grounds remain separate.',14)
text(p,48,537,'VERIFIED FOR THIS REVIEW',13,TEAL,True)
box(p,(48,555,590,687),
    f"Both schematics: 0 ERC findings, 0 exclusions\n{REPORT['preserved_carrier_net_groups']} carrier net groups preserved\n9 original field drawings preserved\n{REPORT['application_gpio']} application GPIOs + reset and power\n50 physical mating pads + 4 matched support pairs",13)
text(p,650,537,'REVIEW BOUNDARY',13,TEAL,True)
box(p,(650,555,1142,693),
    'Confirm servo model and cable pinout. Firmware is unchanged.\nBoth boards must use P4.1 electrical / P5 mechanical.\nPlacement is complete. Controller footprint/rule findings, routing, cable fit and bench / environmental qualification remain open.',13)
text(p,48,739,'Following pages: assembly dimensions, full pinout, 9 controller sheets, then 12 carrier sheets.',12,GRAY)

p=base('Nominal sandwich assembly','Controller headers on the underside; carrier sockets on top. Both boards shown in assembled top view.')
# Drawing uses actual dimensions and source coordinates, scaled to points.
scale=2.3;ox,oy=85,182
def pos(x,y):return (ox+(x-20)*scale,oy+(y-20)*scale)
def rect(x,y,w,h):
    a=pos(x,y);b=pos(x+w,y+h);return pdf.Rect(*a,*b)
p.draw_rect(rect(20,20,120,200),color=INK,fill=(.95,.96,.95))
p.draw_rect(rect(20,20,120,200),color=TEAL,fill=(.82,.92,.91),fill_opacity=.65,width=1.5)
text(p,85,167,'Both boards: 120 x 200 mm',13,bold=True)
text(p,120,269,'Matching outlines',12,TEAL,True)
text(p,120,286,'Components face outward',11,TEAL)
for ref,c in DATA['connectors'].items():
    x,y=c['elevation_origin_xy_mm']
    p.draw_rect(rect(x-1.25,y-1.27,5.05,c['rows']*2.54+.51),color=TEAL,fill=(.18,.35,.35))
    a=pos(x+7,y+8);text(p,*a,ref,11,TEAL,True)
for ref,(x,y) in DATA['supports_controller_xy_mm'].items():
    a=pos(x,y);p.draw_circle(a,4.24,color=INK,fill=(1,1,1))
    text(p,a[0]+8,a[1]-7,ref,9)
text(p,85,678,'Tall converters face below the carrier.',11,GRAY)
text(p,430,192,'ASSEMBLY DATUMS',13,TEAL,True)
box(p,(430,211,1118,316),
    'Controller-to-carrier XY translation: (0, 0) mm.\nSame contact number mates to the same contact number on each board.\nJ30: 30 contacts. J31: 20 contacts. Four 3.2 mm M3 clearance holes.\nThe asymmetrical supports assist orientation; headers remain unshrouded.',14)
text(p,430,355,'SIDE VIEW - NOMINAL',13,TEAL,True)
p.draw_rect(pdf.Rect(480,400,1070,413),color=TEAL,fill=(.15,.45,.35))
p.draw_rect(pdf.Rect(480,536,1070,549),color=TEAL,fill=(.15,.45,.35))
p.draw_rect(pdf.Rect(588,413,627,438),color=INK,fill=(.18,.18,.18))
p.draw_rect(pdf.Rect(588,450,627,536),color=INK,fill=(.18,.18,.18))
for x in [598,617]:p.draw_line((x,438),(x,500),color=(.68,.50,.16),width=4)
p.draw_rect(pdf.Rect(955,413,980,536),color=GRAY,fill=(.78,.80,.81))
p.draw_line((1100,413),(1100,536),color=INK)
p.draw_line((1088,413),(1112,413),color=INK);p.draw_line((1088,536),(1112,536),color=INK)
text(p,710,391,'1.6 mm controller PCB',12)
text(p,710,570,'1.6 mm carrier PCB',12)
text(p,705,464,'12 mm face-to-face gap',16,TEAL,True)
text(p,705,489,'5.02 mm nominal contact insertion',12)
text(p,705,511,'SSW permitted range: 3.68-6.35 mm',12)
text(p,945,591,'12 mm support',10,GRAY)
box(p,(430,620,1135,752),
    'STEP includes boards, connectors, supports and conservative converter envelopes. Connector dimensions come from Samtec TSW / SSW drawings.\nReserve 17.5 mm plus tolerance below the carrier. Final cable, enclosure and assembly tolerances remain open.\nMechanical coordinates and sources: assembly/README.md.',12)

p=base('Complete board-to-board pinout','Signal names are shared; carrier aliases: GND_STM32, +5V_STM32, +3V3_STM32 and CTRL_NRST.')
signals={s['signal']:s for s in DATA['application_signals']}
for col,ref in enumerate(['J30','J31']):
    x=48+col*555;y=185;width=525
    text(p,x,y,ref+(' / 30 contacts' if ref=='J30' else ' / 20 contacts'),17,TEAL,True)
    p.draw_rect(pdf.Rect(x,y+13,x+width,y+36),color=TEAL,fill=TEAL)
    for dx,label in [(9,'PIN'),(52,'SIGNAL'),(305,'GPIO'),(376,'MCU PAD')]:text(p,x+dx,y+29,label,10,(1,1,1),True)
    for row,(pin,sig) in enumerate(DATA['connectors'][ref]['pins'].items()):
        yy=y+37+row*16.7
        if row%2==0:p.draw_rect(pdf.Rect(x,yy,x+width,yy+16.7),color=None,fill=(.95,.97,.97))
        s=signals.get(sig,{})
        for dx,val in [(9,pin),(52,sig),(305,s.get('mcu_gpio','')),(376,s.get('mcu_pad',''))]:text(p,x+dx,yy+12,val,10)
box(p,(603,595,1128,735),
    'Modbus: USART2 PD5 TX / PD6 RX / PD4 DE, AF7.\nJ31-13/14/18 replace ground contacts: match P4.1 boards.\nPort A/B: TIM2 PA5/PB3. Star A/B: TIM3 PC6/PC7.\nStar STEP: TIM5 PA0. PB3 SWO disconnected.\nPC2_C: close the internal analog switch.\nTwo 5 V inputs, two 3.3 V returns, thirteen grounds.',12)

toc=[[1,'Architecture and review status',1],[1,'Nominal assembly',2],[1,'Complete interface pinout',3]]
for name in ['Controller','Elevation']:
    src=pdf.open(OUT/f'P4_{name}_Review.pdf');start=len(doc)+1
    doc.insert_pdf(src);toc.append([1,name+' schematics',start]);src.close()
doc.set_toc(toc)
doc.set_metadata({'title':'P4.1 Electrical / P5 Placement - Elevation Controller Stack','author':'Starspec','subject':'Two-board schematic review; P5 equal outlines; no routing'})
path=OUT/'P4_Stack_Schematic_Review.pdf';doc.save(path,garbage=4,deflate=True)
for i in range(3):doc[i].get_pixmap(matrix=pdf.Matrix(1.5,1.5)).save(OUT/f'p4_cover_{i+1}.png')
print(f'{len(doc)} pages exported: {path}')

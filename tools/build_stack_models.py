"""Create drawing-derived connector envelopes and a nominal two-board assembly.

Requires cadquery. Models show external dimensions, not contact-spring detail.
"""
from pathlib import Path
import json, shutil
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'assembly/stack_interface.json').read_text(encoding='utf8'))
OUT=ROOT/'hardware/3d';OUT.mkdir(parents=True,exist_ok=True)
def connector(rows,socket):
    typ='SSW' if socket else 'TSW';lead='01' if socket else '07'
    name=f'Samtec_{typ}-1{rows:02d}-{lead}-S-D'
    a=cq.Assembly(name=name);length=rows*2.54+(.51 if socket else 0)
    width=4.95 if socket else 5.08;height=8.51 if socket else 2.54;base=.13 if socket else 0
    body=cq.Workplane('XY').box(width,length,height).translate((1.27,-(rows-1)*2.54/2,base+height/2))
    positions=[(x,-i*2.54) for i in range(rows) for x in (0,2.54)]
    if socket:
        holes=cq.Workplane('XY').pushPoints(positions).rect(.9,.9).extrude(6.35).translate((0,0,base+height-6.35))
        body=body.cut(holes)
    a.add(body,name='insulator',color=cq.Color(.12,.12,.12))
    for i,(x,y) in enumerate(positions):
        metal=cq.Workplane('XY').box(.41,.79,2.64).translate((x,y,base-1.32)) if socket else cq.Workplane('XY').box(.635,.635,10.92).translate((x,y,2.92))
        a.add(metal,name=f'contact_{i+1}',color=cq.Color(.8,.7,.3))
    path=OUT/(name+'.step');a.save(str(path))
    shutil.copy2(path,ROOT/'controller/hardware/3d'/path.name)
    return name,a.toCompound()
models={}
for rows in (15,10):
    for sock in (False,True):name,shape=connector(rows,sock);models[name]=shape
assembly=cq.Assembly(name='Elevation_'+DATA.get('mechanical_revision','P4').split()[0]+'_nominal_stack')
thick=DATA['pcb_thickness_mm'];gap=DATA['board_gap_mm'];cx,cy=DATA['controller_to_elevation_translation_mm']
# Assembly XY follows KiCad X and inverted Y. Elevation top copper is z=0.
for controller in (False,True):
    ox,oy=DATA['controller_origin_mm'] if controller else DATA['elevation_origin_mm']
    w,h=DATA['controller_outline_mm'] if controller else DATA['elevation_outline_mm']
    if controller:ox+=cx;oy+=cy
    z=gap+thick/2 if controller else -thick/2
    body=cq.Workplane('XY').box(w,h,thick).translate((ox+w/2,-oy-h/2,z))
    holes=[]
    for x,y in DATA['supports_controller_xy_mm'].values():holes.append((x+cx,-y-cy))
    if not controller:
        holes.extend([(x,-y) for x,y in DATA['enclosure_holes_elevation_xy_mm'].values()] if 'enclosure_holes_elevation_xy_mm' in DATA else
                     [(134,-26),(134,-214),(26,-26),(26,-214)] if DATA.get('mechanical_revision','').startswith('P5')
                     else [(164,-26),(164,-182.5),(84,-26),(84,-182.5)])
    cutter=cq.Workplane('XY').pushPoints(holes).circle(1.6).extrude(30,both=True)
    body=body.cut(cutter)
    assembly.add(body,name='controller_pcb' if controller else 'elevation_pcb',color=cq.Color(.07,.32,.19, .85 if controller else 1))
for ref,info in DATA['connectors'].items():
    # Socket front orientation 0; header back orientation 180 mirrors X in plan.
    sx,sy=info['elevation_origin_xy_mm']
    socket=models['Samtec_'+info['elevation_part']].rotate((0,0,0),(0,0,1),info.get('elevation_angle_deg',0)).translate((sx,-sy,0))
    hx,hy=info['controller_origin_xy_mm'];hx+=cx;hy+=cy
    header=models['Samtec_'+info['controller_part']].rotate((0,0,0),(0,1,0),180).rotate((0,0,0),(0,0,1),info.get('controller_angle_deg',180)-180).translate((hx,-hy,gap))
    assembly.add(socket,name=ref+'_socket',color=cq.Color(.16,.16,.16))
    assembly.add(header,name=ref+'_header',color=cq.Color(.22,.22,.22))
for ref,(x,y) in DATA['supports_controller_xy_mm'].items():
    spacer=cq.Workplane('XY').circle(3).circle(1.6).extrude(gap).translate((x+cx,-y-cy,0))
    assembly.add(spacer,name=ref+'_12mm_spacer',color=cq.Color(.72,.72,.74))
if DATA.get('mechanical_revision','').startswith(('P5','P6')):
    # Conservative rectangular converter envelopes make the outward-facing
    # population strategy explicit. These are not vendor solid models.
    inventory=json.loads((ROOT/DATA.get('placement_inventory','outputs/placement/inventory.json')).read_text())
    for f in inventory['elevation']:
        if f['ref'] not in ('PS1','PS2','PS4','PS5','PS6','PS10','PS11'):continue
        x0,y0,x1,y1=f['box'];height=10.2 if f['ref']=='PS4' else 17.5
        shape=cq.Workplane('XY').box(x1-x0,y1-y0,height).translate(((x0+x1)/2,-(y0+y1)/2,-thick-height/2))
        assembly.add(shape,name=f['ref']+'_outward_body_envelope',color=cq.Color(.24,.27,.30))
assembly.save(str(ROOT/'assembly/Elevation_Stack_Mechanical.step'))
insertion=2.54+5.84+8.51+.13-gap
assert 3.68<=insertion<=6.35
(OUT/'stack_models.json').write_text(json.dumps({'provenance':'Project-authored envelopes from Samtec TSW/SSW drawings; no contact-spring or component-clearance certification','nominal_insertion_mm':round(insertion,2),'socket_insertion_range_mm':[3.68,6.35],'pcb_face_gap_mm':gap,'pcb_thickness_mm':thick,'tail_projection_beyond_1_6mm_pcb_mm':{'header':.94,'socket':.91}},indent=2)+'\n',encoding='utf8')
print('Four connector STEP envelopes and mechanical stack saved; nominal insertion',round(insertion,2),'mm')

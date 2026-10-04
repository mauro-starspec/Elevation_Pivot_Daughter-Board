"""Publish the P6 mechanical/electrical interface from the checked manifest."""
from pathlib import Path
import json,csv
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'assembly/compact_manifest.json').read_text())
d=json.loads((ROOT/'_work/p6_baseline/assembly/stack_interface.json').read_text())
d.update({'revision':'P6','mechanical_revision':'P6 compact placement attempt',
 'controller_outline_mm':[80,130],'elevation_outline_mm':[80,130],
 'controller_origin_mm':[20,20],'elevation_origin_mm':[20,20],
 'controller_to_elevation_translation_mm':[0,0],'supports_controller_xy_mm':m['supports_xy_mm'],
 'enclosure_holes_elevation_xy_mm':{'H7':[25,80],'H5':[95,80],'H8':[36,145],'H6':[84,145]},
 'carrier_population_face':'Both; tall converters and field sockets B.Cu outward; small interfaces F.Cu inward',
 'controller_population_face':'Both; field sockets, Ethernet, USB and debug F.Cu outward; MCU/power B.Cu inward',
 'interface_compatibility':'P6 ONLY. J30 clean logic, J31 field supplies. Never mate with P4/P5 boards.',
 'placement_inventory':'outputs/compact/inventory.json'})
for ref,c in d['connectors'].items():
 x,y=m['header_origins_carrier'][ref]
 c.update({'pins':m['pinout'][ref],'elevation_origin_xy_mm':[x,y],
           'controller_origin_xy_mm':[x,y-2.54],'elevation_angle_deg':90,'controller_angle_deg':270})
for s in d['application_signals']:
 s['crosses_stack']=s['signal'] in m['pinout']['J30'].values()
(ROOT/'assembly/stack_interface.json').write_text(json.dumps(d,indent=2)+'\n')
signals={s['signal']:s for s in d['application_signals']}
with (ROOT/'assembly/stack_pinout.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['Revision','Connector','Pin','Controller net','Carrier net','MCU GPIO','MCU pad','Domain'])
 for ref,c in d['connectors'].items():
  for pin,n in c['pins'].items():
   s=signals.get(n,{});w.writerow(['P6',ref,pin,n,{v:k for k,v in m['supply_aliases'].items()}.get(n,n),s.get('mcu_gpio',''),s.get('mcu_pad',''),'clean' if ref=='J30' else 'field'])
print('P6 matched mechanical and pinout contract updated')

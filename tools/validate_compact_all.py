"""Export and verify the current P6 branch; no design mutations."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
CLI=Path('C:/Program Files/KiCad/9.0/bin/kicad-cli.exe')
OUT=ROOT/'outputs/compact';OUT.mkdir(parents=True,exist_ok=True)
for b,pr in [('controller','controller/Elevation_Controller'),('elevation','Elevation_Pivot_Daughter-Board')]:
    for args in [('sch','export','netlist','--format','kicadxml','-o',str(OUT/(b+'.xml')),pr+'.kicad_sch'),
                 ('sch','erc','--format','json','--severity-all','-o',str(OUT/(b+'_erc.json')),pr+'.kicad_sch'),
                 ('pcb','drc','--format','json','--severity-all','-o',str(OUT/(b+'_drc.json')),pr+'.kicad_pcb')]:
        subprocess.run([str(CLI),*args],cwd=ROOT,check=True,capture_output=True)
subprocess.run([sys.executable,str(ROOT/'tools/validate_compact.py')],cwd=ROOT,check=True)
subprocess.run([str(CLI.parent/'python.exe'),str(ROOT/'tools/validate_compact_pcb.py')],cwd=ROOT,check=True)

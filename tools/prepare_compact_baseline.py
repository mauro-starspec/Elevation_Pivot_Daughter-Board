"""Recover the immutable P5 source for P6 builders/audits from local Git."""
from pathlib import Path
import io,zipfile,subprocess,shutil
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'_work/p6_baseline'
def ensure_baseline():
    if not (BASE/'Elevation_Pivot_Daughter-Board.kicad_pcb').exists():
        raw=subprocess.run(['git','archive','--format=zip','29b4387'],cwd=ROOT,check=True,capture_output=True).stdout
        BASE.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for name in z.namelist():
                resolved=(BASE/name).resolve()
                assert resolved.is_relative_to(BASE.resolve()),name
            z.extractall(BASE)
    for name in ['inventory.json','controller.xml','elevation.xml']:
        if not (BASE/name).exists():shutil.copy2(ROOT/'docs/validation/p6_baseline'/name,BASE/name)
    return BASE
if __name__=='__main__':print(ensure_baseline())

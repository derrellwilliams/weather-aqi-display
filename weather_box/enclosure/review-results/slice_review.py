from pathlib import Path
import subprocess,json,re,hashlib
root=Path(__file__).resolve().parents[1]
tools=root/'.venv/review-tools'
exe=tools/'mounted/Original Prusa Drivers/PrusaSlicer.app/Contents/MacOS/PrusaSlicer'
results=[]
for name in ('01_front_shell','02_electronics_carrier','03_back','optional_fit_coupon'):
 out=tools/(name+'-analysis-only.gcode')
 command=[str(exe),'--datadir',str(tools/'config'),'--threads','4','--load',str(root/'review-results/slicer-settings.ini'),'--center','75,75','--export-gcode','--output',str(out),str(root/'print-files'/f'{name}.stl')]
 r=subprocess.run(command,capture_output=True,text=True)
 (root/'review-results'/f'{name}-slice.log').write_text(r.stdout+r.stderr)
 result={'source_revision':4,'stl_sha256':hashlib.sha256((root/'print-files'/f'{name}.stl').read_bytes()).hexdigest(),'part':name,'exit_code':r.returncode,'profile':'generic PLA 0.4 nozzle; 0.2 layers; NOT Holladay machine G-code'}
 if r.returncode==0:
  text=out.read_text();result['layers']=text.count(';LAYER_CHANGE');result['statistics']=[s for s in text.splitlines() if s.startswith(('; filament used','; estimated printing time','; total filament used'))]
  result['feature_types']=sorted(set(re.findall(r'^;TYPE:(.+)$',text,re.M)))
 results.append(result)
 print(name,'exit',r.returncode,flush=True)
(root/'review-results/slicer-checks.json').write_text(json.dumps(results,indent=2)+'\n')

assert all(r['exit_code']==0 for r in results), 'Slicing failed; do not package results'

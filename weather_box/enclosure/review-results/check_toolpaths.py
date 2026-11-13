from pathlib import Path
import re,json,math
root=Path(__file__).resolve().parents[1];out=[]
for path in sorted((root/'.venv/review-tools').glob('*-analysis-only.gcode')):
 x=y=e=0.;z=0.;layer=-1;counts=[];xy=[];heights=[]
 for line in path.read_text().splitlines():
  if line==';LAYER_CHANGE':layer+=1;counts.append(0)
  if line.startswith(';Z:'):heights.append(float(line[3:]))
  raw=line.split(';')[0].strip();words=raw.split()
  if not words:continue
  vals={k:float(v) for k,v in re.findall(r'([XYZE])(-?\d*\.?\d+)',raw)}
  if words[0]=='G92':e=vals.get('E',e);continue
  if words[0] not in ('G0','G1'):continue
  nx=vals.get('X',x);ny=vals.get('Y',y);ne=vals.get('E',e)
  if ne>e and math.hypot(nx-x,ny-y)>.0001 and layer>=0:
   counts[layer]+=1;xy.extend([(x,y),(nx,ny)])
  x,y,e=nx,ny,ne
 assert all(counts),(path,'empty layers')
 assert all(b>a for a,b in zip(heights,heights[1:])),path
 bounds=[min(p[0] for p in xy),min(p[1] for p in xy),max(p[0] for p in xy),max(p[1] for p in xy)]
 assert min(bounds[:2])>=0 and max(bounds[2:])<=150,path
 out.append({'file':path.name,'nonempty_layers':len(counts),'monotonic_layer_z':True,'min_extruding_moves_per_layer':min(counts),'extrusion_xy_bounds_mm':bounds,'within_150mm_bed':True,'last_layer_z_mm':heights[-1]})
(root/'review-results/toolpath-checks.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))

"""Independent, read-only checks of revision 4 exported STLs. Does not regenerate CAD."""
from pathlib import Path
import json,hashlib
import numpy as np
import trimesh
import manifold3d as m
root=Path(__file__).resolve().parents[1]
results={'source_revision':4,'nuts':[],'meshes':{},'notes':[]}
def load(name,offset=(0,0,0)):
 p=root/'print-files'/name;t=trimesh.load_mesh(p,process=True)
 results['meshes'][name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'watertight':bool(t.is_watertight),'winding_consistent':bool(t.is_winding_consistent),'dimensions_mm':t.extents.tolist(),'min_z_mm':float(t.bounds[0,2]),'connected_solids':len(t.split(only_watertight=False))}
 return m.Manifold(m.Mesh(np.asarray(t.vertices,dtype=np.float32),np.asarray(t.faces,dtype=np.uint32))).translate(offset)
s=load('01_front_shell.stl');c=load('02_electronics_carrier.stl',(3,3,6.8));b=load('03_back.stl',(0,0,33));coupon=load('optional_fit_coupon.stl')
for x in (6,120):
 for y in (6,76):
  nut=m.Manifold.cylinder(2.4,5.5/np.sqrt(3),circular_segments=6).translate((x,y,4))
  v=(s^nut).volume();assert v<.001,('obstructed nut seat',x,y,v)
  for dz in np.arange(0,30,.5):assert (s^nut.translate((0,0,float(dz)))).volume()<.001,('nut insertion',x,y,dz)
  results['nuts'].append({'center':[x,y],'standard_nut_interference_mm3':round(v,6),'fits_nominal_seated_position':v<.001})
  screw=m.Manifold.cylinder(30,1.5,circular_segments=64).translate((x,y,4.5))
  assert max((s^screw).volume(),(c^screw).volume(),(b^screw).volume())<.001
nut=m.Manifold.cylinder(2.4,5.5/np.sqrt(3),circular_segments=6).translate((6,6,4))
results['coupon_nut_interference_mm3']=round((coupon^nut).volume(),6)
# Rail-contact areas as the PCB moves toward its screen connector (-X),
# ignoring friction and the omitted flex cable to isolate the geometric stop.
def box(x,y,z,w,h,d):return m.Manifold.cube((w,h,d)).translate((x,y,z))
slides=[]
for dx in (0,.3,.5,1,2):
 pcb=box(12-dx,27,12.6,42.2,25.1,1.6)
 v=(pcb^c).volume()
 assert v<.001 if dx<=.3 else v>.01,('board insertion-direction stop',dx,v)
 slides.append({'board_shift_toward_ribbon_mm':dx,'carrier_collision_mm3':round((pcb^c).volume(),6)})
results['board_slide_check']=slides
for dx in (.3,.5,1):
 pcb=box(12+dx,27,12.6,42.2,25.1,1.6);v=(pcb^c).volume();assert v<.001 if dx<=.3 else v>.01,('board extraction-direction stop',dx,v)
# Provisional connector envelope: corner stops must leave the central opening clear.
assert (box(9.5,29.2,9,8.5,20.4,10)^c).volume()<.001
assert abs(results['coupon_nut_interference_mm3'])<.001
results['notes']=['Nut check includes the complete exported shell, not just the isolated boss subtraction.','PCB slide check omits friction and cable geometry; it checks positive restraint after the nominal 0.4 mm fit clearance, not an actual load rating.','No real connector geometry, cable bend model, strap tension, magnet holding force or printer-specific fit is inferred.']
(root/'review-results'/'independent-checks.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))

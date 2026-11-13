"""Parametric enclosure, mm. Run with .venv/bin/python make_case.py.
Source of truth for production meshes; no commercial CAD application needed.
"""
from pathlib import Path
import json, math, itertools, hashlib
import manifold3d as m
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'print-files'; OUT.mkdir(exist_ok=True)
W,H,D=126.,82.,36.
SCREWS=[(x,y) for x in (6.,120.) for y in (6.,76.)]
EPS=.01

def box(x,y,z,w,h,d):return m.Manifold.cube((w,h,d)).translate((x,y,z))
def cyl(x,y,z,r,h,n=64):return m.Manifold.cylinder(h,r,circular_segments=n).translate((x,y,z))
def union(xs):
    out=m.Manifold()
    for a in xs:out=out+a
    return out

def rr(x,y,z,w,h,d,r):
    return union([cyl(x+xx,y+yy,z,r,d) for xx in (r,w-r) for yy in (r,h-r)]).hull()

def shell():
    a=rr(0,0,0,W,H,33,4)-rr(2.4,2.4,2,W-4.8,H-4.8,32,2)
    a=a-box(16.3,12.3,-1,93.4,57.4,5)
    # Front ledge + alignment fence. Display sits on 0.4 mm foam tape.
    fence=rr(5.2,8.2,1.8,108.6,65.6,2.8,1.2)-box(6.4,9.4,1.7,106.2,63.2,4)
    fence=fence-box(4,23,1.7,5,36,4)
    a=a+fence
    for x,y in SCREWS:
        a=a+cyl(x,y,0,4.4,6.8)
    # Clear screen insertion pocket through the full height of corner bosses.
    a=a-box(6.4,9.4,2,106.2,63.2,5)
    # Cut cavities LAST so screen fences cannot refill the nut pockets.
    for x,y in SCREWS:
        a=a-cyl(x,y,4,3.35,3,6)-cyl(x,y,3.2,1.7,4)
    return a

def carrier():
    a=rr(3,3,6.8,120,76,2.2,3)
    # Full-depth open channel for the flex cable, leaving its loop untouched.
    a=a-box(0,23,6.7,16,36,3)
    # Open top edge lets the carrier lift past the wall-mounted antenna.
    a=a-box(62,0,6.7,44,5.5,3)
    # Corner sleeves transfer screw load directly to shell bosses, not electronics.
    for x,y in SCREWS:
        a=a+cyl(x,y,6.8,3,26.2)
        a=a-cyl(x,y,6.7,1.75,27)
    # Board edge supports: contacts outermost 0.8 mm only. Underside at 12.6.
    for y in (27,51.3):a=a+box(18,y,8.9,30,.8,3.7)
    for y in (25.6,52.5):a=a+box(18,y,8.9,30,1.0,5.1)
    for y in (28,48):a=a+box(54.6,y,8.9,1.2,3,5.1)
    # Positive -X stops at the PCB corners, 0.4 mm nominal clearance.
    # Bed-supported feet join the carrier across the edge of the ribbon notch.
    # Leave a 20.8 mm central opening between the two ears for connector/latch.
    for y in (26.8,49.8):
        a=a+box(10.4,y,6.8,7.7,2.2,2.2)
        a=a+box(10.4,y,8.9,1.2,2.2,5.3)
    # Board strap passes across shield at x=39..45; slot width accepts 6 mm tape.
    for y in (22.8,54.5):a=a-rr(38, y,6.7,8,2.6,3,.65)
    # Battery rotated to keep its 50.3 mm lead near the board connector.
    # Measured battery 49.8 x 32.3 x 9.9, at 62,39,9; 0.6 mm wall clearance.
    a=a+box(60.2,37.2,8.9,53.4,1.2,4.1)
    a=a+box(60.2,71.9,8.9,53.4,1.2,4.1)
    a=a+box(112.4,37.2,8.9,1.2,35.9,4.1)
    for y,h in ((37.2,11.8),(61,12.1)):a=a+box(60.2,y,8.9,1.2,h,4.1)
    # Battery strap axis y, 6 mm wide, generous threading slots.
    for y in (33.9,74.0):a=a-rr(83,y,6.7,8,2.6,3,.65)
    # Short lead can cross an unobstructed aisle between board and battery.
    return a

def back():
    a=rr(0,0,33,W,H,3,4)
    # Flat inside face: prints directly on bed without support. Screws align lid.
    for x,y in SCREWS:
        a=a-cyl(x,y,32.8,1.75,4)-cyl(x,y,34.5,3.25,2)
    for x in (19,107):
        for y in (17,65):a=a-cyl(x,y,35.4,9.25,1)
    return a

def coupon():
    # Cheap, separate fit check: M3 screw bore, nut well, magnet pocket, strap slot.
    a=rr(0,0,0,66,30,4,2)
    # Include the ACTUAL top-left shell corner, with adjacent screen fence.
    # The isolated revision-3 nut well could not expose fence interference.
    a=a-box(-1,-1,-.1,17,17,8)
    a=a+(shell()^box(0,0,0,16,16,6.8))
    a=a-cyl(30,15,3.4,9.25,1)
    a=a-rr(48,10,-.1,8,2.6,5,.65)
    a=a-cyl(58,22,-.1,1.75,5)-cyl(58,22,2.5,3.25,2)
    return a

def mesh(a):
    v=a.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(v.vert_properties)[:,:3],faces=np.asarray(v.tri_verts),process=True)

def printable(a,name):
    # All three parts print flat as exported, recesses/ledges upward.
    bounds=a.bounding_box();return a.translate((-bounds[0],-bounds[1],-bounds[2]))

solids={'01_front_shell':shell(),'02_electronics_carrier':carrier(),'03_back':back(),'optional_fit_coupon':coupon()}
# Exact box envelopes of the measured components; fittings have conservative placeholders.
components={
 'screen':box(6.8,9.8,2.4,105.4,62.4,1.2),
 'driver_board':box(12,27,12.6,42.2,25.1,1.6),
 'XIAO':box(33.3,30.65,25.2,20.9,17.8,1.6),
 'USB':box(48,35,26.8,7.7,9,2.8),
 'battery':box(62,39,9,49.8,32.3,9.9),
 'antenna':box(64,3.2,10,40,.5,20),
}
# Keepouts are not models of unknown component geometry.
keepouts={
 'board_pin_envelope':box(12,28,11.1,42.2,23.1,1.5),
 'USB_plug_access':box(55.7,32.5,24,35,14,8),
 'battery_lead_aisle':box(22,45,14.3,40,12,4),
}
report={'revision':'4 — corrected first-fit print','units':'mm','dimensions':[W,H,D],'parts':{},'intersections_mm3':{},'keepouts_mm3':{},'physical_fit_tested':False,'slicer_tested':False}
for name,a in solids.items():
    assert str(a.status())=='Error.NoError',(name,a.status())
    pm=mesh(printable(a,name));out=OUT/(name+'.stl');pm.export(out)
    # Reimport exported STL to check actual deliverable rather than in-memory geometry.
    check=trimesh.load_mesh(out,process=True)
    assert check.is_watertight and check.is_winding_consistent and check.volume>0,name
    assert len(check.split(only_watertight=False))==1,name
    assert max(check.extents)<150,name
    # 0.2 mm layer sweep: material above the previous layer must be supported.
    pa=printable(a,name);last=pa.slice(.1);maximum=0.;layers=0
    for z in np.arange(.3,check.extents[2],.2):
        current=pa.slice(float(z));maximum=max(maximum,(current-last.offset(.2)).area());last=current;layers+=1
    assert maximum<.01,(name,'unsupported layer area',maximum)
    report['parts'][name]={'bounds_mm':np.round(check.extents,3).tolist(),'triangles':len(check.faces),'watertight':bool(check.is_watertight),'consistent_winding':bool(check.is_winding_consistent),'connected_solids':1,'layer_height_mm':.2,'layers_checked':layers+1,'max_unsupported_area_mm2':round(maximum,6),'volume_mm3':round(check.volume,2),'solid_PLA_mass_g_at_1_24':round(check.volume/1000*1.24,2),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
for (n,a),(k,b) in itertools.combinations(list(solids.items())[:3],2):
    vol=(a^b).volume();report['intersections_mm3'][n+' / '+k]=round(vol,6);assert vol<.001,(n,k,vol)
for n,a in components.items():
    for k,b in list(solids.items())[:3]:
        vol=(a^b).volume();report['intersections_mm3'][n+' / '+k]=round(vol,6);assert vol<.001,(n,k,vol)
for n,a in keepouts.items():
    for k,b in list(solids.items())[:3]:
        vol=(a^b).volume();report['keepouts_mm3'][n+' / '+k]=round(vol,6);assert vol<.001,(n,k,vol)
# Verify the rigid parts can be lowered into place vertically, not just fit finally.
for dz in np.arange(0,36,1.):
    assert (solids['02_electronics_carrier'].translate((0,0,float(dz))) ^ solids['01_front_shell']).volume()<.001
    assert (solids['02_electronics_carrier'].translate((0,0,float(dz))) ^ components['antenna']).volume()<.001
    assert (components['screen'].translate((0,0,float(dz))) ^ solids['01_front_shell']).volume()<.001
report['vertical_insertion_sweep']={'step_mm':1,'travel_mm':35,'carrier_vs_shell':'pass','carrier_vs_antenna':'pass','screen_vs_shell':'pass'}
# Hardware regression: real nut envelope and continuous insertion keepout.
report['nut_fits']=[]
for x,y in SCREWS:
    nut=cyl(x,y,4,5.5/math.sqrt(3),2.4,6)
    sweep=cyl(x,y,4,5.5/math.sqrt(3),30,6)
    assert (nut^solids['01_front_shell']).volume()<.001
    assert (sweep^solids['01_front_shell']).volume()<.001
    report['nut_fits'].append({'center':[x,y],'seated_and_insertion_clear':True})
# Both longitudinal directions have 0.4 mm clearance then positive restraint.
for dx in (-.5,-.3,0,.3,.5):
    v=(components['driver_board'].translate((dx,0,0))^solids['02_electronics_carrier']).volume()
    assert (v<.001 if abs(dx)<=.3 else v>.01),('board stop',dx,v)
assert (box(9.5,29.2,9,8.5,20.4,10)^solids['02_electronics_carrier']).volume()<.001
report['board_stops']={'nominal_longitudinal_clearance_each_end_mm':.4,'restrained_both_directions':True,'connector_opening_is_assumed_not_measured':True}
# Shared screw stack: 30 mm screw seats at z34.5, enters nut z4..6.4.
report['screw_stack']={'under_head_z':34.5,'length':30,'tip_z':4.5,'nut_bottom_z':4,'nut_top_z':6.4,'thread_engagement_mm':1.9,'blind_bore_bottom_z':3.2}
(ROOT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
# Actual printable meshes in assembled coordinates for the preserved HTML review.
preview=[]
for name,a in list(solids.items())[:3]+list(components.items()):
    tm=mesh(a);preview.append({'name':name,'vertices':np.round(tm.vertices,4).tolist(),'faces':tm.faces.tolist()})
(ROOT/'assembly-meshes.json').write_text(json.dumps(preview,separators=(',',':')))
print(json.dumps(report['parts'],indent=2))

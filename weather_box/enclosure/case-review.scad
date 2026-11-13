// Revision 4 mesh-backed assembly viewer. Units mm.
// EDIT DIMENSIONS in make_case.py, then regenerate; revision 1 geometry is obsolete.
// Print only the exported individual STL files, not this electronics assembly.
part="assembly"; // shell, carrier, back, assembly
module shell(){import("print-files/01_front_shell.stl");}
module carrier(){translate([3,3,6.8])import("print-files/02_electronics_carrier.stl");}
module back(){translate([0,0,33])import("print-files/03_back.stl");}
if(part=="shell")shell();
if(part=="carrier")carrier();
if(part=="back")back();
if(part=="assembly"){
 color([.95,.95,.95,.3])shell();color([.78,.78,.78])carrier();
 color([.9,.9,.9,.2])back();
 color([.9,.9,.9])translate([6.8,9.8,2.4])cube([105.4,62.4,1.2]);
 color([.3,.3,.3])translate([12,27,12.6])cube([42.2,25.1,1.6]);
 color([.5,.5,.5])translate([33.3,30.65,25.2])cube([20.9,17.8,1.6]);
 color([.65,.65,.65])translate([62,39,9])cube([49.8,32.3,9.9]);
}

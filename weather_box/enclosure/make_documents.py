from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib import colors
root=Path(__file__).resolve().parent
c=canvas.Canvas(str(root/'screen-fit-template.pdf'),pagesize=letter)
c.setTitle('Fridge case revision 4 — actual-size screen fit template')
c.setFont('Helvetica-Bold',15);c.drawString(18*mm,263*mm,'Screen / case fit template — actual size')
c.setFont('Helvetica',10)
for i,t in enumerate(['Print at 100% / Actual size. Disable Fit to page.', 'Check the 100 mm bar with a ruler before comparing parts.', 'Black: case / aperture. Dashed: physical screen. Gray: reference active area.', 'Compare without bending the panel. Do not cut or press against the glass.']):c.drawString(18*mm,(253-i*6)*mm,t)
x0,y0=30*mm,130*mm
# Drawing coordinates: x right, y down when viewed from front.
def rect(x,y,w,h,stroke=1,fill=0):c.rect(x0+x*mm,y0+(82-y-h)*mm,w*mm,h*mm,stroke=stroke,fill=fill)
c.setStrokeColor(colors.black);c.setLineWidth(.6);c.roundRect(x0,y0,126*mm,82*mm,4*mm)
c.setFillColor(colors.HexColor('#eeeeee'));rect(16.6,13.16,92.8,55.68,0,1)
rect(16.3,12.3,93.4,57.4)
c.setDash(3,2);rect(6.8,9.8,105.4,62.4);c.setDash()
c.setFont('Helvetica',10)
for i,t in enumerate(['Case: 126 x 82 mm. Window: 93.4 x 57.4 mm.', 'Physical panel: 105.4 x 62.4 mm. Image reference: 92.8 x 55.68 mm.', 'Left/right visible borders: 16.3 mm each. Top/bottom: 12.3 mm each.', 'Image reference is centered in the opening; verify against your actual active pixels.', 'Do this check before attaching the screen with tape.']):c.drawString(18*mm,(117-i*6)*mm,t)
c.line(30*mm,65*mm,130*mm,65*mm)
for x in (30,130):c.line(x*mm,63*mm,x*mm,67*mm)
c.drawString(62*mm,59*mm,'100 mm reference')
c.showPage();c.save()

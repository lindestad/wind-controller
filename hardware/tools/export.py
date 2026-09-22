"""Export and audit the current routed KiCad files; never regenerates or reroutes them."""
from pathlib import Path
import os,shutil,sys,subprocess,csv,json,zipfile,xml.etree.ElementTree as ET,hashlib
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).parent/'vendor'))
import pcbnew as p,pymupdf as fitz
B=Path(__file__).resolve().parents[1]; CLI=Path(os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe')
M=B/'manufacturing';A=M/'assembly';R=B/'reports'
for d in [M/'gerbers',M/'paste',A]:d.mkdir(parents=True,exist_ok=True)
def run(*args):
 r=subprocess.run([str(CLI),*map(str,args)],cwd=B,capture_output=True,text=True)
 if r.returncode:raise RuntimeError(' '.join(map(str,args))+'\n'+r.stdout+r.stderr)
 return r.stdout
run('sch','erc','--exit-code-violations','-o','reports/erc-final.rpt','windpcb.kicad_sch')
run('pcb','drc','--schematic-parity','--all-track-errors','--exit-code-violations','-o','reports/drc-final.rpt','windpcb.kicad_pcb')
run('sch','export','netlist','--format','kicadxml','-o','reports/schematic.net','windpcb.kicad_sch')
b=p.LoadBoard(str(B/'windpcb.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()}
root=ET.parse(R/'schematic.net').getroot();expected={}
for net in root.findall('./nets/net'):
 for n in net.findall('node'):expected[(n.get('ref'),n.get('pin'))]=net.get('name')
actual={}; errors=[]
for ref,f in fps.items():
 for z in f.Pads():
  if z.GetNumber():actual[(ref,z.GetNumber())]=z.GetNetname()
for k,n in expected.items():
 if actual.get(k)!=n:errors.append([k,n,actual.get(k)])
for k,n in actual.items():
 if n and k not in expected:errors.append(['Extra',k,n])
report={'status':'PASS' if not errors else 'FAIL','schematic_connected_and_explicit_NC_pin_count':len(expected),'board_numbered_pad_keys':len(actual),'errors':errors,'mechanical_board_only':sorted(r for r in fps if r.startswith('H')),'notes':'Repeated module ground pads are one logical pin; all occurrences checked by KiCad parity/DRC.'}
(R/'connectivity.json').write_text(json.dumps(report,indent=2));assert not errors,errors
run('sch','export','pdf','-o','reports/schematic.pdf','windpcb.kicad_sch')
run('pcb','export','svg','--layers','F.Fab,F.SilkS,Edge.Cuts','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--sketch-pads-on-fab-layers','--crossout-DNP-footprints-on-fab-layers','--black-and-white','-o','reports/assembly-top.svg','windpcb.kicad_pcb')
# Convert CAD SVG to a cropped, vector PDF. Preserve zoomable geometry.
d=fitz.open(R/'assembly-top.svg');pdf=fitz.open('pdf',d.convert_to_pdf());pdf.save(R/'assembly-top.pdf');pdf[0].get_pixmap(matrix=fitz.Matrix(5,5)).save(R/'assembly-top.png')
for layer,name in [('F.Cu','copper-top'),('B.Cu','copper-bottom')]:
 run('pcb','export','svg','--layers',layer+',Edge.Cuts','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-o',f'reports/{name}.svg','windpcb.kicad_pcb')
run('pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts','--use-drill-file-origin','--subtract-soldermask','-o','manufacturing/gerbers/','windpcb.kicad_pcb')
run('pcb','export','drill','--drill-origin','plot','--excellon-separate-th','--generate-report','--report-path','reports/drills.rpt','-o','manufacturing/gerbers/','windpcb.kicad_pcb')
run('pcb','export','gerbers','--layers','F.Paste','--use-drill-file-origin','-o','manufacturing/paste/','windpcb.kicad_pcb')
run('pcb','export','pos','--format','csv','--units','mm','--use-drill-file-origin','--exclude-dnp','-o','manufacturing/assembly/KiCad-positions.csv','windpcb.kicad_pcb')
run('pcb','export','step','--board-only','--force','--drill-origin','-o','manufacturing/board-only.step','windpcb.kicad_pcb')
rows=list(csv.DictReader((B/'BOM.csv').open(encoding='utf-8-sig')));smt=[x for x in rows if x['Assembly']=='SMT'];assert len(smt)==63
with (A/'SMT-CPL.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation'])
 for a in smt:
  z=fps[a['Reference']];xy=z.GetPosition();w.writerow([a['Reference'],f'{p.ToMM(xy.x-b.GetDesignSettings().GetAuxOrigin().x):.4f}',f'{p.ToMM(b.GetDesignSettings().GetAuxOrigin().y-xy.y):.4f}','Top',f'{z.GetOrientationDegrees()%360:.3f}'])
groups=defaultdict(list)
for a in smt:groups[(a['MPN'],a['Value'],a['Footprint'],a['LCSC'])].append(a['Reference'])
with (A/'SMT-BOM.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['Comment','Designator','Footprint','Quantity','Manufacturer Part Number','LCSC Part #'])
 for (mpn,value,fp,lcsc),refs in groups.items():w.writerow([value,','.join(refs),fp,len(refs),mpn,lcsc])
with (A/'HAND-BOM.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(a for a in rows if a['Assembly']=='HAND')
pcba=[a for a in rows if a['Assembly'] in ['SMT','THT']]
assert len(pcba)==70 and all(a['LCSC'] for a in pcba)
with (A/'PCBA-CPL.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation'])
 for a in pcba:
  ref=a['Reference'];z=fps[ref];xy=z.GetPosition()
  x=p.ToMM(xy.x-b.GetDesignSettings().GetAuxOrigin().x);y=p.ToMM(b.GetDesignSettings().GetAuxOrigin().y-xy.y);rot=z.GetOrientationDegrees()%360
  # JLC's THT models use centred insertion origins, unlike KiCad's pin-1 origin.
  # B.2 origins verified in JLC preview. B.3 J1 uses its new pad-array midpoint; reconfirm the C381115 library overlay before ordering.
  if ref in ['C6','C9']:x+=1.25 if ref=='C6' else 2.5
  if ref in ['J3','J4','J5','J6']:x+=3.81
  if ref=='J1':x-=3.0;y-=2.35;rot=0
  w.writerow([ref,f'{x:.4f}',f'{y:.4f}','Top',f'{rot:.3f}'])
pgroups=defaultdict(list)
for a in pcba:pgroups[(a['MPN'],a['Footprint'],a['LCSC'])].append(a)
with (A/'PCBA-BOM.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['Comment','Designator','Footprint','Quantity','Manufacturer Part Number','LCSC Part #'])
 for (mpn,fp,lcsc),parts in pgroups.items():w.writerow([' / '.join(dict.fromkeys(a['Value'] for a in parts)),','.join(a['Reference'] for a in parts),fp,len(parts),mpn,lcsc])
with zipfile.ZipFile(M/'windpcb-revb-gerbers.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in (M/'gerbers').iterdir():z.write(f,f.name)
 z.write(M/'paste/windpcb-F_Paste.gtp','windpcb-F_Paste.gtp')
run('pcb','render','--width','1400','--height','1400','--quality','high','--use-board-stackup-colors','-o','reports/board-top.png','windpcb.kicad_pcb')
run('pcb','render','--width','1400','--height','1400','--side','bottom','--quality','high','--use-board-stackup-colors','-o','reports/board-bottom.png','windpcb.kicad_pcb')
manifest={str(f.relative_to(B)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [B/'windpcb.kicad_pro',B/'windpcb.kicad_sch',B/'windpcb.kicad_pcb',B/'BOM.csv',A/'SMT-BOM.csv',A/'SMT-CPL.csv',A/'PCBA-BOM.csv',A/'PCBA-CPL.csv',M/'windpcb-revb-gerbers.zip',M/'paste/windpcb-F_Paste.gtp',A/'HAND-BOM.csv']}
(M/'SHA256.json').write_text(json.dumps(manifest,indent=2))
print('PASS: ERC, full DRC + schematic parity, exact pad net audit. Exported Gerbers, drill, 70-place full PCBA BOM/CPL, PDFs, STEP and preview.')

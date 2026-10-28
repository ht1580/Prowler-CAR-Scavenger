"""Model-local RUI mounts and binary table/length normalization."""
import json,sys,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CFG=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'));BUILD=ROOT/'build';TASK=ROOT.parents[1]
sys.path.insert(0,CFG['tools_root']);import rui_editor
model=BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl';rig=json.loads((BUILD/'rig.json').read_text());doc=rui_editor.inspect_mdl(model);data=bytearray(doc['bytes']);report=[]
for mesh in doc['meshes']:
 name=mesh['name'];parent=mesh['parentNames'][0];M=rig['rest_global'][parent];origin=[M[i][3] for i in range(3)];verts=mesh['vertices'];points=[v['position'] for v in verts]
 if name.endswith('car_smg_rui_lower') or name.endswith('car_smg_rui_upper'):
  center=[sum(p[i] for p in points)/len(points) for i in range(3)]
  for v in verts:
   p=v['position'];d=[(p[i]-center[i])*1.25 for i in range(3)]
   q=[.835-d[2],48.75+d[1],2.98+d[0]] if name.endswith('lower') else [0.,46.5,5.]
   struct.pack_into('<3f',data,v['offset']+4,*(q[i]-origin[i] for i in range(3)))
  report.append(name)
 elif name.endswith('pro_screen_rui_upper'):
  for v in verts:struct.pack_into('<3f',data,v['offset']+4,*(x*.65 for x in v['position']))
model.write_bytes(data)
tool=ROOT/'src/tools'
for name in ('ptpov_car101','w_car101'):
 target=BUILD/'compiler_game/models/weapons/car101'/(name+'_conv.mdl');stock=Path(CFG['stock_root'])/'models/weapons/car101'/(name+'.mdl')
 subprocess.run([sys.executable,str(tool/'seq_fix.py'),str(stock),str(target)],check=True)
 subprocess.run([sys.executable,str(tool/'mdl_integrity.py'),str(target),'--fix-length'],check=True)
(BUILD/'rui-mounts.json').write_text(json.dumps(report));print('MODEL_FINISH_OK',report)

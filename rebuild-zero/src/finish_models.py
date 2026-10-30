"""Model-local RUI mounts and binary table/length normalization."""
import json,sys,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CFG=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'));BUILD=ROOT/'build';TASK=ROOT.parents[1]
sys.path.insert(0,CFG['tools_root']);import rui_editor
sys.path.insert(0,str(ROOT/'src/tools'))
from fix_delta_defaults import fix as fix_delta_defaults
from canonicalize_offsets import fix as canonicalize_offsets
delta_report=fix_delta_defaults(BUILD/'compiler_game/models/weapons/car101/ptpov_car101.mdl',BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl')
(BUILD/'delta-defaults.json').write_text(json.dumps(delta_report,indent=2),encoding='utf-8')
print('DELTA_DEFAULTS_FIXED',delta_report['corrected_fields'],flush=True)
offset_report=canonicalize_offsets(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl',BUILD/'rig.json')
(BUILD/'offset-zeros.json').write_text(json.dumps(offset_report,indent=2),encoding='utf-8')
print('EXACT_OFFSET_ZEROS',offset_report['canonical_zero_translations'],flush=True)
model=BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl';rig=json.loads((BUILD/'rig.json').read_text());doc=rui_editor.inspect_mdl(model);data=bytearray(doc['bytes']);report=[]
stock_ui=rui_editor.inspect_mdl(Path(CFG['stock_root'])/'models/weapons/car101/ptpov_car101.mdl')
templates={m['name']:m['vertices'] for m in stock_ui['meshes']}
native_panel=json.loads((ROOT/'src/assets/prowler_ammo_panel.json').read_text(encoding='utf-8'))
for mesh in doc['meshes']:
 name=mesh['name'];parent=mesh['parentNames'][0];M=rig['rest_global'][parent];origin=[M[i][3] for i in range(3)];verts=mesh['vertices'];source=templates[name]
 assert len(verts)==len(source),(name,'original RUI layout differs')
 points=[v['position'] for v in source]
 if name.endswith('car_smg_rui_lower'):
  assert len(verts)==len(native_panel['positions'])==4
  # The original Prowler central ammo screen is local to the gun base, not
  # the independently moved CAR optic. Keep the existing TF2 numeric canvas,
  # face UV data and event binding; replace its physical rectangle only.
  struct.pack_into('<h',data,mesh['parentOffsets'][0],doc['bones'].index(native_panel['parent']))
  for vertex,position in zip(verts,native_panel['positions']):
   struct.pack_into('<3f',data,vertex['offset']+4,*position)
  report.append(name)
 elif name.endswith('car_smg_rui_upper'):
  center=[sum(p[i] for p in points)/len(points) for i in range(3)]
  for v,original in zip(verts,source):
   p=original['position'];d=[(p[i]-center[i])*1.25 for i in range(3)]
   q=[0.,46.5,5.]
   struct.pack_into('<3f',data,v['offset']+4,*(q[i]-origin[i] for i in range(3)))
  report.append(name)
 elif name.endswith('pro_screen_rui_upper'):
  for v,original in zip(verts,source):struct.pack_into('<3f',data,v['offset']+4,*(x*rig['proscreen_scale'] for x in original['position']))
model.write_bytes(data)
tool=ROOT/'src/tools'
for name in ('ptpov_car101','w_car101'):
 target=BUILD/'compiler_game/models/weapons/car101'/(name+'_conv.mdl');stock=Path(CFG['stock_root'])/'models/weapons/car101'/(name+'.mdl')
 subprocess.run([sys.executable,str(tool/'seq_fix.py'),str(stock),str(target)],check=True)
 if name=='ptpov_car101':
  from motion_contract import EXTRA_ANIMS
  from mdl_lib import Mdl
  original=Mdl(stock);compiled=Mdl(target);normalized=bytearray(target.read_bytes())
  for (sr,sn),(br,bn) in zip(original.table(192,232,4),compiled.table(192,232,4)):
   assert sn==bn
   if sn=='idle_seq_autoplay':
    assert compiled.i(br+68,2)==(2,2)
    assert compiled.anims()==original.anims()+list(EXTRA_ANIMS)
    struct.pack_into('<2h',normalized,br+compiled.i(br+60)+4,len(original.anims()),len(original.anims())+1)
  target.write_bytes(normalized)
 subprocess.run([sys.executable,str(tool/'mdl_integrity.py'),str(target),'--fix-length'],check=True)
subprocess.run([sys.executable,str(ROOT/'src/export_rui.py')],check=True)
(BUILD/'rui-mounts.json').write_text(json.dumps(report));print('MODEL_FINISH_OK',report)

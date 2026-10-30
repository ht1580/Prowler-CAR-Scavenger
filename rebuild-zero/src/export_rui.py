"""Export the edited standalone .rui accepted by MDLShit's converter.

Offsets in the mesh table and records are relative; no absolute MDL pointer
is copied. The rest of the model, including animation payload, is excluded.
Edit assets/prowler_ammo_panel.json then run finish_models.py to regenerate.
"""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'))
sys.path.insert(0,CFG['tools_root'])
import rui_editor

def export(model,output):
 doc=rui_editor.inspect_mdl(model)
 count,start=struct.unpack_from('<2i',doc['bytes'],296)
 assert count==len(doc['meshes'])==6
 end=max(max(f['offset']+32 for f in mesh['faces']) for mesh in doc['meshes'])
 data=doc['bytes'][start:end]
 # Verify each relative table entry and all record payload remain byte-exact.
 for mesh in doc['meshes']:
  offset=mesh['headerOffset']-start
  relative=struct.unpack_from('<I',data,offset+4)[0]
  assert offset+relative==mesh['recordOffset']-start
  for vertex in mesh['vertices']:
   assert data[vertex['offset']-start:vertex['offset']-start+16]==doc['bytes'][vertex['offset']:vertex['offset']+16]
 Path(output).write_bytes(data)
 return dict(file=str(output),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),model_sha256=doc['sha256'],
             meshes=[dict(name=m['name'],parents=m['parentNames'],vertices=len(m['vertices']),faces=len(m['faces'])) for m in doc['meshes']],
             edit_source='src/assets/prowler_ammo_panel.json',uv='Unmodified original TF2 per-face data')

if __name__=='__main__':
 report=export(ROOT/'build/compiler_game/models/weapons/car101/ptpov_car101_conv.mdl',ROOT/'build/prowler_car101.rui')
 (ROOT/'build/rui-layout-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print('EDITED_RUI_EXPORTED',report['bytes'],report['sha256'])

"""Regression against actual native Prowler display corners, not hand-picked mounts."""
import json,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'))
sys.path.insert(0,CFG['tools_root'])
import rui_editor

class NativeAmmoPanel(unittest.TestCase):
 def test_final_numeric_canvas_uses_native_parent_and_surface(self):
  source=json.loads((ROOT/'src/assets/prowler_ammo_panel.json').read_text())
  doc=rui_editor.inspect_mdl(ROOT/'build/compiler_game/models/weapons/car101/ptpov_car101_conv.mdl')
  mesh=next(m for m in doc['meshes'] if m['name'].endswith('car_smg_rui_lower'))
  self.assertEqual(mesh['parentNames'],[source['parent']],'ammo display follows the shifted optic instead of the original gun base')
  self.assertEqual(len(mesh['vertices']),4)
  for actual,expected in zip(mesh['vertices'],source['positions']):
   self.assertLess(max(abs(a-b) for a,b in zip(actual['position'],expected)),1e-6,'numeric canvas does not lie on the original Apex display')

 def test_existing_car_uv_and_external_kill_screen_are_retained(self):
  old=rui_editor.inspect_mdl(Path(CFG['stock_root'])/'models/weapons/car101/ptpov_car101.mdl')
  new=rui_editor.inspect_mdl(ROOT/'build/compiler_game/models/weapons/car101/ptpov_car101_conv.mdl')
  self.assertEqual([m['name'] for m in old['meshes']],[m['name'] for m in new['meshes']])
  for a,b in zip(old['meshes'],new['meshes']):
   self.assertEqual(a['flags'],b['flags'])
   self.assertEqual(a['unknown'],b['unknown'])
   for fa,fb in zip(a['faces'],b['faces']):
    self.assertEqual(old['bytes'][fa['offset']:fa['offset']+32],new['bytes'][fb['offset']:fb['offset']+32])
    self.assertEqual(fa['vertices'],fb['vertices'])
   if 'pro_screen' in a['name']:
    self.assertEqual(a['parentNames'],b['parentNames'])
    for va,vb in zip(a['vertices'],b['vertices']):
     self.assertLess(max(abs(x*.65-y) for x,y in zip(va['position'],vb['position'])),1e-6)

if __name__=='__main__':unittest.main()

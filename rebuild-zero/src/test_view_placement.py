"""Engine-space gates: relative hand/gun comparisons cannot detect whole-rig displacement."""
import unittest,sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *

class EnginePlacement(unittest.TestCase):
 def test_proscreen_housing_fits_conservative_fixed_eye_projection(self):
  sys.path.insert(0,str(ROOT/'src/tools'))
  from mdl_mesh import read_mdl_mesh
  doc=json.loads((BUILD/'native-all.json').read_text(encoding='utf-8-sig'))
  order=[b['name'] for b in doc['bones']];parent={b['name']:order[b['parent']] if b['parent']>=0 else None for b in doc['bones']}
  bind=globals_(order,parent,{b['name']:matrix(b['pos'],Euler(b['rot'],'XYZ').to_quaternion()) for b in doc['bones']})
  pose=max((p for p in doc['poses'] if p['name']=='@draw_seq'),key=lambda p:p['frame'])
  G=globals_(order,parent,{order[v['index']]:matrix(v['pos'],Euler(v['rot'],'XYZ').to_quaternion()) for v in pose['locals']})
  md=read_mdl_mesh(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl',include={(4,1)})
  ids={i for part in md['parts'] for f in part['faces'] for i in f}
  camera=Euler((math.pi/2,0,math.pi/2),'XYZ').to_matrix().to_4x4()@Matrix.Rotation(math.pi,4,'Y')
  transform=camera.inverted()@G['def_c_proscreen']@bind['def_c_proscreen'].inverted()
  # A conservative 70-degree horizontal projection is a geometry gate, not a
  # claim about the user's actual engine viewmodel FOV. Runtime is checked too.
  focal=640/math.tan(math.radians(70)/2);visible=0
  for i in ids:
   p=transform@Vector(md['vertices'][i]);depth=-p.z
   if depth>.05 and 10<640+p.x/depth*focal<1270 and 10<360-p.y/depth*focal<700:visible+=1
  self.assertGreaterEqual(visible/len(ids),.95,'screen is cut off below the ordinary held view')

 def test_proscreen_backplate_is_supported_by_receiver_surface(self):
  sys.path.insert(0,str(ROOT/'src/tools'))
  from mdl_mesh import read_mdl_mesh
  from mathutils.bvhtree import BVHTree
  path=BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl'
  md=read_mdl_mesh(path,include={(4,1)})
  used={i for part in md['parts'] for f in part['faces'] for i in f}
  points=[Vector(md['vertices'][i]) for i in used]
  # The rigid housing back is its minimum-X plane. Check attachment to actual
  # receiver geometry, independently of camera FOV and the chosen bone origin.
  back=min(p.x for p in points);rear=[p for p in points if p.x<back+.02]
  body=read_mdl_mesh(path,include={(0,0)})
  tree=BVHTree.FromPolygons(body['vertices'],[f for part in body['parts'] for f in part['faces']],all_triangles=True)
  supported=0
  for p in rear:
   hit=tree.ray_cast(p,Vector((-1,0,0)),.22)
   if hit[0] is not None:supported+=1
  self.assertGreaterEqual(supported/len(rear),.75,'external kill-screen backplate is unsupported or mounted into the rear frame')

 def test_proscreen_housing_and_rui_use_the_same_bone(self):
  sys.path.insert(0,str(ROOT/'src/tools'))
  from mdl_mesh import read_mdl_mesh
  md=read_mdl_mesh(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl',include={(4,1)})
  ids={i for part in md['parts'] for f in part['faces'] for i in f}
  rig=json.loads((BUILD/'rig.json').read_text());ps=rig['order'].index('def_c_proscreen')
  self.assertEqual(rig['parent']['def_c_proscreen'],'weapon_bone')
  for i in ids:
   self.assertTrue(all(b==ps for b,w in md['weights'][i] if w>0),'screen housing is skinned to a different bone than its RUI')

 def test_proscreen_rui_follows_the_same_scaled_mount_as_housing(self):
  sys.path.insert(0,CFG['tools_root']);import rui_editor
  a=rui_editor.inspect_mdl(STOCK/'models/weapons/car101/ptpov_car101.mdl')
  b=rui_editor.inspect_mdl(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl')
  am=next(m for m in a['meshes'] if 'pro_screen' in m['name']);bm=next(m for m in b['meshes'] if 'pro_screen' in m['name'])
  self.assertEqual(am['parentNames'],bm['parentNames'])
  self.assertEqual([v['vertices'] for v in am['faces']],[v['vertices'] for v in bm['faces']])
  for av,bv in zip(am['vertices'],bm['vertices']):
   self.assertLess((Vector(av['position'])*.65-Vector(bv['position'])).length,.0001)

 def test_proscreen_has_no_independent_drift_from_weapon_bone(self):
  rig=json.loads((BUILD/'rig.json').read_text());expected=Matrix(rig['rest_local']['def_c_proscreen'])
  doc=json.loads((BUILD/'native-all.json').read_text(encoding='utf-8-sig'));i=rig['order'].index('def_c_proscreen')
  for p in doc['poses']:
   v=next(v for v in p['locals'] if v['index']==i);actual=matrix(v['pos'],Euler(v['rot'],'XYZ').to_quaternion())
   baseline=Matrix.Identity(4) if rig['animations'][p['name']]['delta'] else expected
   with self.subTest(animation=p['name'],frame=p['frame']):
    self.assertLess((actual.translation-baseline.translation).length,.01)
    self.assertLess(math.degrees(actual.to_quaternion().rotation_difference(baseline.to_quaternion()).angle),.05)

 def test_all_stock_delta_roots_are_preserved(self):
  stock=json.loads((BUILD/'native-stock-all.json').read_text(encoding='utf-8-sig'))
  built=json.loads((BUILD/'native-all.json').read_text(encoding='utf-8-sig'))
  rig=json.loads((BUILD/'rig.json').read_text())
  original={(p['name'],p['frame']):p for p in stock['poses']}
  for p in built['poses']:
   if not rig['animations'][p['name']]['delta'] or p['name'].startswith('attack_') or p['name'].endswith('_autoplay'):continue
   q=original.get((p['name'],p['frame']))
   if q is None:continue
   a=next(v for v in p['locals'] if v['index']==0);b=next(v for v in q['locals'] if v['index']==0)
   with self.subTest(animation=p['name'],frame=p['frame']):
    self.assertLess((Vector(a['pos'])-Vector(b['pos'])).length,.01)
    self.assertLess(math.degrees(Euler(a['rot'],'XYZ').to_quaternion().rotation_difference(Euler(b['rot'],'XYZ').to_quaternion()).angle),.05,'native idle correction must not rotate walk/run overlays')

 def test_autoplay_does_not_change_view_root_or_camera(self):
  doc=json.loads((BUILD/'native-idle.json').read_text(encoding='utf-8-sig'))
  for p in doc['poses']:
   for v in p['locals']:
    name=doc['bones'][v['index']]['name']
    if name not in ('jx_c_delta','jx_c_pov','jx_c_camera'):continue
    with self.subTest(animation=p['name'],frame=p['frame'],bone=name):
     self.assertLess(Vector(v['pos']).length,.01)
     self.assertLess(math.degrees(Euler(v['rot'],'XYZ').to_quaternion().angle),.05,'idle overlay must not turn the whole model behind the fixed game camera')

if __name__=='__main__':
 result=unittest.main(argv=['test_view_placement'],exit=False,failfast=True)
 if not result.result.wasSuccessful():raise RuntimeError('ENGINE_PLACEMENT_REGRESSION')

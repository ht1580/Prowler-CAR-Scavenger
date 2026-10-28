"""Engine-space gates: relative hand/gun comparisons cannot detect whole-rig displacement."""
import unittest,sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *

class EnginePlacement(unittest.TestCase):
 def test_proscreen_is_seated_on_receiver_instead_of_rear_pipe(self):
  sys.path.insert(0,str(ROOT/'src/tools'))
  from mdl_mesh import read_mdl_mesh
  md=read_mdl_mesh(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl',include={(4,1)})
  ids={i for part in md['parts'] for f in part['faces'] for i in f}
  points=[Vector(md['vertices'][i]) for i in ids];center=sum(points,Vector())/len(points)
  self.assertGreater(center.z,2.,'ProScreen is behind the receiver on the rear pipe, outside the ordinary view')
  self.assertLess(center.z,7.)
  self.assertAlmostEqual(min(v.x for v in points),.782,delta=.025,msg='case backing must seat against the original receiver side surface x=0.772 with small clearance')

 def test_proscreen_rui_follows_the_same_scaled_mount_as_housing(self):
  sys.path.insert(0,CFG['tools_root']);import rui_editor
  a=rui_editor.inspect_mdl(STOCK/'models/weapons/car101/ptpov_car101.mdl')
  b=rui_editor.inspect_mdl(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl')
  am=next(m for m in a['meshes'] if 'pro_screen' in m['name']);bm=next(m for m in b['meshes'] if 'pro_screen' in m['name'])
  self.assertEqual(am['parentNames'],bm['parentNames'])
  self.assertEqual([v['vertices'] for v in am['faces']],[v['vertices'] for v in bm['faces']])
  for av,bv in zip(am['vertices'],bm['vertices']):
   self.assertLess((Vector(av['position'])*.65-Vector(bv['position'])).length,.0001)

 def test_compiled_reference_matches_compiled_bind_for_subtract(self):
  doc=json.loads((BUILD/'native-view.json').read_text(encoding='utf-8-sig'))
  p=next(p for p in doc['poses'] if p['name']=='@ref')
  for v in p['locals']:
   b=doc['bones'][v['index']]
   with self.subTest(bone=b['name']):
    self.assertLess((Vector(v['pos'])-Vector(b['pos'])).length,.01)
    a=Euler(v['rot'],'XYZ').to_quaternion();r=Euler(b['rot'],'XYZ').to_quaternion()
    self.assertLess(math.degrees(a.rotation_difference(r).angle),.05,'subtract reference must equal runtime bind; otherwise every overlay inherits a constant offset')

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

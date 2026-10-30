"""Reject native variants which place the held gun behind the fixed original engine eye."""
import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *

class SprintVisibility(unittest.TestCase):
 def test_regular_sprint_has_visible_body_geometry_not_only_a_forward_origin(self):
  sys.path.insert(0,str(ROOT/'src/tools'));from mdl_mesh import read_mdl_mesh
  doc=json.loads((BUILD/'native-all.json').read_text(encoding='utf-8-sig'))
  order=[b['name'] for b in doc['bones']]
  parent={b['name']:order[b['parent']] if b['parent']>=0 else None for b in doc['bones']}
  bind=globals_(order,parent,{b['name']:matrix(b['pos'],Euler(b['rot'],'XYZ').to_quaternion()) for b in doc['bones']})
  mesh=read_mdl_mesh(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl',include={(0,0)})
  ids={i for part in mesh['parts'] for face in part['faces'] for i in face}
  camera=Euler((math.pi/2,0,math.pi/2),'XYZ').to_matrix().to_4x4()@Matrix.Rotation(math.pi,4,'Y')
  focal=640/math.tan(math.radians(70)/2)
  for pose in doc['poses']:
   if pose['name']!='@sprint_seq':continue
   local={order[v['index']]:matrix(v['pos'],Euler(v['rot'],'XYZ').to_quaternion()) for v in pose['locals']}
   gun=globals_(order,parent,local)['def_c_base'];transform=camera.inverted()@gun@bind['def_c_base'].inverted();visible=0
   for i in ids:
    point=transform@Vector(mesh['vertices'][i]);depth=-point.z
    visible+=depth>.05 and 0<640+point.x/depth*focal<1280 and 0<360-point.y/depth*focal<720
   self.assertGreater(visible/len(ids),.25,f'sprint frame{pose["frame"]}: gun body below/outside viewport')

 def test_regular_sprint_keeps_weapon_in_front_of_fixed_engine_eye(self):
  doc=json.loads((BUILD/'native-all.json').read_text(encoding='utf-8-sig'))
  order=[b['name'] for b in doc['bones']]
  parent={b['name']:order[b['parent']] if b['parent']>=0 else None for b in doc['bones']}
  poses=[p for p in doc['poses'] if p['name']=='@sprint_seq']
  self.assertGreaterEqual(len(poses),3)
  # Stock v53 view eye is at the origin, looking along +X (Rx90,Rz90).
  for p in poses:
   local={order[v['index']]:matrix(v['pos'],Euler(v['rot'],'XYZ').to_quaternion()) for v in p['locals']}
   gun=globals_(order,parent,local)['def_c_base'].translation
   with self.subTest(frame=p['frame']):
    self.assertGreater(gun.x,1.0,f'sprint gun origin behind original eye: {list(gun)}')

if __name__=='__main__':
 result=unittest.main(argv=['test_sprint_visibility'],exit=False)
 if not result.result.wasSuccessful():raise RuntimeError('SPRINT_VISIBILITY_FAILED')

"""The third-person accessory must use the same receiver seat as the viewmodel."""
import unittest,sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *

class WorldScreen(unittest.TestCase):
 def test_world_iron_bodygroup_uses_native_prowler_rear_sight(self):
  sys.path.insert(0,str(ROOT/'src/tools'))
  from mdl_mesh import read_mdl_mesh
  from mathutils.kdtree import KDTree
  modelpath=Path(CFG['texture_source']).parents[1]/'01_模型_Models/prowler_react_v21_scavenger_w_LOD0.cast'
  native=first(modelpath,cast.Model);bones=native.Skeleton().Bones();names=[b.Name() for b in bones]
  parent={b.Name():names[b.ParentIndex()] if b.ParentIndex()>=0 else None for b in bones}
  G=globals_(names,parent,{b.Name():matrix(b.LocalPosition(),quat(b.LocalRotation())) for b in bones})
  mesh=next(m for m in native.Meshes() if m.Name().startswith('sight_rear_1'))
  vb=mesh.VertexPositionBuffer();points=[G['def_c_base'].inverted()@Vector(vb[i:i+3]) for i in range(0,len(vb),3)]
  tree=KDTree(len(points))
  for i,p in enumerate(points):tree.insert(p,i)
  tree.balance()
  rig=json.loads((BUILD/'world-rig.json').read_text());W={n:Matrix(v) for n,v in rig['rest_global'].items()}
  tr=Matrix(rig['grip_transform']).inverted()@W['def_c_base'].inverted()
  mdl=read_mdl_mesh(BUILD/'compiler_game/models/weapons/car101/w_car101_conv.mdl',include={(5,1)})
  ids={i for p in mdl['parts'] for f in p['faces'] for i in f};self.assertTrue(ids)
  error=max(tree.find(tr@Vector(mdl['vertices'][i]))[2] for i in ids)
  self.assertLess(error,.02,'world iron bodygroup still contains the unrelated floating CAR sight')

 def test_world_accessories_use_viewmodel_receiver_seats(self):
  def globals_from(file):
   d=json.loads((BUILD/file).read_text(encoding='utf-8-sig'));o=[b['name'] for b in d['bones']]
   p={b['name']:o[b['parent']] if b['parent']>=0 else None for b in d['bones']}
   G=globals_(o,p,{b['name']:matrix(b['pos'],Euler(b['rot'],'XYZ').to_quaternion()) for b in d['bones']})
   return G
  V=globals_from('native-all.json');W=globals_from('native-world.json')
  # The world body is placed into the original CAR right-hand grip in mesh
  # space; its base bone and sequence interface remain stock.
  fit=Matrix(json.loads((BUILD/'world-rig.json').read_text())['grip_transform'])
  for name in ('def_c_proscreen','def_c_holo','def_c_acgs','def_c_cro'):
   view=V['def_c_base'].inverted()@V[name]
   world=fit.inverted()@W['def_c_base'].inverted()@W[name]
   with self.subTest(accessory=name):
    self.assertLess((view.translation-world.translation).length,.01,'world accessory floats at the old CAR mount')
    self.assertLess(math.degrees(view.to_quaternion().rotation_difference(world.to_quaternion()).angle),.05)

if __name__=='__main__':
 r=unittest.main(argv=['test_world_screen'],exit=False)
 if not r.result.wasSuccessful():raise RuntimeError('WORLD_SCREEN_FAILED')

"""Verify native eye-space trajectory, including its authored offscreen phases."""
import sys,json,math,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
class SprintVisibility(unittest.TestCase):
 def test_compiled_cycle_does_not_push_the_gun_away_from_the_original_path(self):
  doc=json.loads((BUILD/'native-dynamic.json').read_text(encoding='utf-8-sig'));o=[b['name'] for b in doc['bones']];p={b['name']:o[b['parent']] if b['parent']>=0 else None for b in doc['bones']}
  c=Clip(SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_base_v_animRig/sprint_0.cast');checks=0
  for pose in doc['poses']:
   if pose['name']!='@sprint_seq':continue
   G=globals_(o,p,{o[v['index']]:matrix(v['pos'],Euler(v['rot'],'XYZ').to_quaternion()) for v in pose['locals']});N=globals_(c.order,c.parent,c.sample_pose(c.end*pose['frame']/max(1,pose['frames']-1)))
   for n in ('def_c_base','def_r_wrist','def_l_wrist'):
    expected=Matrix.Rotation(math.pi/2,4,'Z')@N[n]
    self.assertLess((G[n].translation-expected.translation).length,.05)
    self.assertLess(math.degrees(G[n].to_quaternion().rotation_difference(expected.to_quaternion()).angle),.1);checks+=1
  self.assertEqual(checks,63)
 def test_all_skin_families_keep_the_same_scavenger_surface(self):
  sys.path.insert(0,str(ROOT/'src/tools'));from mdl_lib import Mdl
  for name in ('ptpov_car101','w_car101'):
   m=Mdl(BUILD/'compiler_game/models/weapons/car101'/(name+'_conv.mdl'));families=m.skins()
   self.assertGreater(len(families),1)
   self.assertIn('prowler_zero',families[0][0])
   self.assertTrue(all(f==families[0] for f in families),'a game skin redirects to another material')
if __name__=='__main__':
 r=unittest.main(argv=['native_visibility'],exit=False)
 if not r.result.wasSuccessful():raise RuntimeError('SPRINT_VISIBILITY_FAILED')

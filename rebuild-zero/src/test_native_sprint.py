"""The user requests the original Apex cycle, not the damped first-pose carry."""
import sys,json,math,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
class NativeSprint(unittest.TestCase):
 def test_compiled_loop_uses_the_original_apex_frame_rate(self):
  import struct
  sys.path.insert(0,str(ROOT/'src/tools'));from mdl_lib import Mdl
  m=Mdl(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl');row=next(r for r,n in m.table(184,92,4) if n=='@sprint_seq')
  c=Clip(SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_base_v_animRig/sprint_0.cast')
  self.assertAlmostEqual(struct.unpack_from('<f',m.d,row+8)[0],c.fps,places=4,msg='native cycle is still played at the CAR cadence')
 def test_complete_native_gun_and_hand_trajectory_is_preserved(self):
  o,p,frames,_=smd(BUILD/'view/anims/sprint_seq.smd');c=Clip(SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_base_v_animRig/sprint_0.cast')
  maximum=0.;checks=0
  for i,L in enumerate(frames):
   G=globals_(o,p,L);N=globals_(c.order,c.parent,c.sample_pose(c.end*i/max(1,len(frames)-1)))
   for n in ('def_c_base','def_r_wrist','def_r_elbow','def_r_forearm','def_l_wrist'):
    error=(G[n].translation-N[n].translation).length;maximum=max(maximum,error);checks+=1
    self.assertLess(error,.002,f'{i}/{n}: native position was damped or grip frozen')
    self.assertLess(math.degrees(G[n].to_quaternion().rotation_difference(N[n].to_quaternion()).angle),.02,f'{i}/{n}: native rotation changed')
  (BUILD/'native-sprint-validation.json').write_text(json.dumps(dict(source='original Apex sprint_0.cast',frames=len(frames),fps=c.fps,position_rotation_attenuation=False,frozen_hand_grip=False,source_contact_samples=checks,max_native_position_error=maximum,visibility_policy='Preserve original offscreen phases; do not force constant viewport occupancy.'),indent=2))
 def test_client_cosmetic_guard_covers_view_and_world_weapon(self):
  code=(ROOT/'src/client/prowler_stance.nut').read_text(encoding='utf-8')
  for target in ('weapon','viewmodel'):
   for method in ('SetCamo( 0 )','SetSkin( 0 )'):
    self.assertIn(target+'.'+method,code,'in-game cosmetic overrides still reach the replacement')
if __name__=='__main__':
 r=unittest.main(argv=['native_sprint'],exit=False)
 if not r.result.wasSuccessful():raise RuntimeError('NATIVE_SPRINT_FAILED')

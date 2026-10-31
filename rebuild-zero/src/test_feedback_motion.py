"""Prevent visible grip drift and sideways firing roll under active movement layers."""
import sys,math,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *

MOVEMENT=('run_anim_static','run_anim','run_anim_layer','walk_anim_static','walk_anim','walk_ads_anim','walk_anim_nocam','switch_to_jump_anim','switch_to_land_anim','switch_to_jump_crouch_anim','switch_to_land_crouch_anim','switch_to_jump_ads_anim','switch_to_land_ads_anim','idle_check_anim','idle_check_ads_anim')
def angle(q):return math.degrees(2*math.atan2(Vector((q.x,q.y,q.z)).length,abs(q.w)))
class FeedbackMotion(unittest.TestCase):
 def test_crouch_cant_preserves_view_depth_during_the_whole_transition(self):
  H=self.load('draw_seq')[-1];base=globals_(self.o,self.p,H);D=self.delta(self.load('crouch_offset_anim')[0])
  for w in (.125,.25,.375,.5,.625,.75,.875,1.):
   G=globals_(self.o,self.p,self.add(H,D,w));q=G['def_c_base'].to_quaternion()@base['def_c_base'].to_quaternion().inverted();v=q.to_exponential_map()
   self.assertLess(abs(G['def_c_base'].translation.y-base['def_c_base'].translation.y),.001,'cant brings the long rear housing through the fixed eye')
   self.assertLess(abs(math.degrees(v.x)),.01,'crouch pitch makes rear stock swing toward the eye')
   self.assertLess(abs(math.degrees(v.z)),.01,'crouch yaw makes rear stock swing toward the eye')

 def test_compiled_fire_and_movement_layers_keep_contact(self):
  import hashlib
  doc=json.loads((BUILD/'native-all.json').read_text(encoding='utf-8-sig'));motion=json.loads((BUILD/'native-motion.json').read_text(encoding='utf-8-sig'));fire=json.loads((BUILD/'native-fire.json').read_text(encoding='utf-8-sig'))
  digest=hashlib.sha256((BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl').read_bytes()).hexdigest()
  self.assertEqual(doc['source_sha256'],digest);self.assertEqual(motion['source_sha256'],digest);self.assertEqual(fire['source_sha256'],digest)
  o=[b['name'] for b in doc['bones']];p={b['name']:o[b['parent']] if b['parent']>=0 else None for b in doc['bones']}
  def local(v):return {o[x['index']]:matrix(x['pos'],Euler(x['rot'],'XYZ').to_quaternion()) for x in v['locals']}
  rows=motion['poses']+fire['poses'];worst=degrees=roll=kick=0.;samples=0
  for anchor in ('@draw_seq','ads_in_anim'):
   H=local(max((v for v in doc['poses'] if v['name']==anchor),key=lambda v:v['frame']));HG=globals_(o,p,H)
   for row in rows:
    D=local(row)
    for w in (.25,.5,.75,1.):
     L={n:matrix(H[n].translation+D[n].translation*w,H[n].to_quaternion()@Quaternion().slerp(D[n].to_quaternion(),w)) for n in o};G=globals_(o,p,L)
     if anchor=='@draw_seq' and row['name']=='attack_anim':
      q=G['def_c_base'].to_quaternion()@HG['def_c_base'].to_quaternion().inverted()
      # The compiled fixed view looks along +X (authored view was -Y).
      current_roll=abs(math.degrees(q.to_exponential_map().x));roll=max(roll,current_roll);kick=max(kick,angle(q))
      self.assertLess(current_roll,.01,'converted weapon/sight rolls sideways')
      self.assertLess(angle(q),1.2)
     for hand in ('def_l_wrist','def_r_wrist','def_r_finIndexC','def_r_finThumbC'):
      a=G['def_c_base'].inverted()@G[hand];b=HG['def_c_base'].inverted()@HG[hand];error=(a.translation-b.translation).length;da=angle(a.to_quaternion().rotation_difference(b.to_quaternion()));worst=max(worst,error);degrees=max(degrees,da);samples+=1
      self.assertLess(error,.002,f'{row["name"]}/{row["frame"]}/{w}/{hand}: compiled floating grip')
      self.assertLess(da,.01)
  (BUILD/'compiled-visual-motion-validation.json').write_text(json.dumps(dict(model_sha256=digest,decoded_movement_frames=len(motion['poses']),decoded_attack_frames=len(fire['poses']),contact_samples=samples,max_position_error=worst,max_angle_error=degrees,max_shot_roll_degrees=roll,max_shot_rotation_degrees=kick),indent=2))

 @classmethod
 def setUpClass(cls):
  r=json.loads((BUILD/'rig.json').read_text());cls.o=r['order'];cls.p=r['parent']
 def load(self,n):return smd(BUILD/'view/anims'/(n+'.smd'))[2]
 def delta(self,f):return {n:Matrix.Rotation(math.pi/2,4,'Z')@f[n] if self.p[n] is None else f[n] for n in self.o}
 def add(self,a,d,w):return {n:matrix(a[n].translation+d[n].translation*w,a[n].to_quaternion()@Quaternion().slerp(d[n].to_quaternion(),w)) for n in self.o}
 def test_movement_and_recoil_keep_native_grip_at_fractional_weights(self):
  names=MOVEMENT+('attack_anim','attack_ads_anim','attack_onehanded_anim','attack_onehanded_ads_anim')
  for anchor in ('draw_seq','ads_in_anim'):
   H=self.load(anchor)[-1];base=globals_(self.o,self.p,H)
   for name in names:
    for frame,f in enumerate(self.load(name)):
     for w in (.25,.5,1):
      G=globals_(self.o,self.p,self.add(H,self.delta(f),w))
      for hand in ('def_l_wrist','def_r_wrist','def_r_finIndexC','def_r_finThumbC'):
       a=G['def_c_base'].inverted()@G[hand];b=base['def_c_base'].inverted()@base[hand]
       self.assertLess((a.translation-b.translation).length,.002,f'{anchor}/{name}/{frame}/{w}/{hand}: floating grip')
       self.assertLess(angle(a.to_quaternion().rotation_difference(b.to_quaternion())),.01)
 def test_firing_has_no_sideways_roll_and_has_reduced_visible_kick(self):
  H=self.load('draw_seq')[-1];base=globals_(self.o,self.p,H)['def_c_base']
  for f in self.load('attack_anim'):
   gun=globals_(self.o,self.p,self.add(H,self.delta(f),1))['def_c_base']
   q=gun.to_quaternion()@base.to_quaternion().inverted();rotation=q.to_exponential_map()
   self.assertLess(abs(math.degrees(rotation.y)),.01,'shot rolls the weapon and optic sideways')
   self.assertLess(angle(q),1.2,'visual recoil exceeds requested reduced strength')
   self.assertLess((gun.translation-base.translation).length,.35)
 def test_airborne_duck_is_not_cancelled_by_vertical_speed(self):
  code=(ROOT/'src/client/prowler_stance.nut').read_text()
  self.assertNotIn('GetVelocity().LengthSqr() <',code,'jump velocity cancels the crouch pose')
  self.assertIn('IsInputCommandHeld( IN_DUCK )',code,'airborne duck input is ignored until grounded hull crouch')

if __name__=='__main__':
 r=unittest.main(argv=['feedback_motion'],exit=False)
 if not r.result.wasSuccessful():raise RuntimeError('FEEDBACK_MOTION_FAILED')

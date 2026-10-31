"""Visible motion direction, transition endpoints and source-surface fidelity."""
import sys,json,math,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
sys.path.insert(0,str(ROOT/'src/tools'))
from mdl_mesh import read_mdl_mesh

class DynamicIntegrity(unittest.TestCase):
 def authored(self,name):
  o,p,frames,_=smd(BUILD/'view/anims'/(name+'.smd'));return [globals_(o,p,f) for f in frames]

 def test_regular_sprint_stays_on_right_and_right_hand_keeps_grip(self):
  frames=self.authored('sprint_seq');baseline=Clip(SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_base_v_animRig/draw_0.cast');held=globals_(baseline.order,baseline.parent,baseline.sample(baseline.end));grip=held['def_c_base'].inverted()@held['def_r_wrist']
  for i,G in enumerate(frames):
   self.assertLess(G['def_c_base'].translation.x,-2.,f'frame{i}: raised gun moved to left side')
   actual=G['def_c_base'].inverted()@G['def_r_wrist']
   self.assertLess((actual.translation-grip.translation).length,.025,'free hand used as trigger hand')

 def test_sprint_loop_has_no_sleeve_or_gun_seam(self):
  frames=self.authored('sprint_seq')
  for n in ('def_c_base','def_l_wrist','def_r_wrist','def_l_elbow','def_r_elbow'):
   self.assertLess((frames[0][n].translation-frames[-1][n].translation).length,.01,n)
   self.assertLess(math.degrees(frames[0][n].to_quaternion().rotation_difference(frames[-1][n].to_quaternion()).angle),.1,n)

 def test_all_absolute_descriptors_author_the_same_rigid_counter_seat(self):
  rig=json.loads((BUILD/'rig.json').read_text(encoding='utf-8'));expected=Matrix(rig['rest_local']['def_c_proscreen'])
  for name,meta in rig['animations'].items():
   if meta['delta']:continue
   _,_,frames,_=smd(BUILD/'view/anims'/(name.removeprefix('@')+'.smd'))
   for i,f in enumerate(frames):
    self.assertLess((f['def_c_proscreen'].translation-expected.translation).length,.0001,f'{name}/{i}: stale CAR accessory seat in absolute layer')

 def test_sprint_equip_and_holster_keep_native_hidden_endpoints(self):
  base=SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_base_v_animRig'
  for name,source,index in [('sprintdraw_seq','sprintdraw_0',0),('sprintholster_seq','sprintholster_0',-1)]:
   c=Clip(base/(source+'.cast'));expected=globals_(c.order,c.parent,c.sample(0 if index==0 else c.end))['def_c_base'];actual=self.authored(name)[index]['def_c_base']
   self.assertLess((actual.translation-expected.translation).length,.002,f'{name}: hidden endpoint replaced by held pose')

 def test_normal_raise_from_sprint_finishes_with_two_handed_grip(self):
  c=Clip(SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_base_v_animRig/draw_0.cast');held=globals_(c.order,c.parent,c.sample(c.end))
  for name in ('sprintraise_seq','sprintraise_seq_air','sprintraise_seq_regrip'):
   G=self.authored(name)[-1]
   for hand in ('def_l_wrist','def_r_wrist'):
    a=G['def_c_base'].inverted()@G[hand];b=held['def_c_base'].inverted()@held[hand]
    self.assertLess((a.translation-b.translation).length,.025,f'{name}/{hand}: wrong handed exit')

 def test_counter_is_higher_than_0210_in_held_view(self):
  rig=json.loads((BUILD/'rig.json').read_text(encoding='utf-8'));G=self.authored('draw_seq')[-1];camera=Euler((math.pi/2,0,math.pi/2),'XYZ').to_matrix().to_4x4()@Matrix.Rotation(math.pi,4,'Y');compiler=Matrix.Rotation(math.pi/2,4,'Z')
  old=Matrix(rig['rest_global']['def_c_proscreen']);old.translation=Vector((1.047551,47.0,11.0));body=G['def_c_base']@Matrix(rig['rest_global']['def_c_base']).inverted();new=G['def_c_proscreen'].translation
  def vertical(point):
   p=camera.inverted()@compiler@point;return -p.y/-p.z
  self.assertLess(vertical(new)-vertical((body@old).translation),-.015,'latest feedback requests the screen higher than0.2.10')

 def test_all_counter_standoff_faces_follow_stock_renderer_winding(self):
  for filename in ('ptpov_car101','w_car101'):
   path=BUILD/'compiler_game/models/weapons/car101'/(filename+'_conv.mdl');d=path.read_bytes();md=read_mdl_mesh(path,include={(4,1)});v=d.index(b'IDSV');count=struct.unpack_from('<i',d,v+16)[0];fn,fo=struct.unpack_from('<ii',d,v+48);start=v+struct.unpack_from('<i',d,v+56)[0];logical=[]
   for k in range(fn):
    lod,first,length=struct.unpack_from('<iii',d,v+fo+12*k)
    if lod>=0:logical.extend(range(first,first+length))
   if not fn:logical=list(range(count))
   normals=[Vector(struct.unpack_from('<3f',d,start+48*k+28)) for k in logical]
   for part in md['parts']:
    for face in part['faces']:
     a,b,c=[Vector(md['vertices'][i]) for i in face];dot=(b-a).cross(c-a).dot(sum((normals[i] for i in face),Vector()))
     self.assertLessEqual(dot,1e-7,f'{filename}: inside-out screen support face')

 def test_crouch_to_idle_rows_keep_native_transition_and_correct_ads_anchor(self):
  rig=json.loads((BUILD/'rig.json').read_text(encoding='utf-8'))
  self.assertEqual(rig['animations']['idle_check_anim_nod']['source'],'crouch_to_idle_0')
  c=Clip(SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_base_v_animRig/ads_in_0.cast');held=globals_(c.order,c.parent,c.sample(c.end))
  actual=self.authored('iron_anim_nod')[-1]['def_c_base'];expected=held['def_c_base']
  self.assertLess((actual.translation-expected.translation).length,.002,'crouch exit ADS row uses hip anchor')

if __name__=='__main__':
 r=unittest.main(argv=['dynamic_integrity'],exit=False)
 if not r.result.wasSuccessful():raise RuntimeError('DYNAMIC_INTEGRITY_FAILED')

"""Low right carry and swing requested by the user, including transition seams."""
import sys,json,math,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *

class LowSprint(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.r=json.loads((BUILD/'rig.json').read_text());cls.o=cls.r['order'];cls.p=cls.r['parent']
 def poses(self,name):return [globals_(self.o,self.p,L) for L in smd(BUILD/'view/anims'/(name+'.smd'))[2]]
 def test_normal_sprint_is_lower_with_a_visible_native_step_cycle(self):
  frames=self.poses('sprint_seq');held=self.poses('draw_seq')[-1]['def_c_base'];guns=[G['def_c_base'] for G in frames]
  for i,g in enumerate(guns):
   self.assertLess(g.translation.z,held.translation.z-2.,f'{i}: gun is still raised')
   self.assertLess((g.to_3x3()@Vector((0,0,1))).z,.6,f'{i}: barrel still points upward')
   self.assertLess(g.translation.x,-2.,f'{i}: low carry crosses to left')
   self.assertLess(g.translation.y,-3.,f'{i}: low carry retreats behind fixed eye')
  self.assertGreater(max(g.translation.z for g in guns)-min(g.translation.z for g in guns),.5,'step swing was replaced by a static low pose')
  self.assertEqual(self.r['animations']['@sprint_seq']['source'],'sprint_0')
 def test_low_carry_transitions_meet_loop_without_moving_hidden_or_held_ends(self):
  running=self.poses('sprint_seq')[0]
  for name,endpoint in [('sprintdraw_seq',-1),('sprintholster_seq',0),('sprintraise_seq',0),('sprintraise_seq_air',0),('sprintraise_seq_regrip',0)]:
   G=self.poses(name)[endpoint]
   for n in ('def_c_base','def_r_wrist','def_l_wrist'):
    self.assertLess((G[n].translation-running[n].translation).length,.025,f'{name}/{n}: sprint endpoint seam')
    self.assertLess(math.degrees(G[n].to_quaternion().rotation_difference(running[n].to_quaternion()).angle),.1,f'{name}/{n}: sprint endpoint rotation seam')
 def test_all_compiled_sprint_frames_keep_body_visible_and_low(self):
  import hashlib
  sys.path.insert(0,str(ROOT/'src/tools'));from mdl_mesh import read_mdl_mesh
  path=BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl';doc=json.loads((BUILD/'native-dynamic.json').read_text(encoding='utf-8-sig'));digest=hashlib.sha256(path.read_bytes()).hexdigest();self.assertEqual(doc['source_sha256'],digest)
  o=[b['name'] for b in doc['bones']];p={b['name']:o[b['parent']] if b['parent']>=0 else None for b in doc['bones']};bind=globals_(o,p,{b['name']:matrix(b['pos'],Euler(b['rot'],'XYZ').to_quaternion()) for b in doc['bones']})
  mesh=read_mdl_mesh(path,include={(0,0)});ids={i for part in mesh['parts'] for f in part['faces'] for i in f};camera=(Euler((math.pi/2,0,math.pi/2),'XYZ').to_matrix().to_4x4()@Matrix.Rotation(math.pi,4,'Y')).inverted();focal=640/math.tan(math.radians(70)/2);rows=[]
  for pose in doc['poses']:
   if pose['name']!='@sprint_seq':continue
   G=globals_(o,p,{o[v['index']]:matrix(v['pos'],Euler(v['rot'],'XYZ').to_quaternion()) for v in pose['locals']});gun=G['def_c_base'];T=camera@gun@bind['def_c_base'].inverted();visible=0
   self.assertLess(gun.translation.z,-9.4);self.assertGreater(gun.translation.x,1.)
   for i in ids:
    v=T@Vector(mesh['vertices'][i]);depth=-v.z
    visible+=depth>.05 and 0<640+v.x/depth*focal<1280 and 0<360-v.y/depth*focal<720
   ratio=visible/len(ids);self.assertGreater(ratio,.25,f'frame{pose["frame"]}: low carry leaves viewport');rows.append(dict(frame=pose['frame'],gun_position=list(gun.translation),visible_body_ratio=ratio))
  self.assertEqual(len(rows),self.r['animations']['@sprint_seq']['frames'])
  (BUILD/'compiled-low-sprint-validation.json').write_text(json.dumps(dict(model_sha256=digest,all_loop_frames=len(rows),minimum_visible_body_ratio=min(r['visible_body_ratio'] for r in rows),samples=rows),indent=2))

if __name__=='__main__':
 r=unittest.main(argv=['low_sprint'],exit=False)
 if not r.result.wasSuccessful():raise RuntimeError('LOW_SPRINT_FAILED')

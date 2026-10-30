"""User-requested visible corrections, including source-independent mechanical gates."""
import sys,json,math,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
from arm_fit import ArmFit
sys.path.insert(0,str(ROOT/'src/tools'))
from mdl_lib import Mdl

class Refinements(unittest.TestCase):
 def test_sprint_uses_full_right_hand_motion(self):
  rig=json.loads((BUILD/'rig.json').read_text())
  self.assertEqual(rig['animations']['@sprint_seq']['source'],'sprint_onehanded_0')
  self.assertEqual(rig['animations']['@sprint_seq'].get('motion_policy'),'full_native_right_hand')

 def test_crouch_does_not_straighten_on_every_hip_shot(self):
  code=(ROOT/'src/client/prowler_stance.nut').read_text()
  self.assertNotIn('Time() - lastShot >',code)
  self.assertIn('player.IsCrouched()',code)

 def test_counter_is_forward_of_previous_receiver_seat(self):
  rig=json.loads((BUILD/'rig.json').read_text())
  self.assertGreaterEqual(rig['proscreen_mount'][2],11.0-1e-5) # float32 Vector storage

 def test_compiled_kill_counter_canvas_is_not_occluded_by_gun(self):
  from mdl_mesh import read_mdl_mesh
  from mathutils.bvhtree import BVHTree
  sys.path.insert(0,CFG['tools_root']);import rui_editor
  path=BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl';doc=json.loads((BUILD/'native-all.json').read_text(encoding='utf-8-sig'));o=[b['name'] for b in doc['bones']];p={b['name']:o[b['parent']] if b['parent']>=0 else None for b in doc['bones']}
  bind=globals_(o,p,{b['name']:matrix(b['pos'],Euler(b['rot'],'XYZ').to_quaternion()) for b in doc['bones']});pose=max((v for v in doc['poses'] if v['name']=='@draw_seq'),key=lambda v:v['frame']);G=globals_(o,p,{o[v['index']]:matrix(v['pos'],Euler(v['rot'],'XYZ').to_quaternion()) for v in pose['locals']})
  mesh=read_mdl_mesh(path,include={(0,0)});vertices=[sum((G[o[b]]@bind[o[b]].inverted()@Vector(v)*w for b,w in links),Vector()) for v,links in zip(mesh['vertices'],mesh['weights'])];tree=BVHTree.FromPolygons(vertices,[f for part in mesh['parts'] for f in part['faces']],all_triangles=True)
  panel=next(m for m in rui_editor.inspect_mdl(path)['meshes'] if m['name'].endswith('pro_screen_rui_upper'))
  points=[G['def_c_proscreen']@Vector(v['position']) for v in panel['vertices']];points.append(sum(points,Vector())/len(points))
  for point in points:
   hit=tree.ray_cast(Vector(),point.normalized(),point.length-.03)
   self.assertIsNone(hit[0],'native ammo housing hides the external counter canvas')

 def test_held_right_wrist_is_not_forced_into_a_large_bend(self):
  rig=json.loads((BUILD/'rig.json').read_text());o=rig['order'];p=rig['parent'];rest={n:Matrix(v) for n,v in rig['rest_local'].items()}
  c=Clip(SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_base_v_animRig/draw_0.cast');N=globals_(c.order,c.parent,c.sample(c.end));target={}
  for n in o:target[n]=N[n] if n in N else (target[p[n]] if p[n] else Matrix.Identity(4))@rest[n]
  fit=ArmFit(o,p);actual=fit(target);local=locals_(o,p,actual);q=local['def_r_wrist'].to_quaternion();axis=fit.constants['r']['wrist'].translation.normalized();twist=Quaternion(axis,2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w));bend=q@twist.inverted()
  self.assertLess(math.degrees(bend.angle),32.0,'right wrist bent40deg despite exact gun contact')
  for n in ('def_r_wrist','def_l_wrist','def_c_base'):
   self.assertLess((actual[n].translation-target[n].translation).length,.002,'wrist correction moved a native contact')

 def test_drum_has_seven_stationary_index_poses_and_no_attack_overtravel(self):
  model=Mdl(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl')
  self.assertIn('prowler_drum',model.poseparams(),'per-shot phase cannot persist after attack animation')
  seq=next((s for s in model.sequences() if s['name']=='prowler_drum_autoplay'),None)
  self.assertIsNotNone(seq)
  if seq is None:return
  self.assertEqual(seq['blend'],[7,1])
  import struct
  row=next(r for r,n in model.table(192,232,4) if n==seq['name'])
  weights=struct.unpack_from('<'+'f'*len(model.bones()),model.d,row+model.i(row+156))
  doc=json.loads((BUILD/'native-all.json').read_text(encoding='utf-8-sig'))
  rotors={'def_c_reactive_spinner_coils','def_c_reactive_spinner_1'}
  for pose in doc['poses']:
   if not pose['name'].startswith('prowler_drum_index_'):continue
   for v in pose['locals']:
    if model.bones()[v['index']] in rotors:continue
    self.assertLess(Vector(v['pos']).length,.001,'drum layer has a nonzero fallback position')
    self.assertLess(math.degrees(Euler(v['rot'],'XYZ').to_quaternion().angle),.02,'drum layer changes root/hand/screen basis')
  for k,name in enumerate(seq['anims']):
   _,_,frames,_=smd(BUILD/'view/anims'/(name+'.smd'))
   for frame in frames:
    for rotor,sign in [('def_c_reactive_spinner_coils',1),('def_c_reactive_spinner_1',-1)]:
     self.assertLess(frame[rotor].translation.length,1e-7)
     expected=Quaternion((0,0,1),sign*k*math.pi/3)
     self.assertLess(1-abs(frame[rotor].to_quaternion().dot(expected)),1e-5)
  for name in model.anims():
   if name.startswith('attack_'):
    _,_,frames,_=smd(BUILD/'view/anims'/(name+'.smd'))
    for frame in frames:
     for rotor in ('def_c_reactive_spinner_coils','def_c_reactive_spinner_1','def_c_reactive_spinner_2'):
      self.assertLess(abs(frame[rotor].to_quaternion().angle),1e-6,'attack clip still spins multiple revolutions')

if __name__=='__main__':
 result=unittest.main(argv=['refinements'],exit=False)
 if not result.result.wasSuccessful():raise RuntimeError('REQUESTED_REFINEMENTS_FAILED')

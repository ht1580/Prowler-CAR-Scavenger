"""User-visible stance and trigger policy, checked on authored and compiled clips."""
import sys,json,math,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
sys.path.insert(0,str(ROOT/'src/tools'))
from mdl_lib import Mdl

class MotionPolicy(unittest.TestCase):
 def test_autoplay_cannot_move_arms_or_spin_the_drum(self):
  rig=json.loads((BUILD/'rig.json').read_text())
  for name in ('idle_anim_autoplay','idle_ads_anim_autoplay'):
   order,parent,frames,_=smd(BUILD/'view/anims'/(name+'.smd'))
   for index,frame in enumerate(frames):
    for n,M in frame.items():
     if parent[n] is None:M=Matrix.Rotation(math.pi/2,4,'Z')@M
     self.assertLess(max(abs(M[i][j]-(i==j)) for i in range(4) for j in range(4)),1e-5,f'{name}/{index}/{n}: always-on motion while not firing')

 def test_crouch_has_a_controlled_pose_in_the_active_autoplay_grid(self):
  model=Mdl(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl')
  seq={s['name']:s for s in model.sequences()}
  self.assertIn('prowler_crouch',model.poseparams(),'engine has no crouch-driven parameter')
  self.assertEqual(seq['idle_seq_autoplay']['blend'],[2,2])
  self.assertEqual(seq['idle_seq_autoplay']['anims'][-2:],['crouch_offset_anim','crouch_offset_ads_anim'])
  manifest=json.loads((BUILD/'stage/Prowler.CAR.Scavenger/mod.json').read_text())
  self.assertEqual(manifest.get('Scripts'),[dict(Path='prowler_stance.nut',RunOn='CLIENT',ClientCallback=dict(After='ProwlerStance_Init'))],'CLIENT pose driver is not registered')

 def test_regular_sprint_uses_the_regular_source_stance(self):
  rig=json.loads((BUILD/'rig.json').read_text())
  self.assertEqual(rig['animations']['@sprint_seq']['source'],'sprint_onehanded_0','normal sprint does not use the right-hand cycle')

 def test_compiled_drum_channels_are_stationary_without_attack(self):
  import hashlib
  rig=json.loads((BUILD/'rig.json').read_text())
  doc=json.loads((BUILD/'native-all.json').read_text(encoding='utf-8-sig'))
  self.assertEqual(doc['source_sha256'],hashlib.sha256((BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl').read_bytes()).hexdigest())
  rotors=('def_c_reactive_spinner_coils','def_c_reactive_spinner_1','def_c_reactive_spinner_2')
  import struct
  model=Mdl(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl')
  consumers={}
  for (row,name),seq in zip(model.table(192,232,4),model.sequences()):
   weights=struct.unpack_from('<'+str(len(rig['order']))+'f',model.d,row+model.i(row+156))
   self.assertTrue(all(math.isfinite(w) and w>=-1e-6 for w in weights),'invalid sequence weight table')
   for index in seq['raw']:consumers.setdefault(index,[]).append((seq,weights))
  checks=0
  for pose in doc['poses']:
   if pose['name'].startswith(('attack_','prowler_drum_index_')):continue
   for value in pose['locals']:
    name=rig['order'][value['index']]
    if name not in rotors:continue
    active=[seq for seq,weights in consumers.get(pose['index'],[]) if weights[value['index']]>1e-6]
    # Unreferenced descriptors and zero-weight channels do not drive the model.
    # Their decoder fallback values are not active rotor motion.
    if not active:continue
    self.assertEqual(len({seq['delta'] for seq in active}),1)
    delta=active[0]['delta']
    actual=matrix(value['pos'],Euler(value['rot'],'XYZ').to_quaternion())
    expected=Matrix.Identity(4) if delta else Matrix(rig['rest_local'][name])
    self.assertLess((actual.translation-expected.translation).length,.001,f'{pose["name"]}/{name}: rotor position')
    self.assertLess(math.degrees(actual.to_quaternion().rotation_difference(expected.to_quaternion()).angle),.02,f'{pose["name"]}/{name}: rotor turns without a shot')
    checks+=1
  self.assertGreater(checks,150)

if __name__=='__main__':
 result=unittest.main(argv=['motion_policy'],exit=False)
 if not result.result.wasSuccessful():raise RuntimeError('MOTION_POLICY_FAILED')

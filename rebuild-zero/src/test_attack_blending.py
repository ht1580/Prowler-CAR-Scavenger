"""Reject additive recoil clips that inject a resting arm pose at every shot."""
import sys, math, json, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import *

def angle(m):
 q=m.to_quaternion()
 return math.degrees(2*math.atan2(Vector((q.x,q.y,q.z)).length,abs(q.w)))

class AttackBlending(unittest.TestCase):
 def test_converted_model_keeps_contact_during_crouch_and_recoil_blends(self):
  doc=json.loads((BUILD/'native-all.json').read_text(encoding='utf-8-sig'))
  fire=json.loads((BUILD/'native-fire.json').read_text(encoding='utf-8-sig'))
  import hashlib,struct
  model=BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl'
  self.assertEqual(doc['source_sha256'],hashlib.sha256(model.read_bytes()).hexdigest())
  self.assertEqual(fire['source_sha256'],doc['source_sha256'])
  o=[b['name'] for b in doc['bones']];p={b['name']:o[b['parent']] if b['parent']>=0 else None for b in doc['bones']}
  def local(v):return {o[x['index']]:matrix(x['pos'],Euler(x['rot'],'XYZ').to_quaternion()) for x in v['locals']}
  def add(a,d,w):return {n:matrix(a[n].translation+d[n].translation*w,a[n].to_quaternion()@Quaternion().slerp(d[n].to_quaternion(),w)) for n in o}
  held=local(max((v for v in doc['poses'] if v['name']=='@draw_seq'),key=lambda v:v['frame']))
  crouch=local(next(v for v in doc['poses'] if v['name']=='crouch_offset_anim'))
  for n in o:
   if n=='def_c_spineC':continue
   self.assertLess(crouch[n].translation.length,.001,n)
   self.assertLess(angle(crouch[n]),.01,n)
  sys.path.insert(0,str(ROOT/'src/tools'));from mdl_lib import Mdl
  mdl=Mdl(model);row=next(r for r,n in mdl.table(192,232,4) if n=='idle_seq_autoplay')
  weights=struct.unpack_from('<'+'f'*len(o),mdl.d,row+mdl.i(row+156))
  self.assertEqual(weights[o.index('def_c_spineC')],1.)
  worst=0.;samples=0
  for v in fire['poses']:
   if v['name']!='attack_anim':continue
   for fw in (0,.25,.5,.75,1):
    firing=add(held,local(v),fw);base=globals_(o,p,firing)
    for cw in (0,.25,.5,.75,1):
     actual=globals_(o,p,add(firing,crouch,cw))
     for hand in ('def_l_wrist','def_r_wrist','def_r_forearm'):
      a=actual['def_c_base'].inverted()@actual[hand];b=base['def_c_base'].inverted()@base[hand]
      error=(a.translation-b.translation).length;worst=max(worst,error);samples+=1
      self.assertLess(error,.002)
      self.assertLess(angle(a.inverted()@b),.01)
  (BUILD/'compiled-attack-blending-validation.json').write_text(json.dumps(dict(model_sha256=doc['source_sha256'],contact_samples=samples,max_crouch_contact_error=worst,stage='decoded v53 additive local transforms; stance after attack'),indent=2))

 def test_crouch_and_fractional_fire_keep_the_same_hand_gun_relation(self):
  rig=json.loads((BUILD/'rig.json').read_text());o=rig['order'];p=rig['parent']
  def read(name):return smd(BUILD/'view/anims'/(name+'.smd'))[2]
  def offsets(fr):return {n:Matrix.Rotation(math.pi/2,4,'Z')@fr[n] if p[n] is None else fr[n] for n in o}
  def add(a,d,w):return {n:matrix(a[n].translation+d[n].translation*w,a[n].to_quaternion()@Quaternion().slerp(d[n].to_quaternion(),w)) for n in o}
  held=read('draw_seq')[-1];crouch=offsets(read('crouch_offset_anim')[0])
  worst=0.;samples=0
  for f in read('attack_anim'):
   for fw in (0,.25,.5,.75,1):
    firing=add(held,offsets(f),fw);base=globals_(o,p,firing)
    for cw in (0,.25,.5,.75,1):
     actual=globals_(o,p,add(firing,crouch,cw))
     for hand in ('def_l_wrist','def_r_wrist','def_r_forearm'):
      a=actual['def_c_base'].inverted()@actual[hand];b=base['def_c_base'].inverted()@base[hand]
      error=(a.translation-b.translation).length;worst=max(worst,error);samples+=1
      self.assertLess(error,.002,f'crouch={cw},fire={fw},{hand}: separate additive arm/weapon chains lose contact')
      self.assertLess(angle(a.inverted()@b),.01)
  (BUILD/'attack-blending-validation.json').write_text(json.dumps(dict(stage='source local additive composition; stance after attack',contact_samples=samples,max_crouch_contact_error=worst),indent=2))

 def test_every_attack_returns_the_arm_overlay_to_neutral(self):
  rig=json.loads((BUILD/'rig.json').read_text())
  for name in rig['animations']:
   if not name.startswith('attack_'):continue
   _,_,frames,_=smd(BUILD/'view/anims'/(name+'.smd'))
   for index in (0,-1):
    for bone in ('def_r_shoulder','def_r_elbow','def_r_forearm','def_r_wrist'):
     with self.subTest(animation=name,frame=index,bone=bone):
      self.assertLess(angle(frames[index][bone]),1.,'resting arm twist becomes a repeated shot impulse')

 def test_fire_layer_does_not_repose_the_distal_sleeve(self):
  rig=json.loads((BUILD/'rig.json').read_text())
  for name in rig['animations']:
   if not name.startswith('attack_'):continue
   _,_,frames,_=smd(BUILD/'view/anims'/(name+'.smd'))
   self.assertLess(max(angle(f['def_r_forearm']) for f in frames),10.,name)

if __name__=='__main__':
 r=unittest.main(argv=['attack_blending'],exit=False)
 if not r.result.wasSuccessful():raise RuntimeError('ATTACK_BLENDING_FAILED')

"""Full-frame converted absolute action verification, beyond descriptor/index checks."""
import sys,json,math,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
rig=json.loads((BUILD/'rig.json').read_text(encoding='utf-8'))
doc=json.loads((BUILD/'native-dynamic.json').read_text(encoding='utf-8-sig'))
model=BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl'
assert doc['source_sha256']==hashlib.sha256(model.read_bytes()).hexdigest()
o=rig['order'];p=rig['parent'];bind={b['name']:matrix(b['pos'],Euler(b['rot'],'XYZ').to_quaternion()) for b in doc['bones']}
cache={};counts={};max_gun=0.;max_contact=0.;max_angle=0.;screen_error=0.;max_hip_relative=0.;max_right_pos=0.;max_right_angle=0.
for pose in doc['poses']:
 n=pose['name']
 for v in pose['locals']:assert all(math.isfinite(x) for x in v['pos']+v['rot']),(n,pose['frame'],v['index'])
 if rig['animations'][n]['delta']:continue
 if n not in cache:
  _,_,f,_=smd(BUILD/'view/anims'/(n.removeprefix('@')+'.smd'));cache[n]=f
 expected={n:Matrix.Rotation(math.pi/2,4,'Z')@M for n,M in globals_(o,p,cache[n][pose['frame']]).items()};actual=globals_(o,p,{o[v['index']]:matrix(v['pos'],Euler(v['rot'],'XYZ').to_quaternion()) for v in pose['locals']})
 counts[n]=counts.get(n,0)+1
 err=(actual['def_c_base'].translation-expected['def_c_base'].translation).length
 if err>max_gun:max_gun=err;worst=(n,pose['frame'],err)
 a=actual['def_c_hip'].inverted()@actual['def_c_base'];b=expected['def_c_hip'].inverted()@expected['def_c_base'];max_hip_relative=max(max_hip_relative,(a.translation-b.translation).length)
 q=actual['def_c_base'].to_quaternion().rotation_difference(expected['def_c_base'].to_quaternion());max_angle=max(max_angle,math.degrees(2*math.atan2(Vector((q.x,q.y,q.z)).length,abs(q.w))))
 for hand in ('def_l_wrist','def_r_wrist'):
  a=actual['def_c_base'].inverted()@actual[hand];b=expected['def_c_base'].inverted()@expected[hand];max_contact=max(max_contact,(a.translation-b.translation).length)
 for bone in ('def_r_elbow','def_r_forearm','def_r_wrist'):
  a=actual['def_c_hip'].inverted()@actual[bone];b=expected['def_c_hip'].inverted()@expected[bone];max_right_pos=max(max_right_pos,(a.translation-b.translation).length)
  q=a.to_quaternion().rotation_difference(b.to_quaternion());max_right_angle=max(max_right_angle,math.degrees(2*math.atan2(Vector((q.x,q.y,q.z)).length,abs(q.w))))
 a=actual['def_c_base'].inverted()@actual['def_c_proscreen'];b=expected['def_c_base'].inverted()@expected['def_c_proscreen'];e=(a.translation-b.translation).length
 if e>screen_error:screen_error=e;screen_worst=(n,pose['frame'],e,list(a.translation),list(b.translation))
for n in ('@sprint_seq','@sprintdraw_seq','@sprintholster_seq','@sprintraise_seq','@sprintraise_seq_air','@sprintraise_seq_regrip'):
 assert counts[n]==rig['animations'][n]['frames'],(n,counts.get(n))
print('ERRORS',max_gun,max_contact,max_angle,screen_error,worst,screen_worst,max_hip_relative,flush=True)
# Vector48 truncates the constant hip37.312496 to37.28125 (0.031246).
# Keep a separate absolute compression bound and the existing0.02 motion/contact
# bound relative to hip, so a shared quantization offset cannot hide trajectory loss.
assert max_right_pos<.02 and max_right_angle<.1
assert max_gun<.05 and max_hip_relative<.02 and max_contact<.02 and max_angle<.1 and screen_error<.01
report=dict(model_sha256=doc['source_sha256'],frames=sum(counts.values()),actions=counts,max_right_arm_hip_relative_position_error=max_right_pos,max_right_arm_angle_error=max_right_angle,max_hip_relative_gun_error=max_hip_relative,max_gun_position_error=max_gun,max_gun_angle_error=max_angle,max_hand_contact_error=max_contact,max_screen_relative_error=screen_error,finite=True,passed=True)
(BUILD/'compiled-dynamic-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('COMPILED_DYNAMIC_OK',json.dumps(report))

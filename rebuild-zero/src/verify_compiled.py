"""Compare compiled payload to native source; do not accept names/flags alone as proof."""
import sys,json,math,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
from motion_contract import EXTRA_ANIMS,validate as validate_motion_contract
sys.path.insert(0,str(ROOT/'src/tools'))
from mdl_mesh import read_mdl_mesh
rig=json.loads((BUILD/'rig.json').read_text());order=rig['order'];parent=rig['parent'];rest={n:Matrix(v) for n,v in rig['rest_global'].items()}
modelpath=BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl';m=mdldump(modelpath);stock=mdldump(STOCK/'models/weapons/car101/ptpov_car101.mdl')
def names(model,off,stride,rel=0):return [n for _,n in model['table'](off,stride,rel)]
result=dict(stock_sequences=names(m,192,232,4)==names(stock,192,232,4),stock_anim_order=names(m,184,92,4)==names(stock,184,92,4)+list(EXTRA_ANIMS),stock_attachment_names=names(m,244,92)==names(stock,244,92),bone_order=names(m,160,244)==order)
from mdl_lib import Mdl
validate_motion_contract(Mdl(STOCK/'models/weapons/car101/ptpov_car101.mdl'),Mdl(modelpath))
result['explicit_crouch_hold_contract']=True
eng=json.loads((BUILD/'engine-view.json').read_text(encoding='utf-8-sig'));bs=eng['bones'];L={b['name']:matrix(b['pos'],quat(b['quat'])) for b in bs};G=globals_(order,parent,L);inverseError=bindError=0.
for n,b in zip(order,bs):
 c=b['p2b'];inv=Matrix(((c[0][0],c[1][0],c[2][0],c[3][0]),(c[0][1],c[1][1],c[2][1],c[3][1]),(c[0][2],c[1][2],c[2][2],c[3][2]),(0,0,0,1)))
 inverseError=max(inverseError,max(abs((inv@G[n])[i][j]-(i==j)) for i in range(4) for j in range(4)))
 bindError=max(bindError,max(abs(G[n][i][j]-rest[n][i][j]) for i in range(4) for j in range(4)))
result.update(inverse_bind=inverseError<.0001,bind_error=bindError,inverse_error=inverseError)
decoded=json.loads((BUILD/'native-fire.json').read_text(encoding='utf-8-sig'));maxpos=maxangle=0.;keys=0
for pose in decoded['poses']:
 use=rig['animations'][pose['name']]['source'];c=Clip(SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_react_v21_scavenger_v_animRig'/(use+'.cast'));raw=c.sample(min(pose['frame'],c.end));loc={order[v['index']]:v for v in pose['locals']}
 assert rig['animations'][pose['name']]['delta']
 for n in rig['extra']:
  if n not in raw:continue
  v=loc.get(n,dict(pos=[0,0,0],rot=[0,0,0]));expected=raw[n];actual=matrix(v['pos'],Euler(v['rot'],'XYZ').to_quaternion())
  maxpos=max(maxpos,(actual.translation-expected.translation).length)
  q=actual.to_quaternion().rotation_difference(expected.to_quaternion());maxangle=max(maxangle,math.degrees(2*math.atan2(Vector((q.x,q.y,q.z)).length,abs(q.w))));keys+=1
spinshift=0.
for pose in decoded['poses']:
 for v in pose['locals']:
  if order[v['index']] in ('def_c_reactive_spinner_coils','def_c_reactive_spinner_1','def_c_reactive_spinner_2'):spinshift=max(spinshift,Vector(v['pos']).length)
# Non-rotor position channels are compressed by the SFM -> v53 chain. Keep a sub-0.01-unit bound
# and separately require the actual rotor pivots to remain fixed; do not conflate spring travel with drift.
result.update(native_spin_samples=maxpos<.01 and maxangle<.1 and spinshift<.001,native_keys=keys,max_native_position_error=maxpos,max_native_angle_error=maxangle,max_rotor_pivot_translation=spinshift)
mesh=read_mdl_mesh(modelpath);bad=[]
for i,w in enumerate(mesh['weights']):
 if abs(sum(v for _,v in w)-1)>.00001 or any(b>=len(order) or v<0 or not math.isfinite(v) for b,v in w):bad.append(i)
result.update(vtx_weights=not bad,vertex_count=len(mesh['vertices']),bad_vertex_weights=bad[:20])
# Compare converted absolute wrist/gun/magazine contact to the fresh authored SMD at sampled frames.
absdoc=json.loads((BUILD/'native-view.json').read_text(encoding='utf-8-sig'));contact=0.
for pose in absdoc['poses']:
 if rig['animations'][pose['name']]['delta']:continue
 name=pose['name'].removeprefix('@');_,_,frames,_=smd(BUILD/'view/anims'/(name+'.smd'));expected=globals_(order,parent,frames[min(pose['frame'],len(frames)-1)])
 loc={order[v['index']]:matrix(v['pos'],Euler(v['rot'],'XYZ').to_quaternion()) for v in pose['locals']};actual=globals_(order,parent,{n:loc.get(n,L[n]) for n in order})
 for hand in ('def_l_wrist','def_r_wrist'):
  a=actual[hand].inverted()@actual['def_c_magazine'];e=expected[hand].inverted()@expected['def_c_magazine'];contact=max(contact,(a.translation-e.translation).length)
result['converted_contact_error']=contact
originalWorld=json.loads((BUILD/'native-world-original.json').read_text(encoding='utf-8-sig'));builtWorld=json.loads((BUILD/'native-world.json').read_text(encoding='utf-8-sig'));worldError=0.
for a,b in zip(originalWorld['poses'],builtWorld['poses']):
 assert (a['name'],a['frame'],a['frames'])==(b['name'],b['frame'],b['frames'])
 x=next(v for v in a['locals'] if v['index']==0);y=next(v for v in b['locals'] if v['index']==0);worldError=max(worldError,max(abs(u-v) for u,v in zip(x['pos']+x['rot'],y['pos']+y['rot'])))
worldResult=dict(poses=len(originalWorld['poses']),root_max_error=worldError,root_preserved=worldError<.0001)
(BUILD/'world-validation.json').write_text(json.dumps(worldResult,indent=2));assert worldResult['root_preserved']
(BUILD/'compiled-verification.json').write_text(json.dumps(result,indent=2))
print('COMPILED_VERIFICATION',json.dumps(result),flush=True)
assert all(result[k] for k in ('stock_sequences','stock_anim_order','stock_attachment_names','bone_order','inverse_bind','native_spin_samples','vtx_weights')) and contact<.02,result
print('COMPILED_VERIFICATION_OK',flush=True)

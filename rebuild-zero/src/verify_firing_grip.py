"""Compare source-native firing hand/gun relations against the converted model, across all keys."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
rig=json.loads((BUILD/'rig.json').read_text());order=rig['order'];parent=rig['parent'];L={n:Matrix(v) for n,v in rig['rest_local'].items()}
fire=json.loads((BUILD/'native-fire.json').read_text(encoding='utf-8-sig'));BASE=SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_base_v_animRig';REACT=BASE.parent/'anims_prowler_react_v21_scavenger_v_animRig'
cache={};worstpos=worstangle=0.;checked=0;idlekeys=0
jobs=[(p,False) for p in fire['poses']]
idlePath=BUILD/'native-idle.json'
if idlePath.exists():jobs += [(p,True) for p in json.loads(idlePath.read_text(encoding='utf-8-sig'))['poses']]
for p,isIdle in jobs:
 name=p['name'];oh='onehanded' in name;ads='ads' in name;anchorName='ads_in_onehanded_0' if oh and ads else ('draw_onehanded_0' if oh else ('ads_in_0' if ads else 'draw_0'))
 if anchorName not in cache:
  c=Clip(BASE/(anchorName+'.cast'));cache[anchorName]=(c,globals_(c.order,c.parent,c.sample(c.end)))
 anchor,AG=cache[anchorName];_,_,frames,_=smd(BUILD/'view/anims'/((anchorName.replace('ads_in_onehanded_0','ads_in_onehanded_anim').replace('ads_in_0','ads_in_anim').replace('draw_onehanded_0','draw_onehanded_seq').replace('draw_0','draw_seq'))+'.smd'));held=frames[-1]
 source=('idle_1' if ads else 'idle_0') if isIdle else rig['animations'][name]['source']
 if source not in cache:cache[source]=Clip((BASE if isIdle else REACT)/(source+'.cast'))
 c=cache[source];time=p['frame']*c.end/max(1,p['frames']-1) if isIdle else min(p['frame'],c.end);delta=c.sample(time);SL={}
 for n in c.order:
  baseline=(AG[c.parent[n]].inverted()@AG[n] if c.parent[n] else AG[n]) if n in AG and (not c.parent[n] or c.parent[n] in AG) else c.rest[n]
  SL[n]=matrix(baseline.translation+delta[n].translation,baseline.to_quaternion()@delta[n].to_quaternion())
 expected=globals_(c.order,c.parent,SL);dl={order[v['index']]:v for v in p['locals']};ML={}
 for n in order:
  v=dl.get(n,dict(pos=(0,0,0),rot=(0,0,0)));ML[n]=matrix(held[n].translation+Vector(v['pos']),held[n].to_quaternion()@Euler(v['rot'],'XYZ').to_quaternion())
 actual=globals_(order,parent,ML)
 for hand in ('def_l_wrist','def_r_wrist'):
  a=actual['def_c_base'].inverted()@actual[hand];e=expected['def_c_base'].inverted()@expected[hand];worstpos=max(worstpos,(a.translation-e.translation).length)
  q=a.to_quaternion().rotation_difference(e.to_quaternion());worstangle=max(worstangle,math.degrees(2*math.atan2(Vector((q.x,q.y,q.z)).length,abs(q.w))));checked+=1
  if isIdle:idlekeys+=1
result=dict(keys=checked,idle_keys=idlekeys,firing_keys=checked-idlekeys,max_position_error=worstpos,max_angle_error=worstangle)
(BUILD/'native-firing-grip.json').write_text(json.dumps(result,indent=2));print('NATIVE_FIRING_GRIP',json.dumps(result),flush=True)
assert worstpos<.025 and worstangle<.15,result
print('NATIVE_FIRING_GRIP_OK',flush=True)

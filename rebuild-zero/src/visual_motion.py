"""Apply cosmetic recoil/bob on the existing common arm and weapon branch."""
import math
from mathutils import Matrix,Vector,Quaternion
from core import globals_,matrix

MOVEMENT=('run_anim_static','run_anim','run_anim_layer','walk_anim_static','walk_anim','walk_ads_anim','walk_anim_nocam','switch_to_jump_anim','switch_to_land_anim','switch_to_jump_crouch_anim','switch_to_land_crouch_anim','switch_to_jump_ads_anim','switch_to_land_ads_anim','idle_check_anim','idle_check_ads_anim')
JOINT='def_c_spineC'

def add(base,delta):
 return {n:matrix(base[n].translation+delta[n].translation,base[n].to_quaternion()@delta[n].to_quaternion()) for n in base}

def shared_delta(order,parent,baseline,transform,preserved=None):
 delta={n:Matrix.Identity(4) for n in order}
 if preserved:delta.update(preserved)
 rooted=add(baseline,delta);G=globals_(order,parent,rooted)
 local=G[parent[JOINT]].inverted()@transform@G[JOINT]
 delta[JOINT]=matrix(local.translation-baseline[JOINT].translation,baseline[JOINT].to_quaternion().inverted()@local.to_quaternion())
 return delta

def bounded_motion(basegun,position,rotation,position_scale=.35,pitch=.35,yaw=.15,max_position=.35,max_angle=1.2):
 # Authored view looks along -Y, with Z up. Rotation about Y rolls the
 # entire gun/sight sideways; remove that cosmetic component explicitly.
 move=Vector(position)*position_scale
 if move.length>max_position:move*=max_position/move.length
 v=rotation.to_exponential_map();v=Vector((v.x*pitch,0.,v.z*yaw))
 limit=math.radians(max_angle)
 if v.length>limit:v*=limit/v.length
 q=Quaternion(v) if v.length>1e-10 else Quaternion()
 goal=matrix(basegun.translation+move,q@basegun.to_quaternion())
 return goal@basegun.inverted()

def recoil(order,parent,baseline,native_gun):
 G=globals_(order,parent,baseline);held=G['def_c_base']
 transform=bounded_motion(held,native_gun.translation-held.translation,native_gun.to_quaternion()@held.to_quaternion().inverted())
 return shared_delta(order,parent,baseline,transform)

def movement(order,parent,baseline,stock_order,stock_parent,stock_held,stock_delta):
 # Preserve the stock root/camera tracks (and their coordinate convention).
 # Retarget the remaining gun bob, rather than copying CAR arm pose offsets
 # onto the Prowler grip. Every blended weight now moves both hands with it.
 preserved={n:stock_delta[n].copy() for n in ('jx_c_delta','jx_c_pov','jx_c_camera') if n in stock_delta}
 SG=globals_(stock_order,stock_parent,stock_held)
 posed=globals_(stock_order,stock_parent,add(stock_held,{n:stock_delta[n] for n in stock_order}))
 root=next(n for n in stock_order if stock_parent[n] is None)
 before=SG[root].inverted()@SG['def_c_base'];after=posed[root].inverted()@posed['def_c_base']
 rooted=globals_(order,parent,add(baseline,{n:preserved.get(n,Matrix.Identity(4)) for n in order}))
 basis=rooted[root].to_quaternion()
 position=basis@(after.translation-before.translation)
 rotation=basis@(after.to_quaternion()@before.to_quaternion().inverted())@basis.inverted()
 transform=bounded_motion(rooted['def_c_base'],position,rotation,position_scale=.45,pitch=.45,yaw=.25,max_position=.35,max_angle=2.)
 return shared_delta(order,parent,baseline,transform,preserved)

"""Two-bone TF2 sleeve fit. Hands, props and magazine are immutable world-space targets."""
import math
from mathutils import Matrix,Vector,Quaternion
from core import smd,globals_,locals_,STOCK

class ArmFit:
 fixed_body_bones=('def_c_hip','def_c_spineA','def_c_spineB','def_c_spineC','def_c_neckA','jx_c_neckB','def_c_neckB','def_c_head','def_l_clav','def_r_clav')
 def __init__(self,order,parent):
  self.order,self.parent=order,parent
  self.swivel={}
  so,sp,sf,_=smd(STOCK/'view/ptpov_car101_anims/draw_seq.smd');self.body=sf[-1]
  self.constants={}
  for side in 'lr':
   d={n:self.body[f'def_{side}_{n}'] for n in ('shoulderMid','elbow','elbowB','forearm','wrist')}
   self.constants[side]=d
 def __call__(self,target):
  # Replacing torso/clavicle locals moves sleeves behind the eye. Solve the arms to the unchanged
  # native wrist targets; do not independently push a wrist or magazine outside the camera frame.
  L=locals_(self.order,self.parent,target)
  for n in self.fixed_body_bones:
   L[n]=self.body[n].copy()
  forward=target['jx_c_camera'].to_3x3().col[2].normalized()
  G=globals_(self.order,self.parent,L)
  # The support arm's reach must not push the trigger shoulder forward too.
  # Fit clavicle reach independently, retaining the torso and native wrists.
  for side,r in self.constants.items():
   clav=f'def_{side}_clav';baseline=L[clav].copy()
   direction=G[self.parent[clav]].to_3x3().inverted()@forward
   length=(r['shoulderMid'].translation+r['elbow'].translation).length+r['wrist'].translation.length
   preferred=-2.0 if side=='r' else 0.0
   def reach(shift):
    L[clav]=Matrix.Translation(direction*shift)@baseline
    posed=globals_(self.order,self.parent,L)
    return (target[f'def_{side}_wrist'].translation-posed[f'def_{side}_shoulder'].translation).length/length
   choices=[]
   for i in range(181):
    error=max(0.,reach(preferred+i*.1)-.995);choices.append((error,i*.1))
    if error==0.:break
   _,extra=min(choices);reach(preferred+extra)
   G=globals_(self.order,self.parent,L)
   shoulder=G[f'def_{side}_shoulder'].translation
   reachVector=target[f'def_{side}_wrist'].translation-shoulder
   correction=max(0.,reachVector.length-length*.995)
   if correction:
    if correction>4.:raise ValueError(f'{side} sleeve requires excessive lateral reach correction: {correction}')
    localCorrection=G[self.parent[clav]].to_3x3().inverted()@(reachVector.normalized()*correction)
    L[clav]=Matrix.Translation(localCorrection)@L[clav]
    G=globals_(self.order,self.parent,L)
  for side,r in self.constants.items():
   n=lambda x:f'def_{side}_{x}'
   S=G[n('shoulder')].translation;W=target[n('wrist')].translation
   av=r['shoulderMid'].translation+r['elbow'].translation;bv=r['wrist'].translation
   a,b=av.length,bv.length;D=(W-S).length
   if D>a+b+.015:raise ValueError(f'{side} wrist target unreachable: {D} > {a+b}')
   axis=(W-S).normalized();x=(a*a-b*b+D*D)/(2*D);h=math.sqrt(max(0.,a*a-x*x))
   pole=target[n('elbow')].translation-S;pole-=axis*pole.dot(axis)
   if pole.length<1e-5:pole=axis.cross(Vector((0,0,1)))
   pole.normalize();across=axis.cross(pole)
   hinge=r['elbow'].to_quaternion().axis.normalized()
   eq=r['elbow'].to_quaternion()
   if Vector((eq.x,eq.y,eq.z)).dot(hinge)<0:hinge=-hinge
   # The upper-arm/forearm hinge plane fixes shoulder roll without twisting the hinge itself.
   def frame(v,w):
    z=(w-v*v.dot(w)).normalized();return Matrix((v,z,v.cross(z))).transposed()
   def candidate(phi):
    E=S+axis*x+(pole*math.cos(phi)+across*math.sin(phi))*h
    u=(E-S).normalized();f=(W-E).normalized();theta=u.angle(f)
    localFore=(Matrix.Rotation(theta,3,hinge)@bv).normalized()
    shoulder=Matrix.Translation(S)@(frame(u,f)@frame(av.normalized(),localFore).transposed()).to_4x4()
    elbow=shoulder@r['shoulderMid']@Matrix.Translation(r['elbow'].translation)@Matrix.Rotation(theta,4,hinge)
    wrist=elbow.inverted()@target[n('wrist')];q=wrist.to_quaternion()
    twist=math.remainder(2*math.atan2(Vector((q.x,q.y,q.z)).dot(bv.normalized()),q.w),2*math.pi)
    cost=abs(twist)+.25*abs(phi)
    if side in self.swivel:cost+=.5*abs(math.remainder(phi-self.swivel[side],2*math.pi))
    return cost,shoulder,theta,phi
   best=min((candidate(math.radians(k)) for k in range(-180,181,10)),key=lambda c:c[0])
   _,shoulder,theta,phi=min((candidate(best[3]+math.radians(k)) for k in range(-9,10)),key=lambda c:c[0]);self.swivel[side]=phi
   L[n('shoulder')]=G[n('clav')].inverted()@shoulder
   L[n('shoulderMid')]=r['shoulderMid'].copy()
   L[n('elbow')]=Matrix.Translation(r['elbow'].translation)@Matrix.Rotation(theta,4,hinge)
   elbow=shoulder@L[n('shoulderMid')]@L[n('elbow')]
   wrist=elbow.inverted()@target[n('wrist')]
   # Preserve target translation exactly (also catches incorrect rest lengths or hinge orientation).
   assert (wrist.translation-bv).length<.02,(side,list(wrist.translation),list(bv))
   L[n('wrist')]=wrist
   L[n('elbowB')]=Matrix.Translation(r['elbowB'].translation)@r['elbowB'].to_quaternion().slerp(Quaternion(hinge,theta*.5),.5).to_matrix().to_4x4()
   q=wrist.to_quaternion();twist=2*math.atan2(Vector((q.x,q.y,q.z)).dot(bv.normalized()),q.w)
   L[n('forearm')]=Matrix.Translation(r['forearm'].translation)@Matrix.Rotation(twist*.5,4,bv.normalized())
  G=globals_(self.order,self.parent,L)
  # Root of the complete weapon subtree follows its immutable native target after torso adaptation.
  L['ja_c_propGun']=G[self.parent['ja_c_propGun']].inverted()@target['ja_c_propGun']
  G=globals_(self.order,self.parent,L)
  # Prop helpers are descendants of the preserved wrists. All source finger locals remain unchanged.
  return G

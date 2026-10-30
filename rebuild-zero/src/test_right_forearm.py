"""Actual TF2 right sleeve/hand deformation must follow native distal arm motion."""
import sys,json,math,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
from arm_fit import ArmFit
sys.path.insert(0,str(ROOT/'src/tools'))
from mdl_mesh import read_mdl_mesh
class RightForearm(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  rig=json.loads((BUILD/'rig.json').read_text(encoding='utf-8'));cls.order=rig['order'];cls.parent=rig['parent'];cls.rest={n:Matrix(v) for n,v in rig['rest_local'].items()}
  cls.datasets=[]
  for source in CFG['validation_arms']:
   def path(key):
    p=Path(source[key]);return p if p.is_absolute() else (ROOT/'src'/p).resolve()
   bs=json.loads(path('bones').read_text(encoding='utf-8-sig'))['bones'];names=[b['name'] for b in bs];ap={b['name']:names[b['parent']] if b['parent']>=0 else None for b in bs};al={b['name']:matrix(b['pos'],Euler(b['rot'],'XYZ').to_quaternion()) for b in bs};bind=globals_(names,ap,al)
   mesh=read_mdl_mesh(path('model'));allowed={n for n in names if n.startswith('def_r_fin') or n in ('def_r_elbow','def_r_forearm','def_r_wrist')}
   distal=[i for i,links in enumerate(mesh['weights']) if links and all(names[b] in allowed for b,w in links if w>.0001)];assert len(distal)>500
   cls.datasets.append(dict(name=path('model').name,names=names,bind=bind,mesh=mesh,distal=distal))
 def poses(self):
  base=SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_base_v_animRig'
  for name in ('draw_0','draw_onehanded_0','ads_in_0','ads_out_0','sprint_onehanded_0','sprintraise_0','reload_0','reload_empty_0','holster_0','drawfirst_0','switch_to_onehanded_0','switch_to_twohanded_0'):
   c=Clip(base/(name+'.cast'));self.assertFalse(c.additive)
   fit=ArmFit(self.order,self.parent)
   for frame in (0,c.end*.5,c.end):
    native=globals_(c.order,c.parent,c.sample_pose(frame));target={}
    for n in self.order:target[n]=native[n].copy() if n in native else (target[self.parent[n]] if self.parent[n] else Matrix.Identity(4))@self.rest[n]
    yield name,frame,target,fit(target)
 def test_native_elbow_and_forearm_are_not_straightened_to_fit_the_stock_shoulder(self):
  for name,frame,target,actual in self.poses():
   for bone in ('def_r_elbow','def_r_forearm'):
    self.assertLess((actual[bone].translation-target[bone].translation).length,.001,f'{name}/{frame}/{bone}: native forearm trajectory replaced')
    q=actual[bone].to_quaternion().rotation_difference(target[bone].to_quaternion());angle=math.degrees(2*math.atan2(Vector((q.x,q.y,q.z)).length,abs(q.w)))
    self.assertLess(angle,.01,f'{name}/{frame}/{bone}: cuff rotation changed')
 def test_actual_distal_sleeve_and_hand_vertices_keep_native_deformation(self):
  # This checks actual sleeve and glove skinning, rather than accepting equal wrist transforms.
  worst_by_model={d['name']:0. for d in self.datasets};poses=0
  for name,frame,target,actual in self.poses():
   poses+=1
   for data in self.datasets:
    def skinned(i,pose):
     v=Vector(data['mesh']['vertices'][i]);return sum((pose[data['names'][b]]@data['bind'][data['names'][b]].inverted()@v*w for b,w in data['mesh']['weights'][i]),Vector())
    worst=max((skinned(i,actual)-skinned(i,target)).length for i in data['distal'])
    worst_by_model[data['name']]=max(worst_by_model[data['name']],worst)
    self.assertLess(worst,.002,f"{data['name']}/{name}/{frame}: distal sleeve/palm shape differs by{worst:.3f}")
  (BUILD/'right-forearm-validation.json').write_text(json.dumps(dict(stage='authoring before MDL compression',poses=poses,meshes=[dict(name=d['name'],vertices=len(d['distal']),max_skin_position_error=worst_by_model[d['name']]) for d in self.datasets],source_native_distal_motion=True,threshold=.002),indent=2),encoding='utf-8')
 def test_grip_and_fingers_remain_at_the_native_targets(self):
  for name,frame,target,actual in self.poses():
   for n in self.order:
    if n=='def_r_wrist' or n.startswith('def_r_fin'):
     self.assertLess((actual[n].translation-target[n].translation).length,.0002,f'{name}/{frame}/{n}')
if __name__=='__main__':
 result=unittest.main(argv=['right_forearm'],exit=False)
 if not result.result.wasSuccessful():raise RuntimeError('RIGHT_FOREARM_FAILED')

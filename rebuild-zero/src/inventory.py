"""Inventory original CAST inputs, independent of the old Prowler build."""
import importlib.util,json,hashlib,math,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];TASK=ROOT.parents[1]
CFG=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'))
spec=importlib.util.spec_from_file_location('raw_cast',CFG['cast_parser'])
cast=importlib.util.module_from_spec(spec);spec.loader.exec_module(cast)
def walk(node):
 yield node
 for c in node.childNodes:yield from walk(c)
def first(path,typ):return next(n for r in cast.Cast.load(str(path)).Roots() for n in walk(r) if isinstance(n,typ))
source=(ROOT/'src'/CFG['original_export']).resolve()
modelpath=next((source/'apex_cast/mdl').rglob('*_v_LOD0.cast'))
model=first(modelpath,cast.Model);bones=model.Skeleton().Bones();weighted=collections.Counter()
for mesh in model.Meshes():
 if not mesh.Name().startswith(('body_0','clip_0','sight_front_1')):continue
 influence=mesh.MaximumWeightInfluence();ids=mesh.VertexWeightBoneBuffer();weights=mesh.VertexWeightValueBuffer()
 for i,b in enumerate(ids):
  if influence==1 or weights[i]>.001:weighted[bones[b].Name()]+=1
aroot=source/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler'
clips={};active=set()
for folder,names in [('anims_prowler_react_v21_scavenger_v_animRig',('fire_reactive_3','fire_optic_reactive_3','idle_reactive_layer_3','fire_onehanded_1')),('anims_prowler_base_v_animRig',('draw_0','ads_in_0','reload_0','reload_empty_0','idle_0','fire_0'))]:
 for name in names:
  p=aroot/folder/(name+'.cast');a=first(p,cast.Animation);moving=set();modes=set()
  for c in a.Curves():
   modes.add(c.Mode());v=c.KeyValueBuffer();prop=c.KeyPropertyName()
   if prop=='rq':isactive=any(abs(v[i])+abs(v[i+1])+abs(v[i+2])>.0001 for i in range(0,len(v),4))
   else:isactive=prop in ('tx','ty','tz') and max(map(abs,v),default=0)>.0001
   if isactive:moving.add(c.NodeName())
  if 'scavenger' in folder:active.update(moving)
  clips[name]=dict(frames=max(k for c in a.Curves() for k in c.KeyFrameBuffer())+1,fps=a.Framerate(),modes=sorted(modes),moving=sorted(moving),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
result=dict(model=str(modelpath),model_sha256=hashlib.sha256(modelpath.read_bytes()).hexdigest(),bone_count=len(bones),weighted_bones=dict(weighted),reactive_active_weighted=sorted(active&set(weighted)),clips=clips)
(ROOT/'inventory.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))

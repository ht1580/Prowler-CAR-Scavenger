"""Reconstruct the stock world-model contract directly from MDL tables and original CAST geometry."""
import sys,json,struct,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
# This reader is an extraction tool: it reads the ORIGINAL stock VVD/VTX, never an old mod model.
sys.path.insert(0,str(ROOT/'src/tools'))
from mdl_mesh import read_mdl_mesh
OUT=BUILD/'world';OUT.mkdir(exist_ok=True)
original=STOCK/'models/weapons/car101/w_car101.mdl';m=mdldump(original);table=m['table'];ii=m['i'];data=m['data']
bones=json.loads((ROOT/'stock-world.json').read_text(encoding='utf-8-sig'))['bones'];order=[b['name'] for b in bones];parent={b['name']:order[b['parent']] if b['parent']>=0 else None for b in bones}
L={b['name']:matrix(b['pos'],quat(b['quat'])) for b in bones};G=globals_(order,parent,L)
modelpath=Path(CFG['texture_source']).parents[1]/'01_模型_Models/prowler_react_v21_scavenger_w_LOD0.cast'
native=first(modelpath,cast.Model);nb=native.Skeleton().Bones();nn=[b.Name() for b in nb];np={b.Name():nn[b.ParentIndex()] if b.ParentIndex()>=0 else None for b in nb};nl={b.Name():matrix(b.LocalPosition(),quat(b.LocalRotation())) for b in nb};ng=globals_(nn,np,nl)
baseClip=Clip(SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_base_v_animRig/draw_0.cast');held=globals_(baseClip.order,baseClip.parent,baseClip.sample(baseClip.end))
so,sp,sf,_=smd(STOCK/'view/ptpov_car101_anims/draw_seq.smd');stockHeld=globals_(so,sp,sf[-1])
right=lambda pose:pose['def_c_base'].inverted()@pose['ja_r_propHand']
T=right(stockHeld)@right(held).inverted();base=G['def_c_base'];place=base@T@ng['def_c_base'].inverted()
rest={n:v.copy() for n,v in G.items()};rig=json.loads((BUILD/'rig.json').read_text())
# Mount child attachments to the same rigid world transform as the new body. Both IK roles remain
# named/indexed exactly as stock; the stock l_hand_ik is the grip hand, r_hand_ik the support hand.
for n in order:
 if n not in ('ja_c_propGun','weapon_bone','def_c_base','l_hand_ik','r_hand_ik'):G[n]=base@T@base.inverted()@G[n]
lc=stockHeld['def_c_base'].inverted()@stockHeld['ja_l_propHand'];lp=held['def_c_base'].inverted()@held['ja_l_propHand']
G['r_hand_ik']=base@T@lp@lc.inverted()@base.inverted()@rest['r_hand_ik']
L=locals_(order,parent,G)
material=r'models\Weapons_R2\prowler_zero\scavenger';triangles=[]
for mesh in native.Meshes():
 if not mesh.Name().startswith(('body_0','clip_0','sight_front_1','sight_on')):continue
 vb=mesh.VertexPositionBuffer();norm=mesh.VertexNormalBuffer();uv=mesh.VertexUVLayerBuffer(0);fb=mesh.FaceBuffer();R=place.to_3x3()
 for k in range(0,len(fb),3):
  vs=[]
  for v in fb[k:k+3]:vs.append((place@Vector(vb[v*3:v*3+3]),(R@Vector(norm[v*3:v*3+3])).normalized(),tuple(uv[v*2:v*2+2]),[('def_c_base',1.)]))
  triangles.append((material,vs))
assert triangles,'Original world CAST mesh names need explicit mapping'
write_smd(OUT/'body.smd',order,parent,[L],triangles)
stockMesh=read_mdl_mesh(original);textures=[name for _,name in table(208,44)];stockParts=table(236,16);groups=[]
vvd=data.index(b'IDSV');nv=ii(vvd+16);start=vvd+ii(vvd+56);fixcount,fixoff=ii(vvd+48,2);logical=[]
for k in range(fixcount):
 lod,firstVertex,count=ii(vvd+fixoff+12*k,3)
 if lod>=0:logical.extend(range(firstVertex,firstVertex+count))
if not fixcount:logical=list(range(nv))
normals=[Vector(struct.unpack_from('<3f',data,start+48*k+28)) for k in logical]
for bp,(r,name) in enumerate(stockParts):
 nmodels=ii(r+4);lines=[f'$bodygroup "{name}"','{']
 for option in range(nmodels):
  part=next((p for p in stockMesh['parts'] if p['bodypart']==bp and p['model']==option),None)
  if bp==0:lines.append(' studio "body.smd"');continue
  if part is None:lines.append(' blank');continue
  file=f'attachment_{bp}_{option}.smd';tris=[]
  for face,materialIndex in zip(part['faces'],part['materials']):
   vs=[]
   # Original VTX faces already use the renderer's winding. SMD compilation reverses that order;
   # undo it here so imported stock optics keep the original outward-facing surfaces.
   for v in reversed(face):
    w=[(order[i],weight) for i,weight in stockMesh['weights'][v]]
    # Rigidly carry each stock optic by its own joint's changed transform.
    transform=G[w[0][0]]@rest[w[0][0]].inverted()
    vs.append((transform@Vector(stockMesh['vertices'][v]),(transform.to_3x3()@normals[v]).normalized(),stockMesh['uv'][v],w))
   tris.append((textures[materialIndex],vs))
  write_smd(OUT/file,order,parent,[L],tris);lines.append(f' studio "{file}"')
 lines.append('}');groups.extend(lines)
qc=['$modelname "weapons/car101/w_car101.mdl"','$maxverts 65000','$surfaceprop "weapon"','$contents "solid"','$cdmaterials ""',*groups]
qc+=['$texturegroup "skinfamilies"','{']+[' { "'+material+'" }']*9+['}']
for n in order:
 t=L[n].translation;e=[math.degrees(v) for v in L[n].to_euler('XYZ')]
 qc.append(f'$definebone "{n}" "{parent[n] or ""}" {t.x:.9f} {t.y:.9f} {t.z:.9f} {e[1]:.9f} {e[2]:.9f} {e[0]:.9f} 0 0 0 0 0 0')
 qc.append(f'$bonemerge "{n}"')
for r,name in table(244,92):
 bone=order[ii(r+8)];values=struct.unpack_from('<12f',data,r+12);M=Matrix((values[0:4],values[4:8],values[8:12],(0,0,0,1)));p=M.translation;e=[math.degrees(v) for v in M.to_euler('XYZ')]
 qc.append(f'$attachment "{name}" "{bone}" {p.x:.9f} {p.y:.9f} {p.z:.9f} rotate {e[1]:.9f} {e[2]:.9f} {e[0]:.9f}')
_,_,stockIdle,_=smd(STOCK/'world/world_idle.smd')
# Preserve the original root sequence pose. Child rest transforms reflect the grip placement above.
for r,name in table(192,232,4):
 ar=table(184,92,4)[len([line for line in qc if line.startswith('$sequence')])][0]
 count=ii(ar+16);fps=struct.unpack_from('<f',data,ar+8)[0];frames=[]
 for f in range(count):
  frame={n:L[n].copy() for n in order};frame[order[0]]=stockIdle[min(f,len(stockIdle)-1)][order[0]].copy();frames.append(frame)
 file=name+'.smd';write_smd(OUT/file,order,parent,frames)
 activity=m['text'](r+ii(r+8));loop=' loop' if ii(r+12)&1 else ''
 eventCount,eventOffset=ii(r+24,2);events=[]
 for k in range(eventCount):
  e=r+eventOffset+80*k;cycle,event,eventType=struct.unpack_from('<fii',data,e);options=data[e+12:e+76].split(b'\0')[0].decode('ascii');nameOffset=ii(e+76)
  eventName=m['text'](e+nameOffset) if eventType&1024 and nameOffset else str(event)
  events.append(f' {{ event {eventName} {int(round(cycle*(count-1)))} "{options}" }}')
 qc.append(f'$sequence "{name}" {{\n "{file}"\n activity "{activity}" 1\n fps {fps:g}{loop}\n'+ '\n'.join(events)+'\n}')
(OUT/'w_car101.qc').write_text('\n'.join(qc)+'\n',encoding='ascii')
(BUILD/'world-rig.json').write_text(json.dumps(dict(order=order,parent=parent,grip_transform=[list(r) for r in T],rest_global={n:[list(r) for r in G[n]] for n in order},source_model=str(modelpath),triangles=len(triangles)),indent=2))
print('WORLD_GENERATION_OK',len(order),len(triangles),flush=True)

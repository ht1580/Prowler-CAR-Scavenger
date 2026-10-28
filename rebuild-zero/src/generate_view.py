"""Build new SMD/QC from original model/native CAST clips and the unmodified stock CAR contract."""
import sys,json,math,re,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
from arm_fit import ArmFit
OUT=BUILD/'view';OUT.mkdir(exist_ok=True);ANIM=OUT/'anims';ANIM.mkdir(exist_ok=True)
stock=mdldump(STOCK/'models/weapons/car101/ptpov_car101.mdl')
so,sp,sf,_=smd(STOCK/'view/v_car101.smd');stockG=globals_(so,sp,sf[0])
mesh,ao,ap,al,ag=model();inventory=json.loads((ROOT/'inventory.json').read_text(encoding='utf-8'))
# Every extra joint has source mesh weights AND an independently animated channel. Stock indices
# retain their complete prefix; custom joints keep their original parent instead of sharing the bolt.
required=set(inventory['reactive_active_weighted'])
for n in list(required):
 p=ap[n]
 while p and p not in so:required.add(p);p=ap[p]
extra=[n for n in ao if n in required and n not in so]
order=so+extra;parent=dict(sp)
for n in extra:parent[n]=ap[n]
assert all(parent[n] in order or parent[n] is None for n in order)
restG={n:(ag[n].copy() if n in ag else stockG[n].copy()) for n in order}
OPTICS=('def_c_holo','def_c_acgs','def_c_cro','def_c_sight_on')
BASE=SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_base_v_animRig'
REACT=BASE.parent/'anims_prowler_react_v21_scavenger_v_animRig'
cache={}
def clip(name,reactive=False):
 key=(name,reactive)
 if key not in cache:cache[key]=Clip((REACT if reactive else BASE)/(name+'.cast'))
 return cache[key]
def original_pose(c,t,anchor_override=None):
 L=c.sample(t)
 if c.additive:
  anchor=clip(anchor_override or ('draw_onehanded_0' if 'onehanded' in c.path.name else 'draw_0'))
  A=globals_(anchor.order,anchor.parent,anchor.sample(anchor.end));baseline={}
  for n in c.order:
   baseline[n]=(A[c.parent[n]].inverted()@A[n] if c.parent[n] else A[n]) if n in A and (not c.parent[n] or c.parent[n] in A) else c.rest[n]
  L={n:matrix(baseline[n].translation+L[n].translation,baseline[n].to_quaternion()@L[n].to_quaternion()) for n in c.order}
 G=globals_(c.order,c.parent,L);out={}
 for n in order:
  if n in G and n not in OPTICS and n!='def_c_proscreen':out[n]=G[n].copy()
  else:out[n]=(out[parent[n]] if parent[n] else Matrix.Identity(4))@restL[n]
 return out
# Derive optic placement from the source ADS eye relative to the gun, not a manual viewmodel offset.
ads=clip('ads_in_0');ga=globals_(ads.order,ads.parent,ads.sample(ads.end))
_,_,cf,_=smd(STOCK/'view/ptpov_car101_anims/ads_in_anim.smd');gc=globals_(so,sp,cf[-1])
opticShift=ag['def_c_base'].to_3x3()@((ga['def_c_base'].inverted()@ga['jx_c_camera']).translation-(gc['def_c_base'].inverted()@gc['jx_c_camera']).translation)
for n in OPTICS:restG[n]=Matrix.Translation(opticShift)@stockG[n]
# Mount on the native receiver side (measured source surface x=0.772), not the rear
# vertical pipe. Derive the bone origin from the original housing's backing plane.
proscreenScale=.65
_,_,_,proscreenTriangles=smd(STOCK/'view/v_proscreen.smd')
proscreenOffsets=[stockG['def_c_proscreen'].inverted()@v[0] for _,vs in proscreenTriangles for v in vs]
proscreenOrigin=Vector((.772+.010-proscreenScale*min(v.x for v in proscreenOffsets),46.10,4.50))
restG['def_c_proscreen']=Matrix.Translation(proscreenOrigin)@stockG['def_c_proscreen'].to_quaternion().to_matrix().to_4x4()
restL=locals_(order,parent,restG)
def mapped(n):
 while n not in order:n=ap[n]
 return n
def native_triangles(m):
 vb=m.VertexPositionBuffer();fb=m.FaceBuffer();nb=m.MaximumWeightInfluence();ib=m.VertexWeightBoneBuffer();wb=m.VertexWeightValueBuffer();uv=m.VertexUVLayerBuffer(0);norm=m.VertexNormalBuffer();out=[]
 for k in range(0,len(fb),3):
  vs=[]
  for i in fb[k:k+3]:
   links={}
   for j in range(nb):
    weight=wb[i*nb+j] if nb>1 else 1.
    if weight>.001:
     name=mapped(ao[ib[i*nb+j]]);links[name]=links.get(name,0.)+weight
   w=sorted(links.items(),key=lambda x:-x[1])[:3];s=sum(v for _,v in w);w=[(n,v/s) for n,v in w]
   vs.append((Vector(vb[i*3:i*3+3]),Vector(norm[i*3:i*3+3]),tuple(uv[i*2:i*2+2]),w))
  out.append((r'models\Weapons_R2\prowler_zero\scavenger',vs))
 return out
meshconsumers={n:0 for n in extra}
for m in mesh.Meshes():
 target=next((x for prefix,x in [('body_0','body.smd'),('clip_0','magazine.smd'),('sight_front_1','iron.smd')] if m.Name().startswith(prefix)),None)
 if not target:continue
 tris=native_triangles(m)
 for _,vs in tris:
  for _,_,_,w in vs:
   for n,v in w:
    if n in meshconsumers:meshconsumers[n]+=1
 write_smd(OUT/target,order,parent,[restL],tris)
# Optics use unmodified stock meshes, translated rigidly with the corresponding optic joints.
for name in ('v_holo.smd','v_acgs.smd','v_cro.smd','v_proscreen.smd'):
 _,_,_,tris=smd(STOCK/'view'/name)
 if name!='v_proscreen.smd':tris=[(m,[(p+opticShift,n,uv,w) for p,n,uv,w in vs]) for m,vs in tris]
 else:tris=[(m,[(restG['def_c_proscreen']@((stockG['def_c_proscreen'].inverted()@p)*proscreenScale),n,uv,w) for p,n,uv,w in vs]) for m,vs in tris]
 write_smd(OUT/name,order,parent,[restL],tris)
# StudioMDL adds +90 degrees about world Z to absolute animation roots. The compiled
# subtract reference must match the explicit $definebone bind, not acquire that rotation.
# Mesh bind SMDs above stay in model space; compensate only the reference animation root.
referenceL={n:M.copy() for n,M in restL.items()}
for n in order:
 if parent[n] is None:referenceL[n]=Matrix.Rotation(-math.pi/2,4,'Z')@referenceL[n]
write_smd(OUT/'ref.smd',order,parent,[referenceL]);write_smd(ANIM/'ref.smd',order,parent,[referenceL])
fit=ArmFit(order,parent)
stats=dict(source_kind='native Apex CAST',absolute_frames=0,max_hand_gun_position_error=0.,max_magazine_hand_position_error=0.,native_reactive_keys=0,max_reactive_matrix_error=0.,unused_added_bones=[n for n,c in meshconsumers.items() if not c],independent_offscreen_push=False,clips=[],extra_bones=extra)

def select(name):
 n=name.removeprefix('@');oh='onehanded' in n;tail='_onehanded' if oh else ''
 if n.startswith('ads_in'):return 'ads_in'+tail+'_0'
 if n.startswith('ads_out'):return 'ads_out'+tail+'_0'
 if n.startswith('reload'):
  key='reload_empty' if 'empty' in n else 'reload'
  if 'late2' in n:key+='_late2'
  elif 'late1' in n:key+='_late1'
  return key+tail+('_1' if 'crouch' in n and not oh else '_0')
 if n.startswith('drawfirst'):return 'drawfirst'+tail+'_0'
 if n.startswith('draw'):return 'draw'+tail+'_0'
 if n.startswith('holster'):return 'holster'+tail+'_0'
 if n.startswith('raise'):return 'raise'+tail+'_0'
 if n.startswith('lower'):return 'lower'+tail+'_0'
 if n.startswith('sprintdraw'):return 'sprintdraw_0'
 if n.startswith('sprintholster'):return 'sprintholster_0'
 if n.startswith('sprintraise'):return 'sprintraise'+tail+'_0'
 if n.startswith('sprint'):return 'sprint'+tail+'_0'
 if n.startswith('switch_to_onehanded'):return 'switch_to_onehanded_0'
 if n.startswith('switch_to_twohanded'):return 'switch_to_twohanded_0'
 if 'iron' in n or 'idle_check' in n or 'regrip' in n:return 'crouch_to_idle_0'
 return None

def delta_absolute(delta):
 # SFM needs absolute local source poses and an explicit subtract(ref,0) to write actual DELTA data.
 return {n:matrix(restL[n].translation+delta[n].translation,restL[n].to_quaternion()@delta[n].to_quaternion()) for n in order}

def relative_delta(base,pose):
 return {n:matrix(pose[n].translation-base[n].translation,base[n].to_quaternion().inverted()@pose[n].to_quaternion()) for n in order}

# The delta baseline must be the SAME arm-adapted endpoint used by the authored draw/ADS clips.
# Solve their complete timelines once so the IK swivel history cannot change the overlay baseline.
anchors={}
for native,car in [('draw_0','draw_seq'),('draw_onehanded_0','draw_onehanded_seq'),('ads_in_0','ads_in_anim'),('ads_in_onehanded_0','ads_in_onehanded_anim')]:
 c=clip(native);_,_,old,_=smd(STOCK/'view/ptpov_car101_anims'/(car+'.smd'));fit.swivel={}
 for f in range(len(old)):G=fit(original_pose(c,c.end*f/max(1,len(old)-1)))
 anchors[native]=locals_(order,parent,G)

payload={};verification=[]
for row,descriptor in stock['table'](184,92,4):
 fit.swivel={}
 name=descriptor.removeprefix('@');_,_,oldframes,_=smd(STOCK/'view/ptpov_car101_anims'/(name+'.smd'))
 flags=stock['i'](row+12);isdelta=bool(flags&4);noanim=bool(flags&0x20);frames=[];source=select(descriptor)
 if name=='ref':frames=[referenceL]
 elif name.startswith('attack_'):
  oh='onehanded' in name;ads='ads' in name
  use=('fire_onehanded_1' if ads else 'fire_onehanded_0') if oh else ('fire_optic_reactive_3' if ads else 'fire_reactive_3');c=clip(use,True)
  anchorName='ads_in_onehanded_0' if oh and ads else ('draw_onehanded_0' if oh else ('ads_in_0' if ads else 'draw_0'));baseline=anchors[anchorName]
  for f in range(len(oldframes)):
   raw=c.sample(min(f,c.end));target=original_pose(c,min(f,c.end),anchorName);posed=locals_(order,parent,fit(target));D=relative_delta(baseline,posed)
   # Rebuild shared arm/gun deltas from the native full firing pose after TF2 sleeve adaptation.
   # Mechanism channels remain the exact native local deltas, including each original joint axis.
   for n in extra+['def_c_bolt']:
    if n in raw:D[n]=raw[n]
   frames.append(delta_absolute(D))
   for n in extra:
    if n in raw:
     actual=frames[-1][n];r=restL[n];recovered=matrix(actual.translation-r.translation,r.to_quaternion().inverted()@actual.to_quaternion())
     stats['max_reactive_matrix_error']=max(stats['max_reactive_matrix_error'],max(abs(recovered[i][j]-raw[n][i][j]) for i in range(4) for j in range(4)))
     stats['native_reactive_keys']+=1
  source=use
 elif name in ('idle_anim_autoplay','idle_ads_anim_autoplay'):
  # Bake the native reactive idle into the existing autoplay entry point; no added sequence/poseparam.
  c=clip('idle_reactive_layer_3',True);body=clip('idle_1' if 'ads' in name else 'idle_0');anchorName='ads_in_0' if 'ads' in name else 'draw_0';baseline=anchors[anchorName]
  for f in range(c.end+1):
   # Retiming closes both native cycles on the same existing autoplay sequence boundary.
   raw=c.sample(f);target=original_pose(body,f*body.end/max(1,c.end),anchorName);D=relative_delta(baseline,locals_(order,parent,fit(target)))
   for n in extra:
    if n in raw:D[n]=raw[n]
   frames.append(delta_absolute(D))
  source='idle_reactive_layer_3'
 elif isdelta:
  for old in oldframes:
   D={n:old.get(n,Matrix.Identity(4)).copy() for n in order}
   for n in order:
    if parent[n] is None:D[n]=Matrix.Rotation(math.pi/2,4,'Z')@D[n]
   frames.append(delta_absolute(D))
 elif source and (BASE/(source+'.cast')).exists():
  c=clip(source)
  # Preserve stock timing, use a single shared sampling time for hands, magazine and the whole gun.
  for f in range(len(oldframes)):
   t=c.end*f/max(1,len(oldframes)-1);target=original_pose(c,t);G=fit(target)
   for hand in ('def_l_wrist','def_r_wrist'):
    before=target['def_c_base'].inverted()@target[hand];after=G['def_c_base'].inverted()@G[hand]
    stats['max_hand_gun_position_error']=max(stats['max_hand_gun_position_error'],(after.translation-before.translation).length)
   before=target['def_l_wrist'].inverted()@target['def_c_magazine'];after=G['def_l_wrist'].inverted()@G['def_c_magazine']
   stats['max_magazine_hand_position_error']=max(stats['max_magazine_hand_position_error'],(after.translation-before.translation).length)
   frames.append(locals_(order,parent,G));stats['absolute_frames']+=1
  verification.append(dict(animation=descriptor,source=source,frames=len(frames)))
 else:
  # Unmapped stock-only transitions retain the stock local motions, re-expressed on the new rest rig.
  for old in oldframes:
   G={}
   for n in order:G[n]=(G[parent[n]] if parent[n] else Matrix.Identity(4))@(old.get(n,restL[n]))
   frames.append(locals_(order,parent,G))
 sourcefile=name+'.smd';write_smd(ANIM/sourcefile,order,parent,frames)
 payload[descriptor]=dict(file=sourcefile,delta=isdelta and not noanim,noanimation=noanim,frames=len(frames),source=source)
 print('ANIMATION',descriptor,len(frames),source,flush=True)

qc=(STOCK/'view/ptpov_car101.qc').read_text(encoding='utf-8-sig')
qc=qc.replace('studio "v_car101.smd"','studio "body.smd"').replace('studio "v_car101_magazine.smd"','studio "magazine.smd"').replace('studio "v_car101_sight_on.smd"','studio "iron.smd"')
qc=re.sub(r'"models\\Weapons_R2\\car_smg\\CAR_smg[^"\n]*"',lambda m:'"models\\Weapons_R2\\prowler_zero\\scavenger"',qc)
definitions=[]
for n in order:
 t=restL[n].translation;e=[math.degrees(x) for x in restL[n].to_euler('XYZ')]
 definitions.append(f'$definebone "{n}" "{parent[n] or ""}" {t.x:.9f} {t.y:.9f} {t.z:.9f} {e[1]:.9f} {e[2]:.9f} {e[0]:.9f} 0 0 0 0 0 0')
matches=list(re.finditer(r'^\$definebone[^\n]*',qc,re.M));qc=qc[:matches[0].start()]+'\n'.join(definitions)+qc[matches[-1].end():]
last=list(re.finditer(r'^\$bonemerge[^\n]*',qc,re.M))[-1];qc=qc[:last.end()]+'\n'+'\n'.join(f'$bonemerge "{n}"' for n in extra)+qc[last.end():]
# Every restricted stock mask explicitly excludes added mechanism joints. Only fire/autoplay's
# unrestricted masks animate them. This prevents optic/sprint/noanimation layers resetting custom bones.
for name,a,b,body in reversed(blocks(qc,'weightlist')):
 replacement=body[:-1]+''.join(f'\n "{n}" 0' for n in extra)+'\n}'
 qc=qc[:a]+replacement+qc[b:]
qc=qc.replace('ptpov_car101_anims\\','anims\\')
if 'shell' in ag:
 mount=restG['def_c_base'].inverted()@ag['shell'].translation
 for name in ('shell','shell_fp'):
  qc=re.sub(r'(\$attachment "'+name+r'" "def_c_base") [-\d.]+ [-\d.]+ [-\d.]+',lambda m:m[1]+' '+' '.join(f'{v:.6f}' for v in mount),qc)
# Native source names do not change descriptor/sequence indices. Reorder compiler declarations by the
# original binary animation table; inline sequence animations must appear at their original point.
ab=blocks(qc,'animation');sb=blocks(qc,'sequence');start=min(x[1] for x in ab+sb);end=max(x[2] for x in ab+sb)
A={n:t for n,_,_,t in ab};S={n:t for n,_,_,t in sb};sequenceorder=[n for n,_,_,_ in sb]
for n in A:
 if payload[n]['delta']:
  p=A[n].index('{')+1;A[n]=A[n][:p]+'\n subtract "ref" 0'+A[n][p:]
out=[];emitted=[]
for _,n in stock['table'](184,92,4):
 if n.startswith('@'):
  target=n[1:]
  while target not in emitted:
   nxt=sequenceorder[len(emitted)];out.append(S[nxt]);emitted.append(nxt)
 else:out.append(A[n])
for n in sequenceorder[len(emitted):]:out.append(S[n])
qc=qc[:start]+'\n\n'.join(out)+qc[end:]
qc=qc.replace('$modelname "weapons/car101/ptpov_car101.mdl"','$modelname "weapons/car101/ptpov_car101.mdl"\n$maxverts 65000')
(OUT/'ptpov_car101.qc').write_text(qc,encoding='ascii',errors='replace')
(BUILD/'rig.json').write_text(json.dumps(dict(order=order,parent=parent,rest_local={n:[list(r) for r in restL[n]] for n in order},rest_global={n:[list(r) for r in restG[n]] for n in order},extra=extra,mesh_consumers=meshconsumers,optic_shift=list(opticShift),proscreen_scale=proscreenScale,proscreen_mount=list(proscreenOrigin),animations=payload),indent=2))
stats['clips']=verification
(BUILD/'source-verification.json').write_text(json.dumps(stats,indent=2))
print('VIEW_GENERATION_OK',len(order),stats['absolute_frames'],stats['max_hand_gun_position_error'],stats['max_magazine_hand_position_error'],flush=True)

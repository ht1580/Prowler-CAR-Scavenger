"""Render actual converted weapon and TF2 arm VVD/VTX geometry in decoded engine poses."""
import sys,json,math,bpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
sys.path.insert(0,str(ROOT/'src/tools'))
from mdl_mesh import read_mdl_mesh
OUT=ROOT/'renders';OUT.mkdir(exist_ok=True)
doc=json.loads((BUILD/'native-visual.json').read_text(encoding='utf-8-sig'));bs=doc['bones'];order=[b['name'] for b in bs];parent={b['name']:order[b['parent']] if b['parent']>=0 else None for b in bs};L={b['name']:matrix(b['pos'],Euler(b['rot'],'XYZ').to_quaternion()) for b in bs};bind=globals_(order,parent,L)
gun=read_mdl_mesh(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl',include={(0,0),(5,1),(6,0)})
ab=json.loads((STOCK/'arms/arms_bones.json').read_text(encoding='utf-8-sig'))['bones'];an=[b['name'] for b in ab];ap={b['name']:an[b['parent']] if b['parent']>=0 else None for b in ab};al={b['name']:matrix(b['pos'],Euler(b['rot'],'XYZ').to_quaternion()) for b in ab};ag=globals_(an,ap,al);arms=read_mdl_mesh(STOCK/'arms/pov_pilot_medium_stalker_m.mdl')
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='TEXTURE';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('World');scene.world.color=(.12,.15,.19);scene.view_settings.view_transform='Standard';scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
texture=bpy.data.materials.new('Original Scavenger basecolor');texture.use_nodes=True;tx=texture.node_tree.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(BUILD/'materials/png/scavenger_col.png'));tx.image.pack();texture.node_tree.links.new(tx.outputs['Color'],texture.node_tree.nodes['Principled BSDF'].inputs['Base Color']);texture.node_tree.nodes.active=tx
glove=bpy.data.materials.new('TF2 pilot arms');glove.diffuse_color=(.48,.54,.58,1)
def mesh_obj(name,md,material):
 faces=[f for p in md['parts'] for f in p['faces']];used=sorted({i for f in faces for i in f});ix={i:k for k,i in enumerate(used)};me=bpy.data.meshes.new(name);me.from_pydata([md['vertices'][i] for i in used],[],[tuple(ix[i] for i in f) for f in faces]);me.update();ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob);me.materials.append(material)
 if material==texture:
  uv=me.uv_layers.new(name='Original UV')
  for lo in me.loops:uv.data[lo.index].uv=md['uv'][used[lo.vertex_index]]
 for p in me.polygons:p.use_smooth=True
 return ob,used
go,gu=mesh_obj('Compiled Prowler',gun,texture);ao,au=mesh_obj('Actual TF2 arm geometry',arms,glove)
psmaterial=bpy.data.materials.new('ProScreen housing inspection');psmaterial.diffuse_color=(.15,.32,.48,1)
psmesh=read_mdl_mesh(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl',include={(4,1)})
pso,psu=mesh_obj('Actual ProScreen housing',psmesh,psmaterial)
def update(ob,used,md,names,rest,G):
 skin={n:G[n]@rest[n].inverted() for n in names}
 for vertex,i in zip(ob.data.vertices,used):vertex.co=sum((skin[names[b]]@Vector(md['vertices'][i])*w for b,w in md['weights'][i]),Vector())
 ob.data.update()
def pose(p):
 raw={order[v['index']]:matrix(v['pos'],Euler(v['rot'],'XYZ').to_quaternion()) for v in p['locals']};return globals_(order,parent,{n:raw.get(n,L[n]) for n in order})
def overlay(G,p):
 local=locals_(order,parent,G);dl={order[v['index']]:v for v in p['locals']}
 for n,v in dl.items():local[n]=matrix(local[n].translation+Vector(v['pos']),local[n].to_quaternion()@Euler(v['rot'],'XYZ').to_quaternion())
 return globals_(order,parent,local)
camera=bpy.data.objects.new('First-person camera',bpy.data.cameras.new('First-person camera'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.sensor_fit='HORIZONTAL';camera.data.angle=math.radians(100);camera.data.clip_start=.05;camera.data.clip_end=500
# Fixed original engine eye; never follow a potentially corrupt animated camera bone.
fixedEye=Matrix.Translation(Vector((0,0,-.008)))@Euler((math.pi/2,0,math.pi/2),'XYZ').to_matrix().to_4x4()@Matrix.Rotation(math.pi,4,'Y')
selections=[]
for name,label in [('@draw_seq','normal_hip'),('ads_in_anim','ads'),('@reload_seq','reload'),('@reload_empty_seq','reload_empty'),('@sprint_seq','sprint'),('@draw_onehanded_seq','onehanded')]:
 ps=sorted((p for p in doc['poses'] if p['name']==name),key=lambda p:p['frame'])
 if not ps:continue
 picks=[ps[-1]] if label in ('normal_hip','ads','onehanded') else [ps[int(len(ps)*x)] for x in (0,.25,.5,.75)]+[ps[-1]]
 for p in picks:selections.append((f'{label}_{p["frame"]:03}',pose(p)))
held=pose(max((p for p in doc['poses'] if p['name']=='@draw_seq'),key=lambda p:p['frame']))
fire=json.loads((BUILD/'native-fire.json').read_text(encoding='utf-8-sig'))
for p in fire['poses']:
 if p['name']=='attack_anim' and p['frame'] in (1,2,3,6):selections.append((f'fire_{p["frame"]:03}',overlay(held,p)))
for label,G in selections:
 # Bonemerge the same named bones exactly as the game; helper-only arm bones follow native parents.
 armG={}
 for n in an:armG[n]=G[n] if n in G else (armG[ap[n]] if ap[n] else Matrix.Identity(4))@al[n]
 update(go,gu,gun,order,bind,G);update(ao,au,arms,an,ag,armG);update(pso,psu,psmesh,order,bind,G);camera.matrix_world=fixedEye;scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
 print('POSE_RENDERED',label,flush=True)
ao.hide_render=True;pso.hide_render=True;camera.data.type='ORTHO';camera.data.ortho_scale=10;scene.render.resolution_x=1100;scene.render.resolution_y=650
for p in fire['poses']:
 if p['name']!='attack_anim' or p['frame']>12:continue
 G=overlay(held,p);T=bind['def_c_reactive_spinner_coils'].inverted()@bind['def_c_base']@G['def_c_base'].inverted();fixed={n:T@M for n,M in G.items()}
 update(go,gu,gun,order,bind,fixed);camera.location=(14,-24,7);camera.rotation_euler=(Vector()-camera.location).to_track_quat('-Z','Y').to_euler();camera.rotation_euler.rotate_axis('Z',math.pi/2);scene.render.filepath=str(OUT/f'drum_{p["frame"]:03}.png');bpy.ops.render.render(write_still=True)
# Save a useful first-person inspection state, with native animation sources kept as SMDs alongside.
ao.hide_render=False;pso.hide_render=False;G=held;armG={}
for n in an:armG[n]=G[n] if n in G else (armG[ap[n]] if ap[n] else Matrix.Identity(4))@al[n]
update(go,gu,gun,order,bind,G);update(ao,au,arms,an,ag,armG);update(pso,psu,psmesh,order,bind,G);camera.data.type='PERSP';camera.data.angle=math.radians(100);camera.matrix_world=fixedEye;scene.render.resolution_x=1280;scene.render.resolution_y=720
scene['Scope']='Actual converted MDL + actual original TF2 arms; CPU skinning and bone-name merge from decoded animation. This is offline visual validation, not a runtime capture.'
deliverOut=ROOT.parents[1]/'outputs'/('prowler-zero' if CFG['version']=='0.2.0' else 'prowler-zero-'+CFG['version']);deliverOut.mkdir(exist_ok=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(deliverOut/'Visual_Validation.blend'))
print('VISUAL_RENDER_OK',len(selections),flush=True)

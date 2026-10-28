"""Compare autoplay against a fixed stock eye. Include ProScreen mesh and embedded RUI."""
import sys,json,math,bpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
sys.path.insert(0,str(ROOT/'src/tools'));from mdl_mesh import read_mdl_mesh
sys.path.insert(0,CFG['tools_root']);import rui_editor
OUT=ROOT.parents[1]/'outputs/placement-audit';OUT.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='TEXTURE';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('World');scene.world.color=(.10,.13,.17);scene.view_settings.view_transform='Standard';scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
texture=bpy.data.materials.new('Original Scavenger');texture.use_nodes=True;tx=texture.node_tree.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(BUILD/'materials/png/scavenger_col.png'));tx.image.pack();texture.node_tree.links.new(tx.outputs['Color'],texture.node_tree.nodes['Principled BSDF'].inputs['Base Color']);texture.node_tree.nodes.active=tx
def color(name,v):
 m=bpy.data.materials.new(name);m.diffuse_color=(*v,1);return m
psmat=color('ProScreen housing',(.15,.32,.48));psrui=color('ProScreen RUI surface',(.95,.04,.65));ammorui=color('Native ammo RUI',(1.,.55,.03))
camera=bpy.data.objects.new('FIXED stock eye',bpy.data.cameras.new('FIXED stock eye'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.sensor_fit='HORIZONTAL';camera.data.clip_start=.05;camera.data.clip_end=500
stock=json.loads((BUILD/'native-stock-placement.json').read_text(encoding='utf-8-sig'))
def state(doc,p):
 order=[b['name'] for b in doc['bones']];par={b['name']:order[b['parent']] if b['parent']>=0 else None for b in doc['bones']};L={order[v['index']]:matrix(v['pos'],Euler(v['rot'],'XYZ').to_quaternion()) for v in p['locals']};return order,par,L
v=max((v for v in stock['poses'] if v['name']=='@draw_seq'),key=lambda v:v['frame']);so,sp,SL=state(stock,v);fixed=globals_(so,sp,SL)['jx_c_camera']@Matrix.Rotation(math.pi,4,'Y');camera.matrix_world=fixed
all_results={}
for label,path,viewfile,idlefile in [('before',ROOT/'released-0.2.0/ptpov_car101_conv.mdl',ROOT/'released-0.2.0/native-view.json',ROOT/'released-0.2.0/native-idle.json'),('after',BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl',BUILD/'native-view.json',BUILD/'native-idle.json')]:
 for ob in list(scene.objects):
  if ob!=camera:bpy.data.objects.remove(ob,do_unlink=True)
 doc=json.loads(viewfile.read_text(encoding='utf-8-sig'));idle=json.loads(idlefile.read_text(encoding='utf-8-sig'));o=[b['name'] for b in doc['bones']];p={b['name']:o[b['parent']] if b['parent']>=0 else None for b in doc['bones']};bind=globals_(o,p,{b['name']:matrix(b['pos'],Euler(b['rot'],'XYZ').to_quaternion()) for b in doc['bones']})
 v=max((v for v in doc['poses'] if v['name']=='@draw_seq'),key=lambda v:v['frame']);_,_,held=state(doc,v)
 additions=next(v for v in idle['poses'] if v['name']=='idle_anim_autoplay' and v['frame']==0);dl={o[v['index']]:v for v in additions['locals']}
 L={n:matrix(held[n].translation+Vector(dl.get(n,{}).get('pos',[0,0,0])),held[n].to_quaternion()@Euler(dl.get(n,{}).get('rot',[0,0,0]),'XYZ').to_quaternion()) for n in o};G=globals_(o,p,L)
 def create(name,verts,faces,material,uv=None):
  me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob);me.materials.append(material)
  if uv:
   layer=me.uv_layers.new(name='UV')
   for lo in me.loops:layer.data[lo.index].uv=uv[lo.vertex_index]
  return ob
 metrics={}
 for name,include,material in [('Weapon',{(0,0),(5,1),(6,0)},texture),('ProScreen',{(4,1)},psmat)]:
  md=read_mdl_mesh(path,include=include);skin={n:G[n]@bind[n].inverted() for n in o};faces=[f for part in md['parts'] for f in part['faces']];used=sorted({i for f in faces for i in f});idx={i:k for k,i in enumerate(used)};positions=[sum((skin[o[b]]@Vector(md['vertices'][i])*w for b,w in md['weights'][i]),Vector()) for i in used]
  create(name,positions,[tuple(idx[i] for i in f) for f in faces],material,[md['uv'][i] for i in used]);metrics[name]={'positions':positions}
 for m in rui_editor.inspect_mdl(path)['meshes']:
  if 'pro_screen' not in m['name'] and not m['name'].endswith('car_smg_rui_lower'):continue
  verts=[G[m['parentNames'][v['parent']]]@Vector(v['position']) for v in m['vertices']];create(m['name'],verts,[v['vertices'] for v in m['faces']],psrui if 'pro_screen' in m['name'] else ammorui)
 for fov in (70,90,100):
  camera.data.angle=math.radians(fov);scene.render.filepath=str(OUT/f'{label}-fixed-eye-{fov}.png');bpy.ops.render.render(write_still=True)
  from bpy_extras.object_utils import world_to_camera_view
  for name,d in metrics.items():
   q=[world_to_camera_view(scene,camera,v) for v in d['positions']];d[str(fov)]=sum(v.z>.05 and 0<v.x<1 and 0<v.y<1 for v in q)/len(q)
 all_results[label]={name:{k:v for k,v in d.items() if k!='positions'} for name,d in metrics.items()}
 print(label,json.dumps(all_results[label]),flush=True)
 if label=='after':
  T=G['def_c_base']@bind['def_c_base'].inverted();eye=T@Vector((30,50,3));target=T@Vector((0,47,4));camera.location=eye;camera.rotation_euler=(target-eye).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=24;scene.render.filepath=str(OUT/'proscreen-side-mount.png');bpy.ops.render.render(write_still=True);camera.data.type='PERSP';camera.matrix_world=fixed
(OUT/'projection-comparison.json').write_text(json.dumps(all_results,indent=2),encoding='utf-8')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Fixed_Eye_Validation.blend'))

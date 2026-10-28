"""Original-asset readers and explicit coordinate transforms for the independent rebuild."""
import json,re,struct,math,bisect,importlib.util
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion,Euler
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'))
STOCK=Path(CFG['stock_root']);SOURCE=(ROOT/'src'/CFG['original_export']).resolve()
BUILD=ROOT/'build';BUILD.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('native_cast_parser',CFG['cast_parser']);cast=importlib.util.module_from_spec(spec);spec.loader.exec_module(cast)
def walk(n):
 yield n
 for c in n.childNodes:yield from walk(c)
def first(path,typ):return next(n for r in cast.Cast.load(str(path)).Roots() for n in walk(r) if isinstance(n,typ))
def quat(v):return Quaternion((v[3],*v[:3])).normalized()
def matrix(p,q):return Matrix.Translation(Vector(p))@q.to_matrix().to_4x4()
def globals_(order,parent,local):
 G={}
 def g(n):
  if n not in G:G[n]=(g(parent[n]) if parent[n] else Matrix.Identity(4))@local[n]
  return G[n]
 for n in order:g(n)
 return G
def locals_(order,parent,G):return {n: G[parent[n]].inverted()@G[n] if parent[n] else G[n].copy() for n in order}
def lerp(a,b,t):return matrix(a.translation.lerp(b.translation,t),a.to_quaternion().slerp(b.to_quaternion(),t))
def mdldump(path):
 d=Path(path).read_bytes()
 def i(o,n=1):
  v=struct.unpack_from('<'+'i'*n,d,o);return v[0] if n==1 else v
 def text(o):return d[o:d.index(b'\0',o)].decode('ascii')
 def table(o,stride,nameoffset=0):
  n,start=i(o,2);return [(start+j*stride,text(start+j*stride+i(start+j*stride+nameoffset))) for j in range(n)]
 return dict(data=d,i=i,text=text,table=table)
def smd(path):
 lines=Path(path).read_text(encoding='utf-8-sig',errors='replace').splitlines();a=lines.index('nodes');b=lines.index('end',a);nodes={}
 for s in lines[a+1:b]:
  m=re.match(r'\s*(\d+)\s+"([^"]+)"\s+(-?\d+)',s)
  if m:nodes[int(m[1])]=(m[2],int(m[3]))
 order=[nodes[i][0] for i in sorted(nodes)];parent={n:nodes[p][0] if p>=0 else None for n,p in nodes.values()}
 a=lines.index('skeleton',b);b=lines.index('end',a);frames=[]
 for s in lines[a+1:b]:
  v=s.split()
  if not v:continue
  if v[0]=='time':frames.append({});continue
  values=list(map(float,v[1:7]));frames[-1][nodes[int(v[0])][0]]=matrix(values[:3],Euler(values[3:],'XYZ').to_quaternion())
 tris=[]
 if 'triangles' in lines[b:]:
  i=lines.index('triangles',b)+1
  while lines[i].strip()!='end':
   mat=lines[i].strip();verts=[]
   for s in lines[i+1:i+4]:
    v=s.split();cnt=int(v[9]) if len(v)>9 else 0;links=[(nodes[int(v[10+2*k])][0],float(v[11+2*k])) for k in range(cnt)] or [(nodes[int(v[0])][0],1.)]
    verts.append((Vector(map(float,v[1:4])),Vector(map(float,v[4:7])),tuple(map(float,v[7:9])),links))
   tris.append((mat,verts));i+=4
 return order,parent,frames,tris
def write_smd(path,order,parent,frames,tris=None):
 ids={n:i for i,n in enumerate(order)};path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',encoding='ascii',newline='\n') as f:
  f.write('version 1\nnodes\n')
  for n in order:f.write(f'{ids[n]} "{n}" {ids[parent[n]] if parent[n] else -1}\n')
  f.write('end\nskeleton\n')
  for frame,L in enumerate(frames):
   f.write(f'time {frame}\n')
   for n in order:
    m=L[n];values=(*m.translation,*m.to_euler('XYZ'));assert all(math.isfinite(v) for v in values)
    f.write(str(ids[n])+' '+ ' '.join(f'{v:.9f}' for v in values)+'\n')
  f.write('end\n')
  if tris is not None:
   f.write('triangles\n')
   for material,vs in tris:
    f.write(material+'\n')
    for p,n,uv,w in vs:
     assert abs(sum(v for _,v in w)-1)<.00001
     f.write(f'{ids[w[0][0]]} '+' '.join(f'{v:.9f}' for v in (*p,*n,*uv))+f' {len(w)} '+' '.join(f'{ids[b]} {v:.9f}' for b,v in w)+'\n')
   f.write('end\n')
def blocks(text,kind):
 out=[]
 for m in re.finditer(r'^\$'+kind+r' "([^"]+)"',text,re.M):
  a=text.index('{',m.end());depth=1;b=a+1
  while depth:depth+={'{':1,'}':-1}.get(text[b],0);b+=1
  out.append((m[1],m.start(),b,text[m.start():b]))
 return out

class Clip:
 def __init__(self,path):
  self.path=Path(path);self.animation=first(self.path,cast.Animation);bs=self.animation.Skeleton().Bones();self.order=[b.Name() for b in bs]
  self.parent={b.Name():self.order[b.ParentIndex()] if b.ParentIndex()>=0 else None for b in bs}
  self.rest={b.Name():matrix(b.LocalPosition(),quat(b.LocalRotation())) for b in bs}
  self.restG=globals_(self.order,self.parent,self.rest)
  self.curves={};self.end=0;self.modes=set()
  for c in self.animation.Curves():
   keys=list(c.KeyFrameBuffer());v=list(c.KeyValueBuffer());prop=c.KeyPropertyName();stride=4 if prop=='rq' else 1
   values=[quat(v[i:i+4]) for i in range(0,len(v),4)] if stride==4 else v
   self.curves.setdefault(c.NodeName(),{})[prop]=(keys,values);self.end=max(self.end,max(keys));self.modes.add(c.Mode())
  assert len(self.modes)==1,self.modes
  self.additive=self.modes=={'additive'};self.fps=self.animation.Framerate()
 def sample(self,frame):
  frame=max(0.,min(self.end,float(frame)));out={}
  for n in self.order:
   p=Vector() if self.additive else self.rest[n].translation.copy();q=Quaternion() if self.additive else self.rest[n].to_quaternion()
   for prop,(keys,values) in self.curves.get(n,{}).items():
    i=max(0,bisect.bisect_right(keys,frame)-1);j=min(i+1,len(keys)-1);t=(frame-keys[i])/(keys[j]-keys[i]) if keys[j]!=keys[i] else 0.
    if prop=='rq':q=values[i].slerp(values[j],t)
    elif prop in ('tx','ty','tz'):p['xyz'.index(prop[1])]=values[i]+(values[j]-values[i])*t
    elif prop in ('sx','sy','sz'):assert abs(values[i]-1)<.001,'Scale animation needs explicit skinning support'
   out[n]=matrix(p,q)
  return out

def model():
 path=next((SOURCE/'apex_cast/mdl').rglob('*_v_LOD0.cast'));m=first(path,cast.Model);bs=m.Skeleton().Bones();order=[b.Name() for b in bs]
 parent={b.Name():order[b.ParentIndex()] if b.ParentIndex()>=0 else None for b in bs}
 L={b.Name():matrix(b.LocalPosition(),quat(b.LocalRotation())) for b in bs}
 return m,order,parent,L,globals_(order,parent,L)

if __name__=='__main__':
 m,o,p,L,G=model();c=Clip(SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_base_v_animRig/draw_0.cast')
 for n in ('jx_c_delta','def_c_base','def_l_wrist'):
  print('MODEL',n,list(G[n].translation),list(G[n].to_quaternion()))
  print('CLIPREST',n,list(c.restG[n].translation),list(c.restG[n].to_quaternion()))
 print('SOURCE',SOURCE)

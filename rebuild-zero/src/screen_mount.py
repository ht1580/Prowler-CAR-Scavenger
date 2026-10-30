"""Small rigid receiver stand-offs for a forward external CAR ProScreen."""
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def supports(body_triangles,screen_triangles):
 vertices=[];faces=[]
 for _,triangle in body_triangles:
  if not all(all(n in ('def_c_base','weapon_bone','ja_c_propGun') for n,w in links if w>0) for p,n,uv,links in triangle):continue
  start=len(vertices);vertices.extend(p for p,n,uv,w in triangle)
  a,b,c=[v[0] for v in triangle];normal=sum((v[1] for v in triangle),Vector())
  faces.append((start,start+1,start+2) if (b-a).cross(c-a).dot(normal)>0 else (start,start+2,start+1))
 tree=BVHTree.FromPolygons(vertices,faces,all_triangles=True)
 points=[p for _,triangle in screen_triangles for p,n,uv,w in triangle];back=min(p.x for p in points);ys=[p.y for p in points];zs=[p.z for p in points]
 contacts=[]
 for j in range(1,10):
  y=min(ys)+(max(ys)-min(ys))*j/10
  for k in range(2,9):
   z=min(zs)+(max(zs)-min(zs))*k/10
   hit=tree.ray_cast(Vector((back,y,z)),Vector((-1,0,0)),2.5)
   if hit[0] is None or hit[1].x<.3:continue
   feet=[tree.ray_cast(Vector((hit[0].x+.02,y+dy,z+dz)),Vector((-1,0,0)),.22) for dy in (-.12,.12) for dz in (-.12,.12)]
   if sum(h[0] is not None and h[1].x>.3 for h in feet)<3:continue
   contacts.append((hit[3],y,z,hit[0]))
 chosen=[]
 pairs=[(a,b) for a in contacts for b in contacts if abs(a[1]-b[1])>=.7]
 selected=min(pairs,key=lambda pair:pair[0][0]+pair[1][0]) if pairs else []
 for _,y,z,point in selected:
  chosen.append(dict(contact=list(point),minimum=[point.x+.02,y-.12,z-.12],maximum=[back+.06,y+.12,z+.12]))
 assert len(chosen)==2,f'No two static receiver surfaces support the forward screen: staticFaces={len(faces)}, candidates={len(contacts)}, selected={chosen}, back={back}, y={min(ys),max(ys)}, z={min(zs),max(zs)}'
 return chosen

def box_triangles(box,bone='def_c_proscreen'):
 lo,hi=box['minimum'],box['maximum'];points=[Vector((hi[0] if i&1 else lo[0],hi[1] if i&2 else lo[1],hi[2] if i&4 else lo[2])) for i in range(8)]
 for quad in ((0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)):
  for indices in ((quad[0],quad[1],quad[2]),(quad[0],quad[2],quad[3])):
   a,b,c=[points[i] for i in indices];normal=(b-a).cross(c-a).normalized()
   yield [(p,normal,(.05,.05),[(bone,1.)]) for p in (a,c,b)]

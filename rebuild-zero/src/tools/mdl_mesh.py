import struct
from pathlib import Path

def read_mdl_mesh(path, include=None):
 d=Path(path).read_bytes()
 def ii(o,n=1):
  v=struct.unpack_from('<'+'i'*n,d,o);return v[0] if n==1 else v
 checksum=ii(8);x=-1
 while True:
  x=d.find(struct.pack('<i',7),x+1)
  if x<0:raise ValueError('VTX not found')
  if x+36<len(d) and ii(x+16)==checksum and 1<=ii(x+20)<=8:break
 v=d.find(b'IDSV');nv=ii(v+16);vs=v+ii(v+56);fixnum,fixoff=ii(v+48,2)
 logical=[]
 if fixnum:
  for k in range(fixnum):
   lod,start,count=ii(v+fixoff+12*k,3)
   if lod>=0:logical.extend(range(start,start+count))
  assert len(logical)==nv,(len(logical),nv)
 else:logical=list(range(nv))
 verts=[];links=[];uv=[]
 for k in logical:
  r=vs+48*k;weights=struct.unpack_from('<3f',d,r);ids=struct.unpack_from('<3B',d,r+12);cnt=d[r+15]
  verts.append(struct.unpack_from('<3f',d,r+16));uv.append(struct.unpack_from('<2f',d,r+40));links.append([(ids[j],weights[j]) for j in range(cnt) if weights[j]>0])
 nbp,bpo=ii(x+28,2);mdlnbp,mdlbpo=ii(236,2);assert nbp==mdlnbp
 parts=[]
 for bp in range(nbp):
  b0=x+bpo+bp*8;nm,mo=ii(b0,2)
  mb=mdlbpo+bp*16;mdlnm,_,mdlmoff=ii(mb+4,3);assert nm==mdlnm
  for mi in range(nm):
   if include is not None and (bp,mi) not in include:continue
   mm=mb+mdlmoff+148*mi;modelname=d[mm:mm+64].split(b'\0')[0].decode('utf-8','replace')
   nmeshes,meshidx,mnv,mvindex=ii(mm+72,4)
   m0=b0+mo+mi*8;nlod,loff=ii(m0,2);l0=m0+loff;nmesh,meshoff=ii(l0,2);assert nmesh==nmeshes
   faces=[];materials=[]
   for me in range(nmesh):
    mdlmesh=mm+meshidx+116*me;material,_,mesh_nv,mesh_vstart=ii(mdlmesh,4)
    me0=l0+meshoff+me*9;nsg,sgoff=ii(me0,2)
    for sg in range(nsg):
     g0=me0+sgoff+sg*25;gnv,voff,gni,ioff,ns,soff=ii(g0,6)
     orig=[struct.unpack_from('<H',d,g0+voff+k*9+4)[0] for k in range(gnv)]
     indices=struct.unpack_from('<'+'H'*gni,d,g0+ioff)
     for st in range(ns):
      s0=g0+soff+st*27;sni,sio,snv,svo,snb,sfl,nbsc,bsco=struct.unpack_from('<iiiihBii',d,s0)
      raw=list(indices[sio:sio+sni])
      if sfl&1:tris=[raw[k:k+3] for k in range(0,len(raw)-2,3)]
      elif sfl&2:tris=[(raw[k],raw[k+1],raw[k+2]) if k%2==0 else (raw[k+1],raw[k],raw[k+2]) for k in range(len(raw)-2)]
      else:raise ValueError(('strip flags',sfl))
      for tri in tris:
       ids=tuple(mvindex//48+mesh_vstart+orig[t] for t in tri)
       if len(set(ids))<3:continue
       assert min(ids)>=0 and max(ids)<nv,(ids,nv)
       faces.append(ids);materials.append(material)
   if faces:parts.append({'bodypart':bp,'model':mi,'name':modelname,'faces':faces,'materials':materials})
 return {'vertices':verts,'weights':links,'uv':uv,'parts':parts,'fixups':fixnum}

if __name__=='__main__':
 import sys
 for p in sys.argv[1:]:
  r=read_mdl_mesh(p)
  print(Path(p).name,'vertices',len(r['vertices']),'fixups',r['fixups'],'parts',[(x['name'],len(x['faces'])) for x in r['parts']])

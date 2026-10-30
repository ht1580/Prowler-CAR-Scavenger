"""Produce a reviewable index/animation/event map from the actual v53 models."""
import sys,json,struct,hashlib,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/tools'))
from mdl_lib import Mdl
cfg=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'));build=ROOT/'build'
rig=json.loads((build/'rig.json').read_text(encoding='utf-8'));report={};mapping=[]
def events(m,r):
 count,offset=m.i(r+24,2);out=[]
 for i in range(count):
  e=r+offset+80*i;cycle,number,kind=struct.unpack_from('<fii',m.d,e)
  name=m.s(e+m.i(e+76)) if kind&1024 and m.i(e+76) else str(number)
  option=m.d[e+12:e+76].split(b'\0')[0].decode('ascii')
  out.append((round(cycle,6),name,option))
 return out
for model in ('ptpov_car101','w_car101'):
 st=Mdl(Path(cfg['stock_root'])/'models/weapons/car101'/(model+'.mdl'))
 path=build/'compiler_game/models/weapons/car101'/(model+'_conv.mdl');bu=Mdl(path)
 assert st.anims()==bu.anims(),(model,'animation descriptor order')
 assert st.sequences()==bu.sequences(),(model,'sequence order/references/activities')
 assert st.bodyparts()==bu.bodyparts() and st.attachments()==bu.attachments() and st.poseparams()==bu.poseparams()
 seqs=bu.sequences();arows={n:r for r,n in bu.table(184,92,4)}
 event_count=0
 for index,((sr,sn),(br,bn),seq) in enumerate(zip(st.table(192,232,4),bu.table(192,232,4),seqs)):
  assert sn==bn and st.d[sr+12:sr+16]==bu.d[br+12:br+16]
  assert st.d[sr+32:sr+56]==bu.d[br+32:br+56]
  ev=events(bu,br);assert events(st,sr)==ev,(model,bn,'events');event_count+=len(ev)
  for ai,an in zip(seq['raw'],seq['anims']):
   assert 0<=ai<len(bu.anims())
   row=arows[an];meta=rig['animations'].get(an,{}) if model=='ptpov_car101' else {}
   mapping.append(dict(model=model,sequence_index=index,sequence=bn,activity=seq['activity'],animation_index=ai,animation=an,frames=bu.i(row+16),fps=struct.unpack_from('<f',bu.d,row+8)[0],native_source=meta.get('source') or '',resume_from=meta.get('timing',{}).get('full_sequence',''),resume_offset=meta.get('timing',{}).get('offset',''),event_count=len(ev)))
 report[model]=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),animations=len(bu.anims()),sequences=len(seqs),events=event_count,animation_order=True,sequence_order=True,animation_references=True,events_preserved=True,sequence_flags_and_bbox=True)
(build/'animation-order-validation.json').write_text(json.dumps(report,indent=2))
with (build/'animation-order-map.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=mapping[0]);w.writeheader();w.writerows(mapping)
print('ANIMATION_ORDER_OK',json.dumps(report))

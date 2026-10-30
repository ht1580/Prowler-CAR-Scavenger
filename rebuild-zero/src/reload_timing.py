"""Retarget one coherent native reload timeline to the original CAR milestones."""
import struct
from core import globals_

def stabilize_native_constants(frames,clip,parent,fit_constants):
 """Restore exact native constants lost through global/local matrix round trips.

 A few float32 ULPs below an exact Vector48 value can make the compiler truncate
 a full clip and its resume slice into different half-float bins. Only restore
 channels proven constant in the original clip, with the same parent and with
 every retargeted sample already within 0.0001 of that native value.
 """
 native=clip.sample_pose(0);changed=0
 for n in native:
  if n not in frames[0] or parent[n]!=clip.parent[n]:continue
  for axis,prop in enumerate(('tx','ty','tz')):
   curve=clip.curves.get(n,{}).get(prop)
   if curve and any(abs(v-curve[1][0])>1e-8 for v in curve[1]):continue
   value=native[n].translation[axis]
   if any(abs(fr[n].translation[axis]-value)>1e-4 for fr in frames):continue
   for fr in frames:fr[n][axis][3]=value
   changed+=1
 # ArmFit deliberately substitutes the TF2 torso/clavicle baseline for the
 # Apex one. Use that authoritative baseline for these channels. Real torso
 # reach corrections are >=0.1 units and fail this constant-channel guard.
 for n,baseline in fit_constants.items():
  for axis,value in enumerate(baseline.translation):
   if any(abs(fr[n].translation[axis]-value)>1e-4 for fr in frames):continue
   for fr in frames:fr[n][axis][3]=value
   changed+=1
 return changed

class ReloadTiming:
 def __init__(self,stock):
  self.stock=stock
  self.sequences={s['name']:s for s in stock.sequences()}
  self.rows={n:r for r,n in stock.table(192,232,4)}
  self.animrows={n:r for r,n in stock.table(184,92,4)}

 def sequence_for(self,descriptor):
  return next(n for n,s in self.sequences.items() if s['anims']==[descriptor])

 def frames(self,name):
  descriptor=self.sequences[name]['anims'][0]
  return self.stock.i(self.animrows[descriptor]+16)

 def events(self,name):
  row=self.rows[name];count,offset=self.stock.i(row+24,2);out=[]
  for i in range(count):
   e=row+offset+80*i;cycle,number,kind=struct.unpack_from('<fii',self.stock.d,e)
   event=self.stock.s(e+self.stock.i(e+76)) if kind&1024 and self.stock.i(e+76) else str(number)
   out.append((event,round(cycle*(self.frames(name)-1))))
  return out # Lists retain repeated FILLAMMO and sound events.

 def event_frame(self,name,event):
  return next(f for n,f in self.events(name) if n==event)

 def full_sequence(self,name):return name.replace('_late1','').replace('_late2','')

 def resume_offset(self,name):
  full=self.full_sequence(name)
  return self.event_frame(full,'AE_WPN_READYTOFIRE')-self.event_frame(name,'AE_WPN_READYTOFIRE')

 def full_times(self,name,clip):
  cue_clip=clip
  positions=[]
  for t in range(cue_clip.end+1):
   G=globals_(cue_clip.order,cue_clip.parent,cue_clip.sample_pose(t))
   positions.append((G['def_c_base'].inverted()@G['def_c_magazine']).translation)
  moving=[i for i,p in enumerate(positions) if (p-positions[0]).length>.25]
  if not moving:
   # Native one-handed reload hides/dips the gun and has no moving magazine
   # track. Its empty clip also has a different duration than two-handed empty.
   # Keep its own timing; only resume it through slices of that same timeline.
   assert 'onehanded' in name,(name,'native magazine cue could not be measured')
   end=self.frames(name)-1
   return [clip.end*f/max(1,end) for f in range(end+1)],dict(anchors=[(0,0),(end,clip.end)],mode='native-onehanded-no-magazine-channel')
  pull,seat=moving[0],moving[-1]+1
  assert 0<pull<seat<clip.end,(name,pull,seat,clip.end)
  dst_pull=self.event_frame(name,'AE_WPN_RELOAD_MILESTONE_1')-3
  # Empty reload inserts the magazine at milestone 2. FILLAMMO occurs later,
  # when the charging/bolt operation completes, and is not the insertion cue.
  insert='AE_WPN_RELOAD_MILESTONE_2' if any(n=='AE_WPN_RELOAD_MILESTONE_2' for n,f in self.events(name)) else 'AE_WPN_FILLAMMO'
  dst_seat=self.event_frame(name,insert)-6
  end=self.frames(name)-1
  assert 0<dst_pull<dst_seat<end,(name,dst_pull,dst_seat,end)
  anchors=[(0,0),(dst_pull,pull),(dst_seat,seat),(end,clip.end)]
  times=[]
  for f in range(end+1):
   for (d0,s0),(d1,s1) in zip(anchors,anchors[1:]):
    if d0<=f<=d1:
     times.append(s0+(s1-s0)*(f-d0)/(d1-d0));break
  assert len(times)==end+1 and all(a<=b for a,b in zip(times,times[1:]))
  return times,dict(anchors=anchors,insertion_event=insert,native_cue_clip=cue_clip.path.stem)

"""Check animation contents against CAR milestones and resume-segment continuity."""
import json,sys,unittest,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
sys.path.insert(0,str(ROOT/'src/tools'));from mdl_lib import Mdl
stock=Mdl(STOCK/'models/weapons/car101/ptpov_car101.mdl')
seqs={s['name']:s for s in stock.sequences()}
rows=dict((n,r) for r,n in stock.table(192,232,4))
def events(name):
 row=rows[name];count,offset=stock.i(row+24,2);frames=read_sequence(name)[2];result=[]
 for i in range(count):
  e=row+offset+80*i;cycle,number,kind=struct.unpack_from('<fii',stock.d,e)
  event=stock.s(e+stock.i(e+76)) if kind&1024 and stock.i(e+76) else str(number)
  result.append((event,round(cycle*(len(frames)-1))))
 return result
def read_sequence(name):
 descriptor=seqs[name]['anims'][0].removeprefix('@')
 return smd(BUILD/'view/anims'/(descriptor+'.smd'))
def event_frame(name,event):return next(f for n,f in events(name) if n==event)

class ReloadTiming(unittest.TestCase):
 def test_binary_sequence_and_animation_reference_order(self):
  built=Mdl(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl')
  from motion_contract import validate as validate_motion_contract
  self.assertTrue(validate_motion_contract(stock,built))

 def test_magazine_milestones_match_normal_and_empty_reload_phases(self):
  for name in ('reload_seq','reload_crouch_seq','reload_empty_seq','reload_empty_crouch_seq'):
   o,p,frames,_=read_sequence(name);positions=[]
   for frame in frames:
    G=globals_(o,p,frame);positions.append((G['def_c_base'].inverted()@G['def_c_magazine']).translation)
   moving=[i for i,v in enumerate(positions) if (v-positions[0]).length>.25]
   pull=event_frame(name,'AE_WPN_RELOAD_MILESTONE_1')-3
   insert_event='AE_WPN_RELOAD_MILESTONE_2' if 'empty' in name else 'AE_WPN_FILLAMMO'
   seat=event_frame(name,insert_event)-6
   with self.subTest(sequence=name):
    self.assertTrue(moving)
    self.assertLessEqual(abs(moving[0]-pull),1,'magazine departs before the CAR pull/milestone cue')
    self.assertLessEqual(abs(moving[-1]+1-seat),1,'magazine insertion must use the insert milestone, not the empty-reload bolt-fill event')

 def test_resume_segments_are_continuous_slices_of_the_full_reload(self):
  for name in seqs:
   if not name.startswith('reload') or '_late' not in name:continue
   full=name.replace('_late1','').replace('_late2','')
   start=event_frame(full,'AE_WPN_READYTOFIRE')-event_frame(name,'AE_WPN_READYTOFIRE')
   o,p,frames,_=read_sequence(name);fo,fp,fullframes,_=read_sequence(full)
   self.assertEqual(o,fo);self.assertEqual(p,fp)
   error=0.
   for i,frame in enumerate(frames):
    expected=fullframes[min(start+i,len(fullframes)-1)]
    error=max(error,max(abs(frame[n][r][c]-expected[n][r][c]) for n in o for r in range(4) for c in range(4)))
   with self.subTest(sequence=name):
    self.assertLess(error,.00001,'late reload restarts a different native clip instead of resuming the current hand/gun/magazine timeline')

if __name__=='__main__':
 r=unittest.main(argv=['test_reload_timing'],exit=False)
 if not r.result.wasSuccessful():raise RuntimeError('RELOAD_TIMING_FAILED')

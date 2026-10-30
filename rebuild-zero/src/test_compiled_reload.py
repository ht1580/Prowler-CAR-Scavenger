"""Verify actual v53 reload samples, including compressed resume-segment seams."""
import json,sys,hashlib,math,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
from test_reload_timing import seqs,event_frame
posefile=Path(sys.argv[sys.argv.index('--poses')+1]) if '--poses' in sys.argv else BUILD/'native-reload.json'
doc=json.loads(posefile.read_text(encoding='utf-8-sig'))
model=BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl'
assert doc['source_sha256']==hashlib.sha256(model.read_bytes()).hexdigest(),'reload pose document belongs to a different model'
order=[b['name'] for b in doc['bones']]
parent={b['name']:order[b['parent']] if b['parent']>=0 else None for b in doc['bones']}
poses={}
for p in doc['poses']:
 poses.setdefault(p['name'],{})[p['frame']]={order[v['index']]:matrix(v['pos'],Euler(v['rot'],'XYZ').to_quaternion()) for v in p['locals']}
metrics=dict(model_sha256=doc['source_sha256'],frames=len(doc['poses']),max_resume_position_error=0.,max_resume_angle_error=0.,magazine_phases={})
def frames(name):return poses[seqs[name]['anims'][0]]

class CompiledReload(unittest.TestCase):
 def test_full_reload_magazine_phases_match_car_events(self):
  for name in ('reload_seq','reload_crouch_seq','reload_empty_seq','reload_empty_crouch_seq'):
   points=[];ff=frames(name)
   self.assertEqual(sorted(ff),list(range(len(ff))))
   for i in range(len(ff)):
    G=globals_(order,parent,ff[i]);points.append((G['def_c_base'].inverted()@G['def_c_magazine']).translation)
   moving=[i for i,p in enumerate(points) if (p-points[0]).length>.25]
   wanted_pull=event_frame(name,'AE_WPN_RELOAD_MILESTONE_1')-3
   wanted_seat=event_frame(name,'AE_WPN_RELOAD_MILESTONE_2' if 'empty' in name else 'AE_WPN_FILLAMMO')-6
   metrics['magazine_phases'][name]=dict(pull=moving[0],seat=moving[-1]+1)
   with self.subTest(sequence=name):
    self.assertLessEqual(abs(moving[0]-wanted_pull),1)
    self.assertLessEqual(abs(moving[-1]+1-wanted_seat),1)

 def test_late_reloads_resume_the_same_compiled_hand_gun_and_magazine_motion(self):
  for name in seqs:
   if not name.startswith('reload') or '_late' not in name:continue
   full=name.replace('_late1','').replace('_late2','')
   start=event_frame(full,'AE_WPN_READYTOFIRE')-event_frame(name,'AE_WPN_READYTOFIRE')
   actual,expected=frames(name),frames(full)
   self.assertEqual(sorted(actual),list(range(len(actual))))
   pe=ae=0.
   for i,A in actual.items():
    B=expected[start+i]
    for n in order:
     pe=max(pe,(A[n].translation-B[n].translation).length)
     ae=max(ae,math.degrees(A[n].to_quaternion().rotation_difference(B[n].to_quaternion()).angle))
   metrics['max_resume_position_error']=max(metrics['max_resume_position_error'],pe)
   metrics['max_resume_angle_error']=max(metrics['max_resume_angle_error'],ae)
   with self.subTest(sequence=name):
    self.assertLess(pe,.025)
    self.assertLess(ae,.15)

if __name__=='__main__':
 r=unittest.main(argv=['test_compiled_reload'],exit=False)
 if not r.result.wasSuccessful():raise RuntimeError('COMPILED_RELOAD_FAILED')
 (BUILD/'compiled-reload-validation.json').write_text(json.dumps(metrics,indent=2))
 print('COMPILED_RELOAD_TIMING_OK',json.dumps(metrics))

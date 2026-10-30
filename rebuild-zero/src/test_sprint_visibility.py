"""Reject native variants which place the held gun behind the fixed original engine eye."""
import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *

class SprintVisibility(unittest.TestCase):
 def test_regular_sprint_keeps_weapon_in_front_of_fixed_engine_eye(self):
  doc=json.loads((BUILD/'native-all.json').read_text(encoding='utf-8-sig'))
  order=[b['name'] for b in doc['bones']]
  parent={b['name']:order[b['parent']] if b['parent']>=0 else None for b in doc['bones']}
  poses=[p for p in doc['poses'] if p['name']=='@sprint_seq']
  self.assertGreaterEqual(len(poses),3)
  # Stock v53 view eye is at the origin, looking along +X (Rx90,Rz90).
  for p in poses:
   local={order[v['index']]:matrix(v['pos'],Euler(v['rot'],'XYZ').to_quaternion()) for v in p['locals']}
   gun=globals_(order,parent,local)['def_c_base'].translation
   with self.subTest(frame=p['frame']):
    self.assertGreater(gun.x,1.0,f'sprint gun origin behind original eye: {list(gun)}')

if __name__=='__main__':
 result=unittest.main(argv=['test_sprint_visibility'],exit=False)
 if not result.result.wasSuccessful():raise RuntimeError('SPRINT_VISIBILITY_FAILED')

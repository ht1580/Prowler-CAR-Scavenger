"""Stop events cannot restart a firing loop; a low-ammo cue must not be a 3p report."""
import json,unittest,wave,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class AudioPolicy(unittest.TestCase):
 def test_all_end_events_are_in_tail_group(self):
  audio=ROOT/'build/stage/Prowler.CAR.Scavenger/audio'
  for path in audio.glob('*.json'):
   for event in json.loads(path.read_text())['EventId']:
    if 'end' in event.lower():self.assertEqual(path.stem,'tail',f'{event}: stop event incorrectly restarts the full firing loop')

 def test_low_ammo_uses_the_original_warning(self):
  audio=ROOT/'build/stage/Prowler.CAR.Scavenger/audio'
  for path in audio.glob('*.json'):
   self.assertNotIn('car_lowammo_shot1',json.loads(path.read_text())['EventId'],'3p low-ammo gun report was substituted for a warning cue')

if __name__=='__main__':unittest.main()

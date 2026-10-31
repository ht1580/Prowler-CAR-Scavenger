"""Stop events cannot restart a firing loop; a low-ammo cue must not be a 3p report."""
import json,unittest,wave,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class AudioPolicy(unittest.TestCase):
 def test_reload_mechanical_events_have_audible_replacement_samples(self):
  audio=ROOT/'build/stage/Prowler.CAR.Scavenger/audio';events={}
  for path in audio.glob('*.json'):
   for name in json.loads(path.read_text())['EventId']:events[name]=audio/path.stem/'1.wav'
  for event in ('weapon_car_reload_maggrab','weapon_car_reload_magpull','weapon_car_reload_maginsert','weapon_car_reload_maghandrest','weapon_car_emptyreload_maggrab','weapon_car_emptyreload_magpull','weapon_car_emptyreload_maginsert','weapon_car_emptyreload_handrest','weapon_car_emptyreload_boltback','weapon_car_emptyreload_boltfront'):
   self.assertIn(event,events,'reload action has no explicit mechanical feedback')
   with wave.open(str(events[event])) as w:
    data=struct.unpack('<'+'h'*(w.getnframes()*w.getnchannels()),w.readframes(w.getnframes()))
   self.assertGreater(max(map(abs,data))/32768,.2,event)

 def test_first_person_shots_are_not_limited_to_twenty_percent(self):
  for name in ('first','loop1p'):
   with wave.open(str(ROOT/'build/stage/Prowler.CAR.Scavenger/audio'/name/'1.wav')) as w:
    data=struct.unpack('<'+'h'*(w.getnframes()*w.getnchannels()),w.readframes(w.getnframes()))
   peak=max(map(abs,data))/32768
   self.assertGreaterEqual(peak,.45,name)
   self.assertLess(peak,.8,'sample clips or leaves too little mixing headroom')

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

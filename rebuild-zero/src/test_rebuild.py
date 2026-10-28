"""Source-derived acceptance gates. Run in Blender for native matrix precision."""
import unittest,json,math,sys,struct,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class RebuildArtifact(unittest.TestCase):
 def test_source_motion_and_grip_have_a_verified_rebuild(self):
  path=ROOT/'build/source-verification.json'
  self.assertTrue(path.exists(),'From-zero generator has not produced source animation checks')
  if not path.exists():return
  d=json.loads(path.read_text(encoding='utf-8'))
  self.assertEqual(d['source_kind'],'native Apex CAST')
  self.assertGreater(d['absolute_frames'],1000)
  self.assertLess(d['max_hand_gun_position_error'],.002)
  self.assertLess(d['max_magazine_hand_position_error'],.002)
  self.assertGreater(d['native_reactive_keys'],100)
  self.assertLess(d['max_reactive_matrix_error'],.0001)
  self.assertEqual(d['unused_added_bones'],[])
  self.assertFalse(d['independent_offscreen_push'])

 def test_original_compiled_table_and_source_sampling_are_preserved(self):
  path=ROOT/'build/compiled-verification.json'
  self.assertTrue(path.exists(),'Converted MDL has not been validated against native source motion')
  if not path.exists():return
  d=json.loads(path.read_text(encoding='utf-8'))
  for k in ('stock_sequences','stock_anim_order','stock_attachment_names','native_spin_samples','inverse_bind','vtx_weights'):
   self.assertTrue(d[k],k)

 def test_both_compiled_models_preserve_events_and_attachment_roles(self):
  sys.path.insert(0,str(ROOT/'src/tools'))
  from mdl_lib import Mdl
  cfg=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'))
  for name in ('ptpov_car101','w_car101'):
   stock=Mdl(Path(cfg['stock_root'])/'models/weapons/car101'/(name+'.mdl'));built=Mdl(ROOT/'build/compiler_game/models/weapons/car101'/(name+'_conv.mdl'))
   with self.subTest(model=name):
    self.assertEqual(stock.bones(),built.bones()[:len(stock.bones())])
    self.assertEqual(stock.attachments(),built.attachments())
    self.assertEqual(stock.sequences(),built.sequences())
    self.assertEqual(stock.poseparams(),built.poseparams())
    self.assertEqual(built.i(80),len(built.d))
    def events(m,r):
     count,offset=m.i(r+24,2);out=[]
     for k in range(count):
      e=r+offset+80*k;cycle,event,kind=struct.unpack_from('<fii',m.d,e);option=m.d[e+12:e+76].split(b'\0')[0].decode();name=m.s(e+m.i(e+76)) if kind&1024 and m.i(e+76) else str(event);out.append((round(cycle,5),name,option))
     return out
    for (sr,sn),(br,bn) in zip(stock.table(192,232,4),built.table(192,232,4)):
     self.assertEqual(sn,bn);self.assertEqual(events(stock,sr),events(built,br),sn)

 def test_audio_has_exact_unique_bank_events_and_clean_pcm(self):
  cfg=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'));bank=Path(cfg['stock_root']).parent/'audio_raw/events/tf2_all_audio_events.txt';known={s.split(',',1)[1].strip() for s in bank.read_text().splitlines() if ',' in s};seen=[]
  audio=ROOT/'build/stage/Prowler.CAR.Scavenger/audio'
  for p in audio.glob('*.json'):
   d=json.loads(p.read_text());seen+=d['EventId'];self.assertTrue(set(d['EventId'])<=known)
   with wave.open(str(audio/p.stem/'1.wav')) as w:self.assertEqual((w.getnchannels(),w.getsampwidth(),w.getframerate()),(2,2,48000));self.assertGreater(w.getnframes(),1000)
  self.assertEqual(len(seen),len(set(seen)));self.assertGreater(len(seen),50)

 def test_no_runtime_diagnostic_script_is_packaged(self):
  stage=ROOT/'build/stage/Prowler.CAR.Scavenger';manifest=json.loads((stage/'mod.json').read_text())
  self.assertNotIn('Scripts',manifest)
  self.assertEqual([],list(stage.rglob('*.nut')))
  self.assertEqual([],list(stage.rglob('*.cfg')))

 def test_world_root_matches_original_animation(self):
  path=ROOT/'build/world-validation.json'
  self.assertTrue(path.exists())
  if path.exists():
   d=json.loads(path.read_text());self.assertEqual(d['poses'],12);self.assertLess(d['root_max_error'],.0001)

 def test_native_firing_and_idle_hand_gun_relationships(self):
  path=ROOT/'build/native-firing-grip.json';self.assertTrue(path.exists())
  if path.exists():
   d=json.loads(path.read_text());self.assertEqual(d['firing_keys'],328);self.assertGreaterEqual(d['idle_keys'],1444);self.assertLess(d['max_position_error'],.025);self.assertLess(d['max_angle_error'],.15)

 def test_world_optic_face_winding_matches_original(self):
  sys.path.insert(0,str(ROOT/'src/tools'));from mdl_mesh import read_mdl_mesh
  cfg=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'))
  def signs(path):
   data=Path(path).read_bytes();mesh=read_mdl_mesh(path);v=data.index(b'IDSV');count=struct.unpack_from('<i',data,v+16)[0];fixnum,fixoff=struct.unpack_from('<ii',data,v+48);vertex=v+struct.unpack_from('<i',data,v+56)[0];logical=[]
   for k in range(fixnum):
    lod,start,length=struct.unpack_from('<iii',data,v+fixoff+12*k)
    if lod>=0:logical.extend(range(start,start+length))
   if not fixnum:logical=list(range(count))
   normals=[struct.unpack_from('<3f',data,vertex+48*k+28) for k in logical];out={}
   for part in mesh['parts']:
    positive=negative=0
    for face in part['faces']:
     a,b,c=[mesh['vertices'][i] for i in face];u=[b[i]-a[i] for i in range(3)];w=[c[i]-a[i] for i in range(3)];cross=(u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]);dot=sum(cross[i]*sum(normals[k][i] for k in face) for i in range(3))
     positive+=dot>1e-7;negative+=dot< -1e-7
    out[(part['bodypart'],part['model'])]=positive>negative
   return out
  original=signs(Path(cfg['stock_root'])/'models/weapons/car101/w_car101.mdl');built=signs(ROOT/'build/compiler_game/models/weapons/car101/w_car101_conv.mdl')
  self.assertEqual(original,built,'VTX triangles must be reversed when re-authored as SMD, otherwise world optics turn inside out')

if __name__=='__main__':unittest.main()

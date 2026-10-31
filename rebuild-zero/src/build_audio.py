"""Fresh original WAV decoding, cadence conversion and bank-derived override definitions."""
import json,math,wave,subprocess,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];CFG=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'));SOURCE=Path(CFG['audio_source']);OUT=ROOT/'build/stage/Prowler.CAR.Scavenger/audio';OUT.mkdir(parents=True,exist_ok=True)
SR=48000;RATE=14.1;SHOTS=56
source_assets={}
def load(stem):
 path=next(SOURCE.rglob(stem+'.wav'));source_assets[stem]=hashlib.sha256(path.read_bytes()).hexdigest();r=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ac','2','-ar',str(SR),'-'],capture_output=True,check=True)
 return np.frombuffer(r.stdout,dtype='<f4').reshape(-1,2).copy()
def cadence(a):
 # Envelope downsampling + FFT correlation avoids the old O(N^2) full-rate analysis.
 env=np.abs(a).mean(axis=1);length=len(env)//48;env=env[:length*48].reshape(-1,48).mean(axis=1);env-=env.mean();n=1<<(2*len(env)-1).bit_length();ft=np.fft.rfft(env,n);ac=np.fft.irfft(ft*ft.conj(),n)
 return (60+int(np.argmax(ac[60:111])))/1000
def repeat(a,period):
 duration=int(round(SHOTS*SR/RATE));out=np.zeros((duration,2),np.float32);windowLength=int(round((period+.012)*SR));fade=int(.006*SR);window=np.ones(windowLength,np.float32);window[:fade]=np.linspace(0,1,fade);window[-fade:]=np.linspace(1,0,fade)
 envelope=np.abs(a[:int(period*SR)]).mean(axis=1);onset=max(0,int(np.argmax(np.diff(envelope)))-int(.003*SR));available=max(1,int((len(a)-windowLength-onset)/(period*SR))-1)
 for shot in range(SHOTS):
  start=onset+int(round((1+shot%available)*period*SR));piece=a[start:start+windowLength]*window[:,None];indices=(int(round(shot*SR/RATE))+np.arange(len(piece)))%duration;np.add.at(out,indices,piece)
 return out
close=load('Wpn_ProwlerPDW_3p_WpnFire_Loop_Close_2ch_v1_01');centre=load('Wpn_ProwlerPDW_1p_WpnFire_Loop_Close_C_v1_01');mechanical=load('Wpn_ProwlerPDW_1p_WpnFire_Loop_Mech_2ch_v1_01');mid=load('Wpn_ProwlerPDW_3p_WpnFire_Loop_Mid_2ch_v1_01')
periods={name:cadence(a) for name,a in [('close',close),('centre',centre),('mechanical',mechanical),('mid',mid)]}
tail=load('Wpn_ProwlerPDW_3p_WpnFire_Tail_Mid_2ch_v1_01');tail[-int(.2*SR):]*=np.linspace(1,0,int(.2*SR))[:,None]
sounds={'first':load('Wpn_ProwlerPDW_1p_WpnFire_FirstShot_Close_2ch_v1_01'),'loop1p':repeat(close,periods['close'])+.4*repeat(centre,periods['centre'])+.2*repeat(mechanical,periods['mechanical']),'loop3p':repeat(close,periods['close']),'loopnpc':repeat(mid,periods['mid']),'tail':tail,'silent':np.zeros((int(.05*SR),2),np.float32)}
# Use the existing CAR animation sound events, so interrupts and late reloads
# retain engine timing. These are original mechanical/foley samples, not a
# second timer-driven reload soundtrack layered on top of the engine.
reload_sources={
 'reload_grab':('weapon_car_reload_maggrab','Wpn_ProwlerPDW_1p_reload_foley_ArmToMag_2frames_1'),
 'reload_magout':('weapon_car_reload_magpull','Wpn_ProwlerPDW_1p_reload_mech_reload_MagOut_16frames_1'),
 'reload_magin':('weapon_car_reload_maginsert','Wpn_ProwlerPDW_1p_reload_mech_reload_MagIn_43frames_1'),
 'reload_settle':('weapon_car_reload_maghandrest','Wpn_ProwlerPDW_1p_reload_mech_reload_grab_66frames_1'),
 'empty_grab':('weapon_car_emptyreload_maggrab','Wpn_ProwlerPDW_1p_reload_empty_foley_ArmMagGrab_2frames_1'),
 'empty_magout':('weapon_car_emptyreload_magpull','Wpn_ProwlerPDW_1p_reload_mech_empty_MagOut_13frames_1'),
 'empty_magin':('weapon_car_emptyreload_maginsert','Wpn_ProwlerPDW_1p_reload_mech_empty_MagIn_45frames_1a'),
 'empty_settle':('weapon_car_emptyreload_handrest','Wpn_ProwlerPDW_1p_reload_mech_empty_grab_88frames_1'),
 'empty_boltback':('weapon_car_emptyreload_boltback','Wpn_ProwlerPDW_1p_reload_mech_empty_bolt_pull_68frames_1'),
 'empty_boltfront':('weapon_car_emptyreload_boltfront','Wpn_ProwlerPDW_1p_reload_mech_empty_bolt_release_76frames_1'),
}
bank=Path(CFG['stock_root']).parent/'audio_raw/events/tf2_all_audio_events.txt';events={line.split(',',1)[1].strip() for line in bank.read_text().splitlines() if ',' in line};groups={}
for event in sorted(events):
 e=event.lower();kind=None
 if e.startswith('weapon_car_secondshot'):kind='silent'
 elif e.startswith('weapon_car_firstshot_1p'):kind='first'
 elif e.startswith('weapon_car_firstshot'):kind='silent'
 # Check every stop variant before the broad loop prefix. SuppressedEnd used
 # to receive the entire four-second firing loop again after trigger release.
 elif e.startswith('weapon_car_loop') and 'end' in e:kind='tail'
 elif e.startswith('weapon_car_loop'):
  kind='loop1p' if '_1p' in e else ('loopnpc' if 'npc' in e else 'loop3p')
 # Keep the original low-ammo warning. A 3p low-ammo gun report is a loud
 # two-second shot/tail, not the small first-person warning cue.
 if kind:groups.setdefault(kind,[]).append(event)
for kind,(event,stem) in reload_sources.items():
 assert event in events,event
 groups[kind]=[event];sounds[kind]=load(stem)
targets={'first':.65,'loop1p':.55,'loop3p':.20,'loopnpc':.20,'tail':.20,'silent':0.,'reload_grab':.30,'reload_magout':.45,'reload_magin':.50,'reload_settle':.32,'empty_grab':.30,'empty_magout':.45,'empty_magin':.50,'empty_settle':.32,'empty_boltback':.45,'empty_boltfront':.45}
report={'periods_seconds':periods,'rate':RATE,'original_low_ammo_warning':True,'stop_events_use_tail':True,'reload_events_follow_animation':True,'source_assets':source_assets,'overrides':{}}
# Remove only the obsolete generated warning override, including from reused
# staging directories. Existing installed mods and other task files are untouched.
for path in (OUT/'lowammo.json',OUT/'lowammo/1.wav'):
 assert path.resolve().is_relative_to(OUT.resolve())
 if path.exists():path.unlink()
if (OUT/'lowammo').exists():(OUT/'lowammo').rmdir()
for kind,ids in groups.items():
 a=sounds[kind].copy()
 # Bound overlap headroom and prevent discontinuities at file start/end. The
 # override loader can instantiate several sample voices for the same event.
 fade=min(int(.003*SR),len(a)//2)
 if fade:a[:fade]*=np.linspace(0,1,fade)[:,None];a[-fade:]*=np.linspace(1,0,fade)[:,None]
 peak=float(np.max(np.abs(a)));gain=targets[kind]/peak if peak>1e-9 else 1.;a*=gain
 assert np.max(np.abs(a))<.8
 pcm=np.rint(a*32767).astype('<i2');folder=OUT/kind;folder.mkdir(exist_ok=True)
 with wave.open(str(folder/'1.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
 (OUT/(kind+'.json')).write_text(json.dumps(dict(EventId=ids,AudioSelectionStrategy='sequential'),indent=2),encoding='utf-8')
 report['overrides'][kind]=dict(events=ids,seconds=len(a)/SR,peak=float(np.abs(a).max()),rms=float(np.sqrt(np.mean(a*a))),gain=gain,source=reload_sources[kind][1] if kind in reload_sources else None)
(ROOT/'build/audio-report.json').write_text(json.dumps(report,indent=2));print('AUDIO_BUILD_OK',periods,len(events),sum(len(v) for v in groups.values()),flush=True)

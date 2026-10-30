"""Fresh original WAV decoding, cadence conversion and bank-derived override definitions."""
import json,math,wave,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];CFG=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'));SOURCE=Path(CFG['audio_source']);OUT=ROOT/'build/stage/Prowler.CAR.Scavenger/audio';OUT.mkdir(parents=True,exist_ok=True)
SR=48000;RATE=14.1;SHOTS=56
def load(stem):
 path=next(SOURCE.rglob(stem+'.wav'));r=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ac','2','-ar',str(SR),'-'],capture_output=True,check=True)
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
report={'periods_seconds':periods,'rate':RATE,'original_low_ammo_warning':True,'stop_events_use_tail':True,'overrides':{}}
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
 peak=float(np.max(np.abs(a)));a=a*min(1.,.20/max(peak,1e-9));pcm=np.rint(a*32767).astype('<i2');folder=OUT/kind;folder.mkdir(exist_ok=True)
 with wave.open(str(folder/'1.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
 (OUT/(kind+'.json')).write_text(json.dumps(dict(EventId=ids,AudioSelectionStrategy='sequential'),indent=2),encoding='utf-8')
 report['overrides'][kind]=dict(events=ids,seconds=len(a)/SR,peak=float(np.abs(a).max()),rms=float(np.sqrt(np.mean(a*a))))
(ROOT/'build/audio-report.json').write_text(json.dumps(report,indent=2));print('AUDIO_BUILD_OK',periods,len(events),sum(len(v) for v in groups.values()),flush=True)

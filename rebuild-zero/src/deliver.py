"""Package current source and real-game evidence, keyed to the tested ZIP hash."""
import json,hashlib,csv,zipfile,collections,shutil,sys,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];TASK=ROOT.parents[1];BUILD=ROOT/'build'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg=read(ROOT/'src/config.json');version=cfg['version'];OUT=TASK/'outputs'/('prowler-zero-'+version);OUT.mkdir(exist_ok=True)
package=read(OUT/'package-verification.json');runtime=read(OUT/'runtime-verification.json')
assert runtime['zip_sha256']==package['sha256']==sha(OUT/f'Prowler.CAR.Scavenger-{version}.zip')
package.update(game_tested=runtime['game_tested'],full_visual_acceptance=False,runtime_report='runtime-verification.json')
(OUT/'package-verification.json').write_text(json.dumps(package,indent=2),encoding='utf-8')
rig=read(BUILD/'rig.json');inv=read(ROOT/'inventory.json')
sys.path.insert(0,str(ROOT/'src/tools'));from mdl_mesh import read_mdl_mesh
mesh=read_mdl_mesh(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl');links=collections.Counter()
for weights in mesh['weights']:
 for b,w in weights:
  if w>0:links[rig['order'][b]]+=1
rows=[]
for i,n in enumerate(rig['order']):
 added=n in rig['extra'];rows.append(dict(index=i,name=n,parent=rig['parent'][n] or '',added=added,vertex_influences=links[n],reason=('native weighted mechanism or parent dependency' if added else 'original CAR compatibility contract')))
assert all(r['vertex_influences'] for r in rows if r['added'])
with (OUT/'bone-audit.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
for name in ('source-verification.json','compiled-verification.json','native-firing-grip.json','world-validation.json'):
 shutil.copy2(BUILD/name,OUT/name)
for name in ('animation-order-validation.json','animation-order-map.csv','compiled-reload-validation.json','compiled-dynamic-validation.json','right-forearm-validation.json','attack-blending-validation.json','compiled-attack-blending-validation.json','compiled-visual-motion-validation.json'):
 shutil.copy2(BUILD/name,OUT/name)
for name in ('rui-layout-validation.json','audio-report.json','proscreen-data.json'):
 if (BUILD/name).exists():shutil.copy2(BUILD/name,OUT/name)
shutil.copy2(BUILD/'prowler_car101.rui',OUT/'prowler_car101.rui')
shutil.copy2(ROOT/'src/assets/prowler_ammo_panel.json',OUT/'prowler_ammo_panel.json')
shutil.copy2(ROOT/'README.md',OUT/'BUILD_README.md')
shutil.copy2(ROOT/'reference-structure/structure-comparison.json',OUT/'reference-structures.json')
evidence=OUT/'evidence';evidence.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
sheet=Image.new('RGB',(1920,1200),(18,22,28));draw=ImageDraw.Draw(sheet)
draw.text((22,12),f'{version} 私人比赛实机采集（非 Blender 渲染）',font=font,fill='white')
draw.text((22,45),'仅证明下列采样动作；完整验收范围见 runtime-verification.json。',font=small,fill=(185,196,210))
for i,sample in enumerate(runtime['samples'][:6]):
 p=TASK/sample['path'];assert p.exists();dest=evidence/(sample['name']+'.png');shutil.copy2(p,dest)
 x=(i%2)*960;y=80+(i//2)*370;im=Image.open(p).convert('RGB').resize((960,540));sheet.paste(im.resize((640,360)),(x,y))
 # Beside each complete frame, show the weapon crop at readable resolution.
 original=Image.open(p).convert('RGB');w,h=original.size
 bounds=(round(w*(.36 if sample['name']=='crouch' else .49)),round(h*.05 if sample['name']=='sprint' else h*.32),round(w*.985),round(h*.97))
 crop=original.crop(bounds).resize((320,210));sheet.paste(crop,(x+640,y+30));draw.text((x+648,y+248),sample['label'],font=small,fill='white')
sheet.save(OUT/'runtime-check.png')
for name,relative in runtime.get('sequences',{}).items():
 folder=TASK/relative;fs=sorted(folder.glob('[0-9][0-9][0-9][0-9].png'));assert fs
 record=read(folder/'record.json');times=record['FrameTimes'];assert len(times)==len(fs)
 ffmpeg=shutil.which('ffmpeg');assert ffmpeg,'ffmpeg is required to export gameplay evidence'
 exportWork=TASK/'work'/('deliver-'+version);exportWork.mkdir(exist_ok=True)
 lines=[]
 for p,t,nextTime in zip(fs,times,times[1:]+[record['Seconds']]):
  assert "'" not in str(p)
  lines.extend(["file '"+p.resolve().as_posix()+"'",f'duration {max(.001,nextTime-t):.9f}'])
 lines.append("file '"+fs[-1].resolve().as_posix()+"'")
 listing=exportWork/(name+'.ffconcat');listing.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 dest=evidence/(name+'.mp4')
 run=subprocess.run([ffmpeg,'-v','error','-y','-f','concat','-safe','0','-i',str(listing),'-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-fps_mode','vfr','-an','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],capture_output=True,text=True)
 assert run.returncode==0,run.stderr
 oldGif=evidence/(name+'.gif')
 if oldGif.exists():
  assert oldGif.resolve().parent==evidence.resolve();oldGif.unlink()
 shutil.copy2(folder/'record.json',evidence/(name+'-record.json'))
report=(ROOT/'src/release_report.md.in').read_text(encoding='utf-8').format(version=version,zip_sha256=package['sha256'],files=package['files'],runtime_conclusion=runtime['conclusion'],remaining='; '.join(runtime['remaining']))
(OUT/'重建记录.md').write_text(report,encoding='utf-8')
include=[ROOT/'README.md',ROOT/'inventory.json',ROOT/'reactive-motion.json',ROOT/'stock-world.json']
include += [p for p in (ROOT/'src').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
include += [p for folder in ('view','world') for p in (BUILD/folder).rglob('*') if p.is_file() and p.suffix in ('.smd','.qc')]
include += [BUILD/n for n in ('rig.json','world-rig.json','source-verification.json','compiled-verification.json','native-firing-grip.json','world-validation.json','animation-order-validation.json','animation-order-map.csv','compiled-reload-validation.json','compiled-dynamic-validation.json','right-forearm-validation.json','attack-blending-validation.json','compiled-attack-blending-validation.json','compiled-visual-motion-validation.json')]
include += [BUILD/'prowler_car101.rui',BUILD/'rui-layout-validation.json',BUILD/'audio-report.json']
# Local task history remains in the workspace, outside public deliverables.
manifest=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in sorted(set(include)) if p.exists()]
(OUT/'source-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(OUT/f'Prowler-Rebuild-Source-{version}.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(set(include)):
  if p.exists():z.write(p,'Prowler-Rebuild/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(OUT/f'Prowler-Evidence-{version}.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(evidence.iterdir()):z.write(p,'evidence/'+p.name)
 for n in ('runtime-check.png','runtime-verification.json','package-verification.json','bone-audit.csv','reference-structures.json','compiled-verification.json','native-firing-grip.json','animation-order-validation.json','animation-order-map.csv','compiled-reload-validation.json','compiled-dynamic-validation.json','right-forearm-validation.json','attack-blending-validation.json','compiled-attack-blending-validation.json','compiled-visual-motion-validation.json','重建记录.md','rui-layout-validation.json','audio-report.json','prowler_car101.rui','prowler_ammo_panel.json'):
  z.write(OUT/n,n)
for p in OUT.glob('*.zip'):
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
print('DELIVERABLES_VERIFIED',version,package['sha256'])

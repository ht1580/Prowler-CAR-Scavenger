"""Stage only this independent rebuild and validate the exact install ZIP bytes."""
import json,hashlib,struct,shutil,zipfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];TASK=ROOT.parents[1];CFG=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'));BUILD=ROOT/'build';STAGE=BUILD/'stage'/CFG['mod_name'];OUT=TASK/'outputs'/('prowler-zero' if CFG['version']=='0.2.0' else 'prowler-zero-'+CFG['version']);OUT.mkdir(exist_ok=True)
compiled=BUILD/'compiler_game/models/weapons/car101';models=STAGE/'mod/models/weapons/car101';models.mkdir(parents=True,exist_ok=True)
for name in ('ptpov_car101','w_car101'):shutil.copy2(compiled/(name+'_conv.mdl'),models/(name+'.mdl'))
paks=STAGE/'paks';paks.mkdir(exist_ok=True)
for name in ('prowler_zero.rpak','prowler_zero.starpak'):shutil.copy2(BUILD/'materials/paks'/name,paks/name)
(paks/'rpak.json').write_text(json.dumps({'Postload':{'prowler_zero.rpak':'common.rpak'}},indent=2),encoding='utf-8')
scripts=[dict(Path='prowler_stance.nut',RunOn='CLIENT',ClientCallback=dict(After='ProwlerStance_Init'))]
(STAGE/'mod.json').write_text(json.dumps(dict(Name=CFG['mod_name'],Version=CFG['version'],Description='Prowler Scavenger: native grip, shot-only reactive drum, quiet idle and client crouch pose. Stock CAR gameplay. No glow.',LoadPriority=0,RequiredOnClient=False,Scripts=scripts),indent=2),encoding='utf-8')
client=STAGE/'mod/scripts/vscripts';client.mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/'src/client/prowler_stance.nut',client/'prowler_stance.nut')
kv=STAGE/'keyvalues/scripts/weapons';kv.mkdir(parents=True,exist_ok=True)
(kv/'mp_weapon_car.txt').write_text('WeaponData\n{\n MP_BASE\n {\n  "viewmodel" "models/weapons/car101/ptpov_car101.mdl"\n  "playermodel" "models/weapons/car101/w_car101.mdl"\n  "holstermodel" "models/weapons/car101/w_car101.mdl"\n }\n}\n',encoding='ascii')
if '--stage-only' in sys.argv:
 print('STAGE_ONLY_OK',STAGE)
 sys.exit(0)
archive=OUT/(CFG['mod_name']+'-'+CFG['version']+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(STAGE.rglob('*')):
  if p.is_file():z.write(p,CFG['mod_name']+'/'+p.relative_to(STAGE).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name in z.namelist():
  relative=name.split('/',1)[1];p=STAGE/relative;data=z.read(name);assert data==p.read_bytes()
  if p.suffix=='.mdl':assert struct.unpack_from('<I',data,80)[0]==len(data)
  if p.suffix in ('.json','.txt'):assert not data.startswith(b'\xef\xbb\xbf')
  assert p.suffix not in ('.cfg','.dll','.exe','.bat','.ps1')
  if p.suffix=='.nut':assert p.relative_to(STAGE).as_posix()=='mod/scripts/vscripts/prowler_stance.nut'
report=dict(version=CFG['version'],sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size,files=len(z.namelist()),zip_crc=True,stage_bytes_equal=True,game_tested=False)
(OUT/'package-verification.json').write_text(json.dumps(report,indent=2));print('STAGE_PACKAGE_OK',json.dumps(report))

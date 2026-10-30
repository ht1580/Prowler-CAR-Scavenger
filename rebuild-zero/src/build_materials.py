"""Build fresh no-glow material packages from original PNGs. Does not consume old mod RPaks."""
import json,subprocess,struct
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];CFG=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'));OUT=ROOT/'build/materials';MAP=OUT/'maps';ASSET=OUT/'assets';PNG=OUT/'png'
for p in (MAP,ASSET,PNG):p.mkdir(parents=True,exist_ok=True)
tools=Path(CFG['tools_root'])/'vendor/tools';texconv=tools/'texconv.exe';repak=tools/'RePak-1.2.0.exe';texdir='texture/models/Weapons_R2/prowler_zero';dest=ASSET/texdir;dest.mkdir(parents=True,exist_ok=True)
spec={'col':('BC7_UNORM_SRGB',True),'nml':('BC5_UNORM',False),'gls':('BC7_UNORM',False),'spc':('BC7_UNORM_SRGB',True),'ilm':('BC7_UNORM',False),'ao':('BC7_UNORM',False),'cav':('BC7_UNORM',False)}
for suffix,(fmt,srgb) in spec.items():
 im=Image.open(Path(CFG['texture_source'])/f'prowler_v21_react_scavenger_{suffix}.png')
 if suffix in ('gls','ao','cav'):im=im.convert('L').convert('RGBA')
 else:im=im.convert('RGBA')
 image=PNG/f'scavenger_{suffix}.png';im.save(image)
 subprocess.run([str(texconv),'-srgb' if srgb else '--ignore-srgb','-nologo','-y','-dx10','-m','0','-f',fmt,'-o',str(dest),str(image)],capture_output=True,check=True)
tex=lambda s:texdir+'/scavenger_'+s
def material(kind):
 return dict({'$type':'matl'},path='models/Weapons_R2/prowler_zero/scavenger',type=kind,version=12,shaderset=f'shaderset/uberAoCavEmitEntcolmeSamp2222222_{kind}.rpak',surface='weapon',width=2048,height=2048,selfillumtint=[0,0,0,1],visibilityflags='opaque',faceflags=6,textures=[tex(s) for s in ('col','nml','gls','spc','ilm')]+['']*6+[tex('ao'),tex('cav')])
doc=dict(name='prowler_zero',assetsDir='../assets',outputDir='../paks',version=7,starpakPath='prowler_zero.starpak',files=[{'$type':'txtr','path':tex(s)} for s in spec]+[material('skn'),material('fix')])
(MAP/'prowler_zero.json').write_text(json.dumps(doc,indent=2))
r=subprocess.run([str(repak),'prowler_zero.json'],cwd=MAP,capture_output=True,text=True);(OUT/'repak.log').write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0,r.returncode
print('MATERIALS_OK',[(p.name,p.stat().st_size) for p in (OUT/'paks').glob('*')])

"""Package current source and real-game evidence, keyed to the tested ZIP hash."""
import json,hashlib,csv,zipfile,collections,shutil,sys
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
for name in ('animation-order-validation.json','animation-order-map.csv','compiled-reload-validation.json'):
 shutil.copy2(BUILD/name,OUT/name)
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
 crop=Image.open(p).convert('RGB').crop((640,300,1280,720)).resize((320,210));sheet.paste(crop,(x+640,y+30));draw.text((x+648,y+248),sample['label'],font=small,fill='white')
sheet.save(OUT/'runtime-check.png')
for name,relative in runtime.get('sequences',{}).items():
 folder=TASK/relative;fs=sorted(folder.glob('[0-9][0-9][0-9][0-9].png'));assert fs
 frames=[Image.open(p).convert('RGB').resize((768,432)) for p in fs]
 record=read(folder/'record.json')
 times=record.get('FrameTimes')
 if times and len(times)==len(frames):
  interval=[max(20,round((b-a)*100)*10) for a,b in zip(times,times[1:]+[record['Seconds']])]
 else:interval=max(20,round(record['Seconds']*100/len(frames))*10)
 frames[0].save(evidence/(name+'.gif'),save_all=True,append_images=frames[1:],duration=interval,loop=0)
 shutil.copy2(folder/'record.json',evidence/(name+'-record.json'))
report=f'''# {version} 参考结构修改与实机复测

当前安装包 SHA256：`{package['sha256']}`。安装目录全部 {package['files']} 个文件逐一核对与 ZIP 相同。

本轮参考了 [HK560 马洛里安](https://thunderstore.io/c/northstar/p/HK560/Malorian_Arms_3516/)、[Creamy CAR](https://thunderstore.io/c/northstar/p/Creamy_jpg/CAR_Pastel_Perfection/) 和 [CNS144 R301](https://thunderstore.io/c/northstar/p/CNS144/Mythic_R301_apex_R201/) 的骨架、序列表、增量动画编码及 bodygroup 结构；未复制其资产。

已修正转换器给省略位移的增量轨道填入绑定位置的问题，以及 Crowbar 验证时掩盖 RAWPOS 的问题。改用显式位移姿态和原版序列 DELTA 标记，精确保留零位移轨道；普通冲刺选用源原生右手动画。外接击杀屏依据实际机匣表面安装，第一、第三人称安装座一致。完整技术说明见 BUILD_README.md。

实机结论：{runtime['conclusion']}

0.2.4 动画核对：动画描述符/序列索引分别为第一人称124/97、第三人称4/4，255条原版事件及引用保持不变。修复了完整换弹的里程碑重采样及 late 段恢复：普通/空仓late1从完整段第34帧开始，空仓late2从第55帧开始。空仓插匣使用MILESTONE_2，后续FILLAMMO属于枪机/补弹阶段。编译后968帧验证与逐序列映射见 animation-order-map.csv 和 compiled-reload-validation.json。

尚未验收的范围：{'; '.join(runtime['remaining'])}

初始配装经运行时 GetMods 确认是机瞄、快速换弹、击杀减冷却及 ProScreen；附件测试和恢复结果单独列在运行时报告。客户端临时 SetBodygroup 会被游戏重新覆盖，其返回成功不证明已完成附件切换，相关尝试不计入验收。已有准星模组关闭原生瞄具 UI3/UI4/UI7；保留该配置，不将未显示原生准星误记为改模错误。

[实机采样图](runtime-check.png)、[逐骨骼用途](bone-audit.csv)、[运行时报告](runtime-verification.json)、[参考结构](reference-structures.json)。evidence 内 GIF 为真实窗口连续采集。原 CFG 未作源码编辑，安装前的模组及配置备份保留在本地 work 下。

本版是经过所列实机采样的测试候选，完整视觉验收尚未完成，不能标为最终通过。
'''
(OUT/'重建记录.md').write_text(report,encoding='utf-8')
include=[ROOT/'README.md',ROOT/'inventory.json',ROOT/'reactive-motion.json',ROOT/'stock-world.json']
include += [p for p in (ROOT/'src').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
include += [p for folder in ('view','world') for p in (BUILD/folder).rglob('*') if p.is_file() and p.suffix in ('.smd','.qc')]
include += [BUILD/n for n in ('rig.json','world-rig.json','source-verification.json','compiled-verification.json','native-firing-grip.json','world-validation.json','animation-order-validation.json','animation-order-map.csv','compiled-reload-validation.json')]
# Local task history remains in the workspace, outside public deliverables.
manifest=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in sorted(set(include)) if p.exists()]
(OUT/'source-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(OUT/f'Prowler-Rebuild-Source-{version}.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(set(include)):
  if p.exists():z.write(p,'Prowler-Rebuild/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(OUT/f'Prowler-Evidence-{version}.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(evidence.iterdir()):z.write(p,'evidence/'+p.name)
 for n in ('runtime-check.png','runtime-verification.json','package-verification.json','bone-audit.csv','reference-structures.json','compiled-verification.json','native-firing-grip.json','animation-order-validation.json','animation-order-map.csv','compiled-reload-validation.json','重建记录.md'):
  z.write(OUT/n,n)
for p in OUT.glob('*.zip'):
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
print('DELIVERABLES_VERIFIED',version,package['sha256'])

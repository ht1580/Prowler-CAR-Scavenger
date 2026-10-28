"""Assemble reviewable source, evidence and previews. Does not upgrade runtime status."""
import json,hashlib,csv,collections,zipfile,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];TASK=ROOT.parents[1];BUILD=ROOT/'build'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
cfg=read(ROOT/'src/config.json');VERSION=cfg['version'];OUT=TASK/'outputs'/('prowler-zero' if VERSION=='0.2.0' else 'prowler-zero-'+VERSION);OUT.mkdir(exist_ok=True)
cfg=read(ROOT/'src/config.json');rig=read(BUILD/'rig.json');inv=read(ROOT/'inventory.json');source=read(BUILD/'source-verification.json');compiled=read(BUILD/'compiled-verification.json');grip=read(BUILD/'native-firing-grip.json');package=read(OUT/'package-verification.json');cleanup=read(ROOT/'cleanup-verification.json')
import sys
sys.path.insert(0,str(ROOT/'src/tools'));from mdl_mesh import read_mdl_mesh
md=read_mdl_mesh(BUILD/'compiler_game/models/weapons/car101/ptpov_car101_conv.mdl');links=collections.Counter()
for weights in md['weights']:
 for i,w in weights:
  if w>0:links[rig['order'][i]]+=1
rows=[]
for i,name in enumerate(rig['order']):
 added=name in rig['extra'];children=[n for n,p in rig['parent'].items() if p==name]
 rows.append(dict(index=i,name=name,parent=rig['parent'][name] or '',added=added,vertex_influences=links[name],native_animated=name in inv['reactive_active_weighted'],children=';'.join(children),reason=('native weighted motion' if name in inv['reactive_active_weighted'] else 'weighted parent dependency') if added else 'original CAR contract'))
assert all(r['vertex_influences']>0 for r in rows if r['added'])
with (OUT/'bone-audit.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
sheet=Image.new('RGB',(1440,960),(16,21,29));draw=ImageDraw.Draw(sheet);draw.text((22,14),f'{VERSION} 固定游戏视角：成品模型 + 真实 TF2 手臂',font=font,fill='white');draw.text((22,53),'离线检查，非实机截图；灰色手臂、蓝色 ProScreen 为检查材质。',font=small,fill=(180,195,215))
for i,(name,label) in enumerate([('normal_hip_025','普通持枪'),('ads_015','开镜'),('reload_030','换弹：手与弹匣保持同一原生运动'),('fire_002','原生开火动作')]):
 im=Image.open(ROOT/'renders'/(name+'.png')).convert('RGB').resize((720,405));x=(i%2)*720;y=92+(i//2)*432;sheet.paste(im,(x,y));draw.text((x+16,y+405),label,font=small,fill='white')
sheet.save(OUT/'visual-check.png')
frames=[]
for p in sorted((ROOT/'renders').glob('drum_*.png')):
 im=Image.open(p).convert('RGB').resize((880,520));d=ImageDraw.Draw(im);d.rectangle((0,0,880,44),fill=(16,21,29));d.text((14,8),'原生机构动作 / 成品 MDL 解码帧 '+p.stem.split('_')[-1],font=small,fill='white');frames.append(im)
frames[0].save(OUT/'native-drum.gif',save_all=True,append_images=frames[1:],duration=130,loop=0,optimize=True)
for name in ('source-verification.json','compiled-verification.json','world-validation.json','audio-report.json','native-firing-grip.json','rig.json','rui-mounts.json'):
 shutil.copy2(BUILD/name,OUT/name)
shutil.copy2(ROOT/'cleanup-verification.json',OUT/'cleanup-verification.json')
runtime=dict(game_visual_verified=False,resources_loaded_in_initial_candidate=True,successful_holding_capture=False,baseline_training_error='Undefined variable SaveRecordedAnimation, sp/_gauntlet.gnut line 1033',local_mp_reached_verifiable_scene=False,desktop_capture_usable=False,temporary_game_processes_stopped=True,production_profile_modified=False,user_data_hashes_preserved=cleanup['all_hashes_match'])
(OUT/'runtime-verification.json').write_text(json.dumps(runtime,indent=2),encoding='utf-8')
evidence=OUT/'verification-logs';evidence.mkdir(exist_ok=True)
for name in ('placement-regression-before.log','proscreen-regression-before.log','placement-regression-after.log','compiled-021.log','grip-021.log','fixed-eye-render.log'):
 p=ROOT/name
 if p.exists():shutil.copy2(p,evidence/name)
excerpts=[]
for p in sorted((ROOT/'test-profile/logs').glob('*.txt')):
 lines=p.read_text(encoding='utf-8',errors='replace').splitlines()
 selected=[s for s in lines if any(k in s for k in ('PZ_','COMPILE ERROR Undefined variable "SaveRecordedAnimation"','sp/_gauntlet.gnut line','Loaded mod Prowler.CAR.Scavenger successfully','Mod Prowler.CAR.Scavenger is disabled','LoadStreamPak: prowler_zero'))]
 if selected:excerpts += [p.name,*selected]
(evidence/'runtime-excerpts.txt').write_text('\n'.join(excerpts),encoding='utf-8')
provenance=[]
paths=[Path(inv['model']),Path(read(BUILD/'world-rig.json')['source_model']),Path(cfg['stock_root'])/'models/weapons/car101/ptpov_car101.mdl',Path(cfg['stock_root'])/'models/weapons/car101/w_car101.mdl']
native=(ROOT/'src'/cfg['original_export']).resolve()/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler'
used={d['source'] for d in rig['animations'].values() if d['source']}|{'idle_0','idle_1'}
for name in sorted(used):
 folder='anims_prowler_react_v21_scavenger_v_animRig' if name.startswith(('fire_reactive','fire_optic_reactive','fire_onehanded','idle_reactive')) else 'anims_prowler_base_v_animRig';p=native/folder/(name+'.cast')
 if p.exists():paths.append(p)
for p in paths:provenance.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
(OUT/'input-provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
readme=(ROOT/'README.md').read_text(encoding='utf-8')
report=f'''# 从零重建 {VERSION} 交付记录

已生成独立新工程、安装候选包、完整生成的 SMD/QC 和检查资料。**实机视觉验收未完成，不能将本版标记为最终验收通过。**

[安装包](Prowler.CAR.Scavenger-{VERSION}.zip) · [完整重建源码](Prowler-Rebuild-Source-{VERSION}.zip) · [离线画面核查](visual-check.png) · [原生机构动作 GIF](native-drum.gif)

安装包 {package['bytes']:,} 字节，{package['files']} 个文件。SHA256：`{package['sha256']}`。

本轮没有改写旧工程或实际 R2Vanilla 的模组目录。测试仅使用独立 D: profile，临时进程已经停止。原设置、CFG、视频配置和存档共 4 个文件的哈希与备份完全一致，无需还原。

## 0.2.1 修正：整体视角与 ProScreen

用户实机报告 0.2.0 枪模位于视野外、ProScreen 没有对上。现已离线重现：固定原版相机后，旧版实际待机叠加把枪模整体旋出画面；旧预览跟随动画相机，掩盖了问题。

根因是参考动画被编译器多转了 +90°，使 `subtract(ref)` 的待机根骨产生 -90° 偏移。现在仅补偿参考动画根骨，转换后参考与绑定一致，待机根骨与相机均为零偏移；原始绝对动作、手枪相对关系和游戏 FOV 不靠手工前推修补。

ProScreen 外壳从后部立管移到机匣侧面，依据原生侧表面 x=0.772 与外壳背面推导骨骼安装位置，留 0.01 单位间隙；外壳和 RUI 仍使用同一骨骼及 0.65 缩放。新增 4 项位置回归与原有 8 项检查通过，共 12 项。

[固定相机前后对照](placement-comparison.png) 包含真正解码的待机层；[ProScreen 侧面核对](proscreen-side-mount.png) 中蓝色为外壳、粉色为 RUI 的检查材质，不是实机外观。旧版在 70/90/100° 水平 FOV 扫描中枪模均不可见，修正后枪模进入画面。新版 ProScreen 外壳在 90/100° 完整进入画面；70° 会有部分外壳被画面边界裁切。

以上是离线重现与修正证据，0.2.1 尚未实机复测。安装时完整替换旧同名模组，确保游戏加载新版 MDL。

## 与旧版的区别

- 重新读取原始模型和原生动作，重新生成第一/第三人称模型、骨架、动画、材质和声音；没有把旧成品模型换版本号，也没有复用旧生成的 SMD/QC。
- 不再把转鼓塞到 CAR 枪栓上；保留原生独立线圈、转环、软管和弹簧关节及其局部曲线。总计 118 根骨骼：原版 CAR 的 85 根兼容骨，加 33 根有网格或父级用途的机构骨。
- 开火和待机的公共手臂运动也来自原生动作，经 TF2 手臂适配后生成增量，不再用 CAR 公共层替代原生开火握持。
- 换弹期间，手、枪和弹匣共享同一原生采样时间；没有独立将手推离镜头。
- 机瞄/附件、事件和序列表保持原版 CAR 的角色与索引；无新加火层、姿态参数或生产客户端脚本，无发光。
- 第三人称瞄具从原始 VTX 重建时纠正面绕序，并与原版表面法线及朝向做回归对照。第三人称仍使用原版 4 个序列，没有追加独立的世界反应皮机构动画。

## 已核查的数据

| 项目 | 结果 |
|---|---|
| 第一人称 / 第三人称骨骼 | 118 / 14；新增机构骨均有实际引用 |
| 绝对动画 | {source['absolute_frames']} 帧；源握持位置误差小于 0.000062 单位 |
| 原生机构关键帧/骨骼对照 | {compiled['native_keys']} 次；最大旋转差 {compiled['max_native_angle_error']:.6f}° |
| 成品待机 / 开火逐帧 | 722 / 164 帧 |
| 成品双手相对枪身的原生对照 | {grip['keys']} 次；最大位置差 {grip['max_position_error']:.6f} 单位、角度差 {grip['max_angle_error']:.6f}° |
| 转子额外枢轴平移 | {compiled['max_rotor_pivot_translation']} |
| 逆绑定矩阵最大残差 | {compiled['inverse_error']:.9f} |
| VVD/VTX 硬件骨骼映射 | 视角与世界模型的骨骼引用直方图差异均为 0 |
| 世界动画根骨 | 12 个样本；最大差 0.000003815 |
| 回归检查 | 8 项通过，含附件角色、事件、音频库事件和原生握持 |
| 安装包 | CRC、逐字节暂存一致性和 MDL 内嵌长度通过 |

普通机构平移通道转换误差最高约 0.003906 单位，已记录；转子自身的平移独立要求为零。原生待机公共曲线重采样到机构循环时长；原有开火描述符保留 CAR 的帧率与长度，超出原生开火曲线的尾部保持原末帧。

离线画面使用真实 TF2 手臂几何，但没有复刻游戏中的光照、手套材质、不同 FOV、其他模组叠加或运行时序列调度。不能把这些预览当作实机截图。

## 实机尝试与剩余阻塞

现有启动器能加载初始候选的模组、RPak、Starpak 和声音；这些只是资源加载证据。

禁用重建模组后，本地训练关仍在原版 `sp/_gauntlet.gnut` 第 1033 行报告 `SaveRecordedAnimation` 未定义。其他独立本地多人尝试没有进入可观察的持枪场景。桌面抓取还出现黑屏、遮挡或陈旧画面，游戏内部截图也未得到可用文件。上述尝试没有被标记为实机通过；最终版包含后续原生开火/待机修订，尚未取得它的实机视觉证据。

因此“实机连射、停火、跨姿态过渡均正常”的目标仍未满足；没有宣布目标完成，也没有升级或替换用户的启动器、驱动、网络或登录配置。

## 检查材料

- [逐骨骼引用清单](bone-audit.csv)
- [原生握持逐帧结果](native-firing-grip.json)
- [成品动画与矩阵核查](compiled-verification.json)
- [设置/存档哈希与进程清理记录](cleanup-verification.json)
- [实机尝试边界](runtime-verification.json)
- [完整构建说明](BUILD_README.md)

参考成品仅用于机制对照：[HK560 马洛里安](https://thunderstore.io/c/northstar/p/HK560/Malorian_Arms_3516/)、[Nachos Apex CAR](https://thunderstore.io/c/northstar/p/NachosChipeados/Apex_Legends_Car/)、[Echo 反应皮 R99](https://thunderstore.io/c/northstar/p/Echo_XI/Apex_Reactive_R99_Model/)。本轮未复制这些参考作品的模型、材质或音频。
'''
(OUT/'重建记录.md').write_text(report,encoding='utf-8');(OUT/'BUILD_README.md').write_text(readme,encoding='utf-8')
archive=OUT/f'Prowler-Rebuild-Source-{VERSION}.zip'
include=[ROOT/'README.md',ROOT/'inventory.json',ROOT/'reactive-motion.json',ROOT/'stock-world.json']
include += [p for p in (ROOT/'src').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
include += [p for folder in ('view','world') for p in (BUILD/folder).rglob('*') if p.is_file() and p.suffix in ('.smd','.qc')]
include += [BUILD/n for n in ('rig.json','source-verification.json','compiled-verification.json','native-firing-grip.json','world-validation.json','audio-report.json')]
include += list((ROOT/'.planning/prowler-zero').glob('*.md'))
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(set(include)):
  if p.exists():z.write(p,'Prowler-Rebuild/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
manifest=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(set(include)) if p.exists()]
(OUT/'source-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('DELIVERABLES_READY',package['sha256'],archive.stat().st_size,len(include))

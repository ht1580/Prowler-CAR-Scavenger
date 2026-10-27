# Codex 历史经验（2026-08 ~ 2026-10）

来源：`D:\CodexStorage\CodexHome\memories\`、`D:\TitanfallMods\02_说明与核对`、`13_FinalAudit_20260916\FINAL-AUDIT.md`、`TitanfallModWorkbench\CAR_WORKFLOW.md`、`README.md`、`RUI_EDITOR_GUIDE.md`、`work\car_pipeline\README.md`、`outputs\CAR_RichMahogany_BUILD_REPORT.md`。

## 已做过的项目（避免重复劳动）

| 项目 | 内容 | 状态 / 位置 |
|---|---|---|
| Codex.CAR.RichMahogany 1.1.2（桃花心木） | Apex 模型移植到 CAR，RePak 1.2，6 个文件 | 曾进入主菜单；`work\car_pipeline` 可复现构建 |
| CAR.OutlandsAnnihilator 1.0.x（外域毁灭者） | Apex 皮肤，RePak 1.4 统一常驻包 | 弹药数字 RUI **未解决**；最新 1.0.13-rui 只是候选包 |
| CAR.Mythic.Allfather 1.1.x（神话皮） | 80 张贴图、48 个材质，眼睛和翅膀刚性绑定，有发光，无 PCF | 位置和光效待实测 |
| Codex.B3.MercilessWing 1.1.7（小帮手） | B3 Wingman 皮肤，保留原版骨骼索引和 5 个 RUI | 已安装在 R2Vanilla |
| Codex.ReducedImpactCamera 0.2.0 | NUT 加 147 个 keyvalues 补丁，用于减弱镜头抖动 | 游戏内无明显效果，见下文 |
| CameraShakeBlocker.dll | R2Vanilla 原生插件，hook ClientScreenShake | 只确认了启动器加载，没确认 hook 生效；绑定特定 client.dll 版本 |
| `D:\TitanfallMods\NN_*` | 每一轮修正一个目录（DoubleTake、AnimatedFX、PerOpticSensitivity 等） | 做类似需求前先看这些目录 |

## 模型（MDL v53）

- 流程：VPK 或 Harmony 提取 → MDLShit 提取 `.rui` → Crowbar 反编译 → Blender Source Tools → StudioMDL 编译（目标选 SFM）→ MDLShit 合并（vtx 用 `.dx90.vtx`，RUI 一起嵌入）。
- Blender 导入 QC 时用 `bpy.ops.import_scene.smd(filepath=qc, doAnim=False, createCollections=True)`。缺 DMX 的报错、导入动画慢，都不代表网格导入失败。QC、SMD 和 anims 文件夹要放在一起。
- 改 Blender 插件设置前先关掉所有 Blender 实例，否则正在运行的实例退出时会覆盖保存的设置。
- Apex 的骨骼数量比 TF2 多，必须**按骨骼名称重映射**到 TF2 骨架（CAR 有 85 根骨骼），不能沿用骨骼编号。没有参与蒙皮的辅助骨骼可以丢弃，缺失的装饰骨骼绑定到最近的祖先骨骼。
- 机瞄、弹匣、静态子弹如果抽动，就把它们绑定到 `def_c_base`。要检查**编译后**的成品，源 SMD 正确不代表成品正确。同时改第一人称和第三人称。
- 保留原版 QC 的 `$sequence` 顺序、事件帧、`$definebone` 和 `$bonemerge`。Delta 动画只覆盖指定的骨骼。
- 超过 32 个材质会编译失败。斜杠方向不同的同一路径算两个材质。可以加 `$MaxVerts 9999999`。
- 模型编译回**原版已登记的路径**（例如 `models/weapons/car101/ptpov_car101.mdl`）就不需要预缓存。用自定义路径时，需要加 `SERVER || CLIENT` 的 Before 回调来预缓存，否则地图里会报模型未预缓存（桃花心木 1.0.0 出过这个问题）。
- TF2 专用的细小材质面有时承担扳机或材质引用的作用，映射时可以从正常的参考 SMD 中保留这些面。
- 外观粗糙时，先比较三角面和顶点数，再检查各张贴图，不要反复换模型。
- 借用模型的技巧（Car Devo）：在 keyvalues 里把 `viewmodel` 指向另一把枪的 ptpov 模型，`playermodel` 指向 w_ 模型，再调整 bodygroup 和 UiData。

## RUI（弹药计数器、瞄具、Pro Screen）

RUI 由三部分组成：

1. MDL 里内嵌的 RUI 网格：决定位置、父骨骼和 UV，只存在于 ptpov 模型中。
2. keyvalues 里的 `uiN_enable` + `UiDataN { "ui" "mesh" Args{} }`。
3. `ui/*.rpak` 中的布局：二进制，不能编辑。

注意事项：

- **弹药数字和 Pro Screen 击杀计数器是两套东西**。`car_smg_ammo_counter` / `car_smg_rui_lower` 绑定 `weapon_ammo`；`pro_screen_panel` / `pro_screen_rui_upper` 绑定 `proscreen_int0`。外域毁灭者把两者搞混过，错误地宣称"修好了"。
- 只设置 bodygroup，或者只检查 RUI 的名称和数量都不够。要核对 RUI 的顶点、朝向、UV、父骨骼和遮挡，以及合并后的 UiData。
- UI 槽编号不能照搬其他武器的（Car Devo 改过槽位）。
- 用 `TitanfallModWorkbench --rui-inspect` 和 `--rui-apply` 编辑 RUI。这两个命令只改原字节位置的数据，不改拓扑。
- 骨骼顺序变了就必须重新映射 RUI。只改网格、骨骼名称和顺序不变时，可以沿用原来的 .rui。
- 神话皮：从 Apex RMDL 中提取了四顶点的弹药面板，替换 `car_smg_rui_lower` 的空间位置，同时保留 TF2 的 UI 名称、UV 和显示逻辑。

## 材质与贴图

- 验证过的编码方式（外域毁灭者 1.0.7/1.0.8）：

| 贴图 | 编码 |
|---|---|
| `col` | BC7_UNORM_SRGB |
| `nml` | BC5_UNORM |
| `gls` | BC4_UNORM |
| `spc` | BC7_UNORM_SRGB |
| `ao` / `cav` / `ilm` | BC7_UNORM（线性） |

- Apex 的法线贴图蓝通道为 0，只存储 XY，必须用 BC5，由着色器重建 Z；用 BC7 会出错。
- 颜色图的 sRGB 设置要明确。不能靠整体压暗来掩盖重复的 gamma 校正。验证时要把成品贴图解码出来和原图比较，只看 DDS 头不够。
- 材质和贴图放在**同一个常驻 rpak** 里（`$disableStreaming: true`），并用 `Postload` 挂到 `common.rpak` 之后。以前分成多个包时，出现过启动卡住、材质不加载的问题。
- RePak 1.2 需要手动修补页对齐，否则会出现段尺寸不足；RePak 1.4 不需要。
- 外域毁灭者 1.0.8 的模板（alpha 和发光）在阴影里会泛白。1.0.10 的修正：不透明 blendState、关闭发光、断开 ilm、perfGloss 0.35、perfSpecColor 0.015。参数见 `car_outlands\stability-policy.json`。
- 不透明材质要显式设置 `visibilityflags: opaque`（RePak 1.2 map）。
- 用 1.4 制作材质最简单的方法：用 RSX 导出一个原版 TF2 matl（得到 .json + .uber），然后只改 `$textures` 的路径和 name。skn 着色器的 0 基槽位是 0 col、1 nml、2 gls、3 spc、4 ilm、11 ao、12 cav。
- 发光要分两件事记录：材质发光和 PCF 粒子。VMT 存在、亮度参数调大、Blender 里能发光，都不能证明 TF2 里能显示。删掉 PCF 也不等于粒子问题修好了。

## Keyvalues 与冲突

- Northstar 按已加载模组的**倒序**合并 keyvalues，结果在 `<profile>\runtime\compiled\scripts\weapons\`，文件为 `mod_original_X.txt` 加 `mod_patch_0..N_X.txt`，用 `#base` 串联。CAR 同时被 SimplerCrosshairs、CustomScopeFOV、RemoveMuzzleFlash、Dot crosshair、RestoredReloadHint 等模组修改。改 CAR 之前先看这条合并链。
- 皮肤或模型包**不要带武器脚本**，避免重新声明伤害、后坐力、ADS 等值，覆盖用户其他模组的设置。
- `viewmodel_offset_hip/ads` 的三个分量顺序是 X（左右，正值向右）、Z（前后，正值向前）、Y（上下，正值向上）。用户已有的 ADS 值不要擅自改：桃花心木是 `0 0 0.25`，外域毁灭者和神话皮的机瞄是 `0 0 0.65`。
- Mods 块中可以用相对写法 `"damage_near_value" "++10"`。Mods 里只能写 eWeaponVar 支持的键，否则会报 Unrecognized entry 并崩溃。

## 脚本、CVar 与原生插件

- `.nut` 和 `.gnut` 都可以用，文件名不需要和函数名一致，必须在 Scripts 中声明。
- 设置已知的客户端 ConVar 时，直接调用 `SetConVarFloat`，比 `ClientCommand("exec ...")` 可靠。
- **旧的 CVar dump 不可信**：`shake_angleFactor_*`、`viewmodelShake` 在当前版本里会报 Unknown command。必须先用当前游戏日志或控制台验证。`shake_stop` 带作弊标记，`viewpunch_predictable_scalar` 和 `explosion_shake_*` 由服务端决定，在远程服务器上可能无效。
- 日志里出现 `Running custom CLIENT script callback` 或自己打印的 `[XXX] Applied`，只能说明脚本跑了，不能说明效果出现了。
- R2Vanilla 原生插件（ABI v1）：放在 `<profile>\plugins`，DLL 需要导出 `initializePlugin`，资源 101 中嵌入 `manifest.json`（`api_version: "1"`）。插件要校验 client.dll 的哈希，版本对不上就拒绝工作。确认生效必须看到 hook 成功的日志，再分场景实测。
- 用户在官服用 R2Vanilla。曾经出过事故：模组装到了 R2Northstar，结果根本没有加载。

## 音效

- 神话皮使用 10 个 48kHz、16 位 PCM、无元数据的事件音频，保留了原版 SecondShot。这是 Apex 音效的裁切和混音适配，不是完整的 Miles 事件图。

## 2026-10-26 Prowler.CAR 新经验（Claude）

工程目录：`D:\TitanfallMods\35_ProwlerCAR`。一键构建：`scripts\build_all.ps1 -Version x.y.z`。下次做同类移植时可以直接照搬这套脚本。

### 发光

- **RePak 1.2 的自发光字段是 `selfillumtint: [r,g,b,a]`**，ILM 贴图放在 textures 的第 5 个槽位。`emissiveTint`、`albedoTint`、`rasterFlags` 都不会被读取，日志会提示 "No selfillumtint specified"。Codex 以前 CAR 的发光不生效，很可能就是这个原因。
- RePak 1.2 的崩溃坑：
  - `outputDir` 目录不存在时，会直接以 0xC0000409 崩溃，而且没有任何日志。
  - BC4 贴图有疑似问题，gls 改用 BC7 线性即可。
- RePak 1.2 产出的 segment 2 尺寸偏小（B3 也是这样），可以用 `scripts\rpak_segments.py --fix` 修补。

### 导出 Apex 资产

- RSX 的 nogui 模式里，`--exportfilter` 会**缩小全局资产表**。导出 rig 和它的序列时，要把 rig GUID 和所有 aseq GUID 都写进 filter，并且 `--exporttypes arig,aseq`。否则日志会报 "RSEQ DEP not loaded"。
- 当前版本 Apex 的 aseq 会让 rsx_full 崩溃。R5Reloaded（S3 版本）可以正常导出：先用 `decompress_zstd_rpak.py` 解压 common.rpak，再把 starpak 硬链接到同一个目录，然后用 rsx_full 导出 SMD 动画。
- 音频：R5R 和当前 Apex 的 mbnk 都能用 RSX 按名称导出（`--exporttypes asrc --exportfilter <名称>`）。当前 Apex 导出的是 float32 WAV，需要用 ffmpeg 转换。

### 动画（Apex 原生动画搬到 TF2）

- TF2 viewmodel 本身不含手臂网格，手臂是通过 bonemerge 合进来的。所以 bind pose 是 T-pose 也没关系。
- 绝对动画（换弹、拔枪、开镜、冲刺等）用猎兽动画按骨骼名做 globals 重定向。叠加动画（idle、attack、walk、sway，SMD 里注释为 desc_delta）沿用 CAR 原版。
- 换弹做时间映射：Apex 弹匣离开、插回的帧，分别对齐 CAR 的 MILESTONE_1 和 FILLAMMO 事件帧。late 段从完整换弹里切出来，切点按 READYTOFIRE 的差值算。
- TF2 瞄具的位置：用 Apex 开镜末帧的相机位置减去 CAR 的，得到 Δ，把 TF2 瞄具平移 Δ。这样原版各瞄具的 `viewmodel_offset_ads` 不用改。
- Crowbar 输出的 `$definebone` 旋转顺序是 (eulerY, eulerZ, eulerX)，单位是度。
- RUI 顶点存在父骨骼的局部空间，移动骨骼时 RUI 会跟着走。CAR 的弹药 RUI 挂在 def_c_sight_on 上，换了枪身之后要用 rui_editor 重新摆放。

### 序列与索引（硬性规则）

- **sequence、attachment、bodygroup、poseparameter 的顺序必须与原版完全一致，新增内容只能追加在末尾。** 官服或原版服务端跑的是原版模型，服务端会把序列索引下发给客户端，中间插入一个序列就会让后面的动画全部播错。0.1.2 就踩过这个坑。
- 原版 `w_car101` 有 4 个序列：idle_seq，以及 attack_seq、attack_seq_alt1、attack_seq_alt2。三个 attack 序列在第 0 帧都有 muzzle_flash、shell_eject 回调和 3002 事件。**Codex 的世界模型模板只有一个 `idle`**，这会导致第三人称没有枪口火焰和抛壳。外域、神话、桃花心木这些包很可能都受影响。
- 核对工具：
  - `35_ProwlerCAR\scripts\mdl_compare.py <stock> <built>`：比对各表的名称顺序。
  - `mdl_seq_dump.py`：直接从 v53 二进制中读出序列、activity、flags 和事件。
- **anim desc 的顺序也要对齐**：Crowbar 的 QC 把所有 `$animation` 放在前面，内联动画（`@seq`）会被排到最后。要按原版二进制的 anim 表顺序交错输出 `$animation` 和 `$sequence`（gen_qc.py 已实现）。核对用 `mdl_deep_compare.py`，它基于 `mdl_lib.py`，表偏移是在原版 CAR 上校准的：bones 160/244、anim 184/92、seq 192/232、tex 208/44、skin 224、bodypart 236/16、attach 244/92、pose 304/20。
- **MDLShit 处理奇数（9）个 blend 时，最后一个动画索引会损坏**（越界）。1D blend 改用偶数个，转换后检查每个索引是否有效。
- 已发布的 Apex 移植模组（Nachos 的 CAR、Echo 的 R99、HK560 的 Flatline）都是**直接覆盖原版路径的模型**，keyvalues 不改 viewmodel。这是主流做法。
- 序列 0 `ref` 的 SMD 必须换成**新骨架自己的绑定姿态**。不能沿用原版的 ref.smd，因为里面武器骨骼还在原枪的位置。
- 交付前对照 Codex 的《改模 MOD 流程：历史记忆总结》第 7 节逐项核对。35_ProwlerCAR 已有对应的检查脚本：
  - `verify_baseline.py`：确认基线反编译和 RUI 来自当前 VPK
  - `audit_sources.py`：QC 引用、权重、绑定骨、材质
  - `mdl_deep_compare.py`：与原版逐项比对二进制结构
  - `make_blend.py`：生成 .blend 基线
- `PrecacheModel` 在客户端和 shared 脚本里都能用（原版 cl_stalker、sh_faction_dialogue 有先例）。
- SFM StudioMDL + MDLShit 编出来的模型，带 weightlist 的序列 flags 高位（0x80000/0x100000）和原版不同。这是工具链本身的差异，之前的构建也一样，不算回归。

### 世界模型动画的根骨旋转（"枪口朝上 90°"）

- 原版 TF2 世界武器模型（如 w_car101）的序列动画里，根骨 `ja_c_propGun` **每一帧都绕 X 轴旋转 +90°**（SMD 行 `0 0 0 0 1.5707963 0 0`）。第三人称持枪方向依赖这个旋转。
- 重建世界模型序列时，**不能用绑定姿态当动画**，否则枪会偏 90°、枪口朝上。要从原版反编译的 idle（`world_idle_tf2.smd`）里复制根骨姿态和帧数（CAR 是 61 帧）。
- 二进制结构比对（骨骼、挂点、序列名）查不出这个问题，必须单独比对动画数据。`35_ProwlerCAR\scripts\check_world_anim.py` 已作为构建门槛。

### 第三人称握持（世界模型）

- TF2 第三人称用的是原武器的手部动画，手持的是 weapon_bone。换成握把位置或角度不同的枪（比如无托枪）时，需要把世界模型网格和子骨骼整体乘以 `T = H_原枪 · H_新枪⁻¹`。H 取各自第一人称待机里的 `inv(def_c_base) @ ja_r_propHand`。
- 前手 IK（`r_hand_ik`，对应左手支撑）用左手关系映射：`T · L_新 · L_原⁻¹ · IK_原`。不要目测改位置。
- 对应工具：`35_ProwlerCAR\scripts\grip_delta.py` 计算 T，`overlay_world.py` 用 VVD 顶点出侧视对比图，`mdl_bones.py` 读取 v53 骨骼的 pos/quat（mstudiobone 结构：pos 在 +32，quat 在 +44，stride 244）。

### mod.json 不能带 BOM（0.1.2 到 0.1.7 实测全部失效的原因）

- Northstar 遇到 UTF-8 BOM 会报 `Failed reading mod file ...mod.json: parse error "Invalid value." at offset 0`，然后**静默跳过整个模组**。
- PowerShell 5.1 的 `Set-Content -Encoding utf8` 和 `Out-File` 一定会写入 BOM。写文本时必须用 `[IO.File]::WriteAllText(p, s, (New-Object Text.UTF8Encoding($false)))`。
- PowerShell 的 ConvertFrom-Json 能容忍 BOM，所以不能用它来验证。现在 ns.ps1 validate 会逐字节检查 BOM。
- 用户反馈"完全没效果"时，第一步先在 nslog 里搜 `Failed reading mod file` 或 `Skipping loading mod`。

### 序列描述的标志和 bbox 要恢复为原版值（0.1.11，第一人称看不到枪）

- v53 中 Crowbar 把原版 idle 序列的标志 `0x80000` 反编译成 `noanimation`。SFM studiomdl 编译、MDLShit 转换后，这一位变成了 `0x100000`。原版没有这个位，持枪待机时播放的正是这些序列。
- 编译链还会给 `optic_layer` 多加 `0x80000`，并重新计算每个序列的 bbox。
- 做法：MDLShit 之后运行 `35_ProwlerCAR\scripts\seq_fix.py <stock.mdl> <built.mdl>`。它把原版下标范围内的 seqdesc 标志（偏移 +12）和 bbox（+32，6 个 float）原样拷回。追加的序列只保留低 16 位标志。
- seqdesc 逐字核对：`mdl_deep_compare` 不比较标志和 bbox，要另外比较。除偏移量字段外，应与原版逐字节一致。
- 第一人称看不到、第三人称正常时，先排查：绑定姿态（`mdl_rest_cam.py`）、动画中枪相对相机的位置（`check_anim_cam.py`）、bodygroup、材质名。然后比较 seqdesc。

### 声音覆盖的 EventId 必须是音频库里的小写名（0.1.2–0.1.13 全部没生效的原因）

- NorthstarLauncher `audio.cpp` 用 `m_loadedAudioOverrides.find(eventName)` 区分大小写地精确匹配，不做小写转换。`EventIdRegex` 用 `std::regex_search`，同样区分大小写。
- 游戏传给它的是 Miles 音频库里的名字，例如 `weapon_car_loop_1p`，**不是** keyvalues 里的 `Weapon_Car_Loop_1P`。日志里出现 "Registering sound event ..." 只说明读取成功，**不能**说明匹配成功。
- 武器音效有多个变体：`_int`、`_intsm/_intmed/_intlg`（室内）、`_enemy`、`_BU`/`_BU1`、`_OLD2`。在一个 json 里把这些变体都列进 `EventId`。样本文件夹以 json 文件名（不含扩展名）命名；同一个 EventId 只有第一个注册的生效。
- 完整事件名清单：rwynx/Northstar-Commands-and-Audio-Overriding `all_audio_events.txt`（项目副本在 `35_ProwlerCAR\audio_raw\events\tf2_all_audio_events.txt`）。游戏里用 `ns_print_played_sounds 1` 确认。

### Crowbar 增量动画的根骨 −90°（开枪时模型飞走）

- Crowbar 反编译 v53 的增量 SMD 时，根骨统一带 (0,0,−90°) 的坐标修正，原版解码后的真实值是 0。用 SFM 重新编码时必须撤销这个修正，**而且要按数据判断**（所有帧的根骨都是 −90° 就撤销），不能按"文件和反编译结果字节相同"来判断：复制后再改过的动画（射击动画加了后坐）同样带着这个修正。
- 验证：用 `scripts\decode_native_pose.ps1`（32 位 PowerShell 加载 Crowbar 0.74 的程序集）解码最终 MDL，检查各增量层的根骨。

### 转动部件做进射击增量动画（不用姿态参数和脚本）

- 像枪栓、左轮转轮那样，把旋转直接写进 attack_* 增量动画，序列表和姿态参数表就能与原版完全一致。
- 自动武器每发都会重新触发射击序列，而且有 fadein，上一发的层还在淡出。所以每发要转**整圈**，按每帧 120° 设关键帧（slerp 走最短路径，单步必须小于 180°），最后回到原位。这样淡出的层只会继续向前转。按对称角度只转一格的话，淡出时会往回抖。

### HK560 的武器动画教程（用户指定以此为准）

- 图文版：https://github.com/HK560/Titanfall2AnimationModTutorial，副本在 `35_ProwlerCAR\docs_ref\`。视频合集 BV1zW4y1q7gm 没有简介，未登录拿不到 AI 字幕，360p 也看不清字。
- 要点：
  - 合并骨架：移植枪根骨的父级设为 `weapon_bone`；
  - 网格加 Armature 修改器，在姿态模式下检查模型是否跟着骨骼走；
  - 相机挂在 `jx_c_camera` 下；
  - delta 动画必须补上新骨骼的零增量，否则新骨骼会乱飞；
  - 每根骨骼都声明 `$bonemerge`；
  - 新序列只能加在 QC 末尾。
- 项目里的对应脚本：
  - `make_rig_blend.py`：生成 Blender 工程，并从游戏相机渲染第一人称图和侧视图；
  - `check_drum_seat.py`：解码全部动画，检查部件有没有离开原位。

### Blender Source Tools 在 Blender 5 里导入动画的坑

- 导入动画 SMD 时，BST 会写进骨架**当前的** action。每次导入前先设 `arm.animation_data.action = None`。
- 切换 action 时还要设置 `animation_data.action_slot = act.slots[0]`（Blender 4.4 以后的 slotted actions），否则姿态不会更新。
- BST 在 load_post 里报 "'Scene' object has no attribute 'vs'" 不影响导入。

### TF2 第三人称的手部 IK 是生效的

- 原版各枪的 `r_hand_ik`（前手 IK 目标）都不一样：Alternator z 2.4、CAR 8.4、Hemlok 9.3、R-201 7.1；`l_hand_ik`（握把手）都在原点附近。所以前手位置跟随武器模型。
- 换枪时：模型只做刚体变换，不要拉伸或压缩网格；把握把对齐后，前手 IK 放到新枪的前握把上。

### CAR 枪声替换要覆盖 fire_sound_2

- CAR 的 `fire_sound_2_player_1p/3p/npc` = `Weapon_Car_SecondShot_1P/3P/NPC`，每发都会播放。只替换 `burst_or_looping_*` 时，原版 CAR 的枪声会一直叠在新声音上。要用静音 wav 覆盖这三个事件。
- 猎兽在 Apex 里只有一套全自动循环开火音（连发模式也用它）。1p `Loop_Close_C` 是很安静的中置层，主体要用 3p `Loop_Close`。
- 进化皮的 `ReactiveFX_Fire_Swt` 是会衰减的单发点缀音，不能当循环切片使用。
- 重排循环时，切片要对齐每发的起音，不能从文件开头按周期硬切。

### Apex 第一人称动画要按 TF2 手臂重定向（0.1.16）

- TF2 的第一人称手臂是独立模型（`models/weapons/arms/pov_pilot_*.mdl`，在 `client_mp_common.bsp.pak000` 的 VPK 里），按骨骼名合并到武器模型上，并且带完整的肩膀和袖子。
- Apex 骨架身体高约 2 个单位、锁骨前倾，直接用会让肩膀和上臂出现在镜头前（"浮空的手 / 手臂挡镜头"）。只渲染骨骼线是看不出来的。
- 检查方法：`sim_fp_arms.py`。从 v53 MDL 嵌入的 VVD（`IDSV`，每个顶点 48 字节）读顶点，按骨骼名合并后蒙皮，再从 `jx_c_camera` 渲染，并和原版枪对照。
- 修复：`retarget_arms.py`：
  - 身体换成原版姿态；
  - 枪和手腕保持世界坐标不变；
  - 肘部用两骨 IK 求解；
  - 够不到时把身体沿视线前移最小的距离。
- 测试：两肩不能在眼睛前方超过 1.5 个单位。

### 手臂重定向要遵守 TF2 手臂骨架规则（0.1.17）

- 原版 CAR 实测的规则：
  - `shoulderMid` 不旋转；
  - 肘部只绕局部 −Y 轴弯曲（纯铰链，绕上臂的扭转为 0）；
  - `elbowB = 0.5×弯曲角 + 20.5°`；
  - `forearm` 承担约一半的手腕扭转。
- 用最短旋转的 IK 会把上臂拧到 88°，游戏里表现为袖子和手套拉伸。
- 肘部绕"肩→腕"轴的摆动角，选手腕扭转最小的位置。
- 检查工具：`arm_twist_report.py`。

### 原版的旋转/平行部件怎么做（L-STAR、Softball、MGL）

- 原版武器本来就有自己额外的枪骨，例如：
  - MGL：关节 `jx_ammo_root` 下挂一串子弹 `def_ammo1..9`；
  - Softball：`def_cylinder` 下挂 8 个并列的 `def_cylinder_flap`；
  - L-STAR：`def_spin_mid` / `def_l_spin_top` 并列挂在 `def_c_base` 下。
  所以"不能加骨骼"不是 TF2 的规则。
- 原版让零件转起来的几种方式：
  - Softball 单发转一格：开火增量动画从 +60°（一格）缓回 0。只适合单发武器；按 14 发/秒模拟会前后抖。
  - L-STAR 全自动：`attack_anim` 每发转一圈（13 帧）。
  - 另有序列 `fire_layer`（循环、增量、realtime、无 activity），开火时由引擎按名字播放。脚本和其他序列都没有引用它，与 `wind_loop_layer`、`run_layer` 同属引擎约定。
  - `loop_layer` 是常驻的慢转层。
  - `cooldown_seq` 负责停火后的减速。
- 工具：`spin_part_report.py`。读序列子层可以用 Crowbar 反射读取 `theAutoLayers`。
- 不要用"客户端脚本 + 姿态参数 + 常驻混合层"去转零件。Prowler 0.1.17–0.1.19 这样做，游戏里零件一转就飞，原因离线查不出来。直接照抄原版的 `fire_layer`（循环增量动画，标志 0x15）。
- StudioMDL 会把循环动画的最后一帧强制改成第一帧：转动循环必须转满 360°（每步不超过 180°）。0–120° 的锯齿会被编译成 0、40、80、0。
- 骨骼核查工具：`skeleton_audit.py`。逐帧检查拓扑、左右手链数量、拉伸、肘部铰链、扭转，并和原版对比，同时画骨架线框图（镜头视角下要把身体骨隐藏）。

### 第一人称移植不要新增骨骼（0.1.19，参照成功案例）——已被上一节修正：原版也有额外枪骨

- 能正常使用的 Apex→TF2 第一人称移植模组，骨骼都与原版完全一致，没有新增骨骼，进化皮的可动零件也一样。实测过 Nachos 的 Apex CAR（85 根）和 Echo 的进化 R99（88 根），参考包在 `references\thunderstore`。
- Prowler 移植加了 34 根骨骼后，游戏里绑在新骨骼上的转鼓一直会飞，换了两种转动方式都一样。
- 正确做法：Apex 零件刚性绑到原版骨骼。需要动的零件，借用原版本来就会动的骨骼（例如枪栓骨骼 `def_c_bolt` 改作转鼓），把它的静止位置放到零件轴心，在全姿态动画里固定。
- 对比工具：`compare_ports.py`、`anim_desc_dump.py`。Crowbar 解码第三方 v53 文件的动画块会失败，`decode_native_pose.ps1` 已改为跳过；但这样得到的只是静止姿态，不能拿来比较动作。

### Apex 动画藏在画面外的动作要推出 TF2 视野（0.1.18）

- 两边的武器画面视野不同：
  - Apex 固定 70°（4:3），16:9 下约 ±42.9° 水平、±27.7° 垂直；
  - TF2 跟随玩家视野，最大 110°，约 ±62.2° 水平、±46.9° 垂直。
- Apex 换弹会把甩出旧弹匣、取新弹匣（弹匣瞬移）放在 43–47° 这一带。在 TF2 里，这些就成了"多出来的手"和"乱飞的弹匣"。
- 修复办法：手或弹匣已离开枪身、且在 Apex 画面外时，沿原方向推出 TF2 最大视野（保持与镜头的距离，平滑过渡）。实现见 `retarget_arms.py` 的 `keep_offscreen`。
- 检查工具：
  - `screen_scan.py`：列出手和弹匣的屏幕角度；
  - `sim_fp_arms.py`：设 `SIM_FOV=110` 模拟宽视野；
  - `apex_mag.py` 的思路：直接看 Apex 源动画（注意文件名带 `_59_98_` 的是切片）。
- 原版 CAR 的 `wind_loop_layer` 是非增量层，只作用在左臂和镜头上，高速移动时把左手举到左上方。这是 TF2 自带的动作，不是 bug。
- 排查"零件乱飞"时，先把编译后的数据核一遍：`vtx_bones.py`（VTX/VVD 骨槽）、`check_pose_to_bone.py`、`mdl_engine_dump.ps1`（v53 骨骼字段）。

### 持续转动的零件不能写进开火增量动画

- 引擎每发都会重新叠加开火增量动画，并和上一发交叉淡入淡出，所以增量动画无法跨多发累积转动。
- 写进开火动画的话，只能每发转整圈。这样转速太快，画面频闪，看起来像零件在乱飞。
- 正确做法：客户端脚本用 `SetPoseParameter` 控制一个循环姿态参数，配合常驻（autoplay）的增量动画层，序列和参数都追加在最后。
- 关键帧数：MDLShit 会损坏 9 键混合的第 9 个索引，所以用 8 键均分 0–360°（第 7 键等于第 0 键），循环无缝。

### 音效峰值要留余量

- Apex 的浮点音源峰值可以超过 0 dBFS（猎兽 3P Loop_Close 到 +3）。
- 首发和循环在开火瞬间同时播放，两者都接近满幅时，叠加后会在游戏里炸音。
- 所有覆盖样本用线性增益降到 −6 dBFS。不要用 tanh 之类的软削波，它本身就是失真。

### 脚本与工具小坑

- PowerShell 5.1 读取没有 BOM 的 .ps1 时按 ANSI 解码，脚本里写的中文路径（`01_最新安装包`）会变成乱码。含中文的 .ps1 要存成带 BOM 的 UTF-8；只有给 Northstar 读的 mod 文本文件才必须无 BOM。
- PowerShell 5.1 用 `*>` 重定向写出的日志是 UTF-16LE。Python 读这些日志要先检查 BOM。

- 客户端脚本里 `SetPoseParameter(string name, float)` 传的是名字，服务端传的是 id。
- 客户端可以用 `GetViewModelEntity`、`LookupAttachment`、`StartParticleEffectOnEntity`。
- PowerShell 的 `$p` 和 `$P` 是同一个变量（大小写不敏感），`$args` 是自动变量，都不能拿来当普通变量。

## 工作方式偏好（用户）

- 先扫描本机已有的东西，再考虑下载，并分清哪些已有、哪些真的缺。
- 遇到问题要做文件级诊断，给出能用的结果，不要只给通用建议。
- 用户纠正方向时，先回答用户实际问的问题（例如问的是 .nut 文件名，就先判断文件名本身）。
- 用户说"没用"时，要换思路（例如从 CFG 改成注入），不要继续堆参数。
- 用户偏好原生风格的 UI（Blender 面板等），不要额外的装饰。
- Codex 留下的报告是中文，格式为"历史问题 → 当前处理 → 边界"。每次交付都写清楚静态核对的范围和待实测的项目。

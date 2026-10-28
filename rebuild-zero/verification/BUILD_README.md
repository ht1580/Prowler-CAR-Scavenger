# Prowler CAR Scavenger — independent rebuild 0.2.0

这是从原始 Apex CAST 和 TF2 原版资源重新构建的独立工程，不以 0.1.x 生成的 SMD、QC 或模型作为生产输入。旧工程保持原状。现有解包、转换及二进制核查工具予以复用，并保存在 `src/tools/`。

当前状态：完整离线构建和数据核对通过；尚未完成实机画面验收。不得把日志中的模组/材质加载记录视作游戏视觉效果已通过。

## 构建

1. 检查 `src/config.json` 中的原始资源、CAST 解析库和本机工具路径。
2. 运行 `src/rebuild.ps1 -Render`。它会重新生成视角/世界模型、动画、材质、声音，编译并转换为 MDL v53，反向解码验证，运行回归检查，再打包。
3. 已生成的 SMD/QC 位于 `build/view/` 和 `build/world/`。只重编译模型可运行 `src/compile_models.ps1`、`src/finish_models.py`；仍需要本机编译器、转换器和原版 RUI。

需要 Blender 5.2（含 mathutils / numpy）、Source Filmmaker StudioMDL、MDLShit、Crowbar 0.74（由 x86 PowerShell 反射调用）、texconv、RePak 1.2、ffmpeg、Python/Pillow。工具二进制与原始游戏资源不在源码包中；本机已经存在，配置文件记录了路径。

## 主要实现

- 保留 CAR 第一人称 85 根骨骼的名称、顺序与父级，追加 33 根有原始权重、独立运动或必要父级用途的机构骨，共 118 根；没有无引用的新增骨骼。
- 使用原始 CAST 的拔枪、开镜、换弹、冲刺等动作；手、枪身和弹匣使用同一时间采样。TF2 手臂通过双骨 IK 适配，保持原始手腕与道具的世界位置，不再独立将手推离镜头。
- 开火时公共手臂和枪身也采用原生反应皮动作，经手臂适配后计算增量；不再保留 CAR 公共射击层来替代原生握持运动。
- 原生反应皮机构运动写入现有开火和待机 autoplay 描述符，不增加自定义开火序列或姿态参数。待机的公共动作曲线重采样到机构循环的周期，两端闭合。
- CAR 原有 124 个动画描述符、97 个序列、30 个附件、3 个姿态参数保持索引；第三人称保留 14 根原版骨骼、附件、事件和 4 个序列；没有追加独立的世界反应皮机构动画。
- 原始贴图重新编码为 RPak；不发光。原始 WAV 重新解码并按 CAR 节奏重排，按实际音频库的大小写定义 71 个事件覆盖。
- 武器 KeyValues 只指定模型路径，不修改 CFG、数值、射速、准星或视场角。

## 验证

- 2,093 帧绝对动画验证原生握持关系。
- 转换后逐帧核对 164 个开火帧、722 个待机帧；共 1,772 次双手相对枪身的原生姿态对照。
- 检查骨骼逆绑定矩阵、嵌入的 VVD/VTX、硬件骨骼槽映射、三角面绕序、序列与事件、音频事件、ZIP 与暂存目录的一致性。
- 从原始 VTX 重建世界瞄具时会显式翻转面顺序以适配 SMD 编译约定；回归检查与原版的表面法线及面朝向比较。
- 实际 TF2 手臂与成品武器网格用于离线渲染。`Visual_Validation.blend` 是烘焙蒙皮检查场景；完整骨架和动画源见生成的 SMD/QC。

## 参考与验证边界

- [HK560 Malorian Arms 3516 0.1.0](https://thunderstore.io/c/northstar/p/HK560/Malorian_Arms_3516/)：活动零件在原有攻击描述符中运动，成品有 118 根骨骼。
- [NachosChipeados Apex Legends Car 1.0.0](https://thunderstore.io/c/northstar/p/NachosChipeados/Apex_Legends_Car/)：CAR 替换的原有表结构。
- [Echo_XI Apex Reactive R99 Model 1.0.1](https://thunderstore.io/c/northstar/p/Echo_XI/Apex_Reactive_R99_Model/)：反应皮与原有 autoplay/开火入口。

本轮已用独立 D: profile 启动现有启动器，确认候选资源可以加载；但没有取得可用的实机持枪画面。禁用重建模组的训练关基线遇到 `SaveRecordedAnimation` 未定义的原版脚本错误，本地多人尝试也未进入可验收场景。桌面抓屏出现黑屏、被遮挡或陈旧图像；这些图片不作为实机证明。临时测试进程已停止，用户设置、CFG 与存档的 4 个文件均核对与备份哈希一致。

诊断 profile 和临时 UI/client 脚本仅存在于工作目录，不包含在安装包或生成的生产资产中。实机连射、停火、跨姿态过渡与其他 profile 模组共存仍待确认。

# Prowler.CAR.Scavenger

Apex猎兽Scavenger替换Titanfall2 / R2Vanilla CAR。当前 **0.2.14 完整原生跑步与固定外观候选，未完成本轮实机视觉验收**。

- [下载候选安装包](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.14/Prowler.CAR.Scavenger-0.2.14.zip)
- [源码及SMD/QC](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.14/Prowler-Rebuild-Source-0.2.14.zip)
- [离线预览与检查记录](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.14/Prowler-Evidence-0.2.14.zip)
- [已编译模型离线GIF和视频](previews/0.2.14/README.md)

普通跑步完整使用原始sprint_0的21帧、36FPS枪和双手轨迹，保留原生退出视野下沿阶段。去掉此前20%/25%摆幅压缩和固定初始握点。出入跑步仍匹配端点，原始根/镜头轨迹和CAR事件时序保留。

两个MDL的9档皮肤表原本已经统一为猎兽材质。新增只作用于本地CAR武器和第一人称实体的Skin/Camo归零保护，隔离游戏内皮肤和迷彩覆盖；原始猎兽贴图、保存的配装、手套和其他武器材质保持。既有枪声、换弹声音、斜持、弱视觉后座和计数器安装保留。

72项源/编译检查通过，40个安装文件与ZIP一致。本轮原配置及独立测试配置均白屏，未确认新外观保护的运行时效果；一次白屏下跳图诊断出现engine.dll崩溃，原因未定位。离线基础色预览不能替代实机验收，没有使用旧版录像冒充新版本通过。

退出游戏并备份旧同名模组后，将ZIP内Prowler.CAR.Scavenger完整替换到实际profile的mods目录。候选安装包无CFG、DLL、EXE或QA诊断脚本，含一个生产CLIENT脚本。源码与安装包均明确保留未实测状态。

[本轮验证边界](rebuild-zero/verification/0.2.14/runtime-verification.json) · [固定外观检查](rebuild-zero/verification/0.2.14/fixed-appearance-validation.json) · [重建记录](rebuild-zero/verification/0.2.14/重建记录.md) · [构建说明](rebuild-zero/README.md)

[此前0.2.13实机记录](previews/0.2.13/README.md)保留作历史对照，其跑步仍为压缩摆幅版本。

# Prowler.CAR.Scavenger

Apex 猎兽 Scavenger 替换 Titanfall 2 / R2Vanilla CAR。当前 **0.2.10 开火与蹲姿混合修正候选**，已安装并冷启进入960x540窗口私人比赛复测。

- [下载安装包](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.10/Prowler.CAR.Scavenger-0.2.10.zip)
- [本版视频、GIF及原生跑步片段核对](previews/0.2.10/README.md)
- [完整实机证据](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.10/Prowler-Evidence-0.2.10.zip)
- [源码及SMD/QC](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.10/Prowler-Rebuild-Source-0.2.10.zip)

0.2.9此前只验证了静态/完整权重姿势，漏掉动态缺陷。本版定位并修改：原_3开火层首尾夹带约40至47度右前臂偏转；分别编写的蹲姿手臂和枪械局部偏移在叠加开火时会破坏接触。改用能回到中性的原生_0开火片段，并把蹲姿倾斜集中到现有公共spineC分支，镜头分支保持独立。

58项单元检查通过，源动作及编译后分别2100个混合接触采样，编译后相对位置变化最大约0.0014单位。2476帧绝对动画、968帧完整及恢复换弹检查继续核对；原动画索引、255条事件及骨骼数量保持。实际Jester_f手臂、14段653帧窗口采样覆盖普通点射/连射、蹲射、ADS、蹲起、换弹、侧移与跑步/停止；最终游戏正常退出。完整视觉接受仍待用户对照，不能仅靠数值和日志判定右手外观完全正确。

跑步片段重新核对了普通、heavy、onehanded和althand分支，目前保留右侧举枪的sprint_onehanded_0。关于是否改为Apex常见低持摆动仍待用户澄清；未声称已还原恶灵/烟妹完整选择图。

退出游戏并备份旧同名模组，将ZIP内Prowler.CAR.Scavenger完整替换到实际profile的mods目录。本机当前20个安装文件已核对与ZIP一致。包内只有一个生产CLIENT姿态脚本，没有CFG、DLL、EXE或诊断脚本。本轮未改配装和既有CFG源码。一次在比赛中切换640x360的B轮出现界面绘制调用栈中的整数除零，已记录并排除，恢复960x540冷启完成最终C轮；不声称消除所有崩溃风险。

[修正记录](rebuild-zero/verification/0.2.10/重建记录.md) · [运行时范围](rebuild-zero/verification/0.2.10/runtime-verification.json) · [编译混合验证](rebuild-zero/verification/0.2.10/compiled-attack-blending-validation.json) · [构建说明](rebuild-zero/README.md)

[0.2.9旧版近景](previews/0.2.9/README.md)保留作历史对照，不作为动态问题已通过的证据。视频无音轨，本轮未重新验收声音、击杀累计及公共服务器长期共存。

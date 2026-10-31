# Prowler.CAR.Scavenger

Apex猎兽Scavenger替换Titanfall2 / R2Vanilla CAR。当前 **0.2.12 右侧低持跑步修正候选**，已安装并在窗口模式私人比赛复测。

- [下载安装包](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/Prowler.CAR.Scavenger-0.2.12.zip)
- [源码和SMD/QC](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/Prowler-Rebuild-Source-0.2.12.zip)
- [完整实机证据](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/Prowler-Evidence-0.2.12.zip)
- [新旧跑姿GIF与视频](previews/0.2.12/README.md)

按用户明确选择，普通跑步由始终举枪的sprint_onehanded_0改为原生sprint_0低持节奏。为适配TF2固定镜头，保留20%位移和25%旋转摆幅并整体前移6单位；双手随同一低持握点摆动。进入/退出跑步对齐枪和双手端点，隐藏收放和两手举枪完成端保留，修正左肘循环接缝。特殊onehanded分支仍用独立单手动作，没有强制所有移动状态都冲刺。

68项检查通过；完整21帧低持循环、2476帧绝对动作和968帧换弹恢复继续核对。原动画顺序、255条事件、骨骼数量保持。16段974帧私人比赛覆盖跑步、起停、跑步后开火换弹、蹲姿/ADS开火与空中按蹲，游戏正常退出。

40个已安装文件与ZIP完全相同，相对0.2.11仅第一人称模型和mod.json版本号变化。0.2.11的增强枪声、换弹声音、空中斜持、弱化视觉左滚和外接屏安装保持。CFG源码、配装、武器数值未改。

退出游戏，备份旧同名模组后，将ZIP内Prowler.CAR.Scavenger完整替换到实际profile的mods目录。安装包不含CFG、DLL、EXE或诊断脚本。本版视频无音轨；[0.2.11有声实机](previews/0.2.11/README.md)可供试听相同音频。

完整视觉和手感仍待用户复核；未宣称还原恶灵/烟妹完整角色动画图，未穷尽全部手套、瞄具、技能和中断组合，未重新验收外接屏击杀数字增长或公共服务器长期共存。

[修正记录](rebuild-zero/verification/0.2.12/重建记录.md) · [运行时范围](rebuild-zero/verification/0.2.12/runtime-verification.json) · [完整低持循环检查](rebuild-zero/verification/0.2.12/compiled-low-sprint-validation.json) · [构建说明](rebuild-zero/README.md)

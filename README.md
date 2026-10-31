# Prowler.CAR.Scavenger

Apex 猎兽 Scavenger 替换 Titanfall 2 / R2Vanilla CAR。当前 **0.2.11 声音与动态修正候选**，已安装并冷启进入窗口模式私人比赛复测。

- [下载安装包](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.11/Prowler.CAR.Scavenger-0.2.11.zip)
- [完整实机证据](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.11/Prowler-Evidence-0.2.11.zip)
- [源码及SMD/QC](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.11/Prowler-Rebuild-Source-0.2.11.zip)
- [有声视频、动态GIF及新旧对比](previews/0.2.11/README.md)

本版针对枪声小、换弹缺少声音、空中蹲姿触发不稳、开火向左倾、枪手分离及外接击杀屏位置：

- 第一人称首发/连射样本峰值由0.20提高至0.65/0.55，补齐10个现有换弹声音路由。实际游戏正常/空仓换弹共触发7种事件，没有脚本重复整段播放；停火尾音和低弹警告保留。
- 蹲姿接受实际蹲姿或IN_DUCK输入，取消垂直速度门槛。25度斜持保持枪身前后深度；ADS和换弹由对应动作接管。
- 15个移动、跳落和regrip叠加条目通过现有公共骨骼驱动枪与手。开火弱化视觉位移/俯仰及偏航，去掉作者引入的视线轴左滚。CAR弹道后坐力与武器数值保留。
- 外接击杀屏上移1.5、前移3并收近枪管侧面，缩短两处支架；外壳和RUI共用安装骨骼。中央弹药屏保留。

65项单元检查与原始动画顺序/255条事件核对通过，编译后16,832个移动/攻击接触采样；2476帧绝对动作和968帧换弹恢复继续核对。没有新增骨骼。最终D轮覆盖站立、斜持腰射、侧移/蹲姿ADS、空中按蹲、普通/空仓换弹、跑步与停止，正常退出。声音录制来自同次游戏输出，无后期增益，削波计数0。

40个已安装文件与发布ZIP逐一相同。退出游戏并备份旧同名模组后，将ZIP内Prowler.CAR.Scavenger完整替换到实际profile的mods目录。包内无CFG、DLL、EXE或诊断脚本，本轮未改配装和既有CFG源码。

完整视觉/听感接受仍待用户复核，未穷尽所有手套、瞄具、技能与快速中断组合，未重新验收外接屏击杀数字增长及公共服务器长期共存。原生机械开放空隙保留。

[修正记录](rebuild-zero/verification/0.2.11/重建记录.md) · [运行时范围](rebuild-zero/verification/0.2.11/runtime-verification.json) · [编译握持核对](rebuild-zero/verification/0.2.11/compiled-visual-motion-validation.json) · [构建说明](rebuild-zero/README.md)

[0.2.10历史预览](previews/0.2.10/README.md)保留作对照。

> 此候选已撤回：跑步衔接混合误改根/镜头轨迹。请使用[0.2.13修正版预览](../0.2.13/README.md)。下文保留为历史诊断记录。

# 0.2.12 右侧低持跑步

按用户确认，普通跑步改为Apex常见的低持摆动。原生sprint_0节奏适配TF2固定镜头：20%位移、25%旋转摆幅，整体前移6单位；手和枪保持同一低持握点。特殊onehanded动作保留独立分支。没有宣称复原恶灵/烟妹完整角色动画选择图。

最终A轮，进程66976，R2Vanilla，960×540窗口私人Homestead/Attrition。16段974帧，对应ZIP b8186f1854e4ab5370aca0b64eab87a6203ae860c7fcd9177fdd909ff1e32360。早期3段菜单误录已排除，不放入发布证据。

## 新旧跑姿

![0.2.11举枪与0.2.12低持](sprint-before-after.gif)

左侧为0.2.11既有实机，右侧为本次0.2.12实机。场地路线和录制时刻不同，不是逐像素对齐比较。

![低持跑步静帧](sprint-before-after.png)

## 连续动作

![右侧低持摆动](preview-field-sprint.gif)

此GIF为field-sprint前4秒；完整6秒MP4保留末段靠墙/停止过程。

![两次开始和停止](preview-run-stop.gif)

![跑步后开火及换弹](preview-run-fire.gif)

以下视频均无音轨，按实际采集时间编码。音频、世界模型、材质和姿态控制器与0.2.11逐字节一致；[0.2.11有声试听](../0.2.11/README.md)保留。

- [ads-fire.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/ads-fire.mp4)
- [after-long-stop.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/after-long-stop.mp4)
- [air-duck.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/air-duck.mp4)
- [crouch-fire.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/crouch-fire.mp4)
- [field-sprint.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/field-sprint.mp4)
- [field-stop.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/field-stop.mp4)
- [final-idle.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/final-idle.mp4)
- [lane-stop.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/lane-stop.mp4)
- [reload.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/reload.mp4)
- [reload-after-ads.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/reload-after-ads.mp4)
- [run-fire.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/run-fire.mp4)
- [run-stop.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/run-stop.mp4)
- [sprint-lane.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/sprint-lane.mp4)
- [sprint-long.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/sprint-long.mp4)
- [standing.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/standing.mp4)
- [stop.mp4](https://github.com/ht1580/Prowler-CAR-Scavenger/releases/download/v0.2.12/stop.mp4)

68项单元检查通过；编译后完整21帧低持循环在保守70度水平视角下，最少32.95%的枪身顶点在画面内，既有25%门槛保持。源/编译后全动作、枪手接触、循环接缝、进入/退出跑步端点、255条原事件及原序列前缀继续核对。此几何统计不能替代实机外观判断。

普通低持循环没有枪身绕到左侧，所录停止/开火/换弹能恢复对应动作。近墙和落地仍由原游戏状态机选择动作；未把所有移动强制成冲刺。

这是修正候选，摆动手感和手部外观仍待用户复核。未穷尽所有手套、瞄具、技能、快速中断和公共服务器长期测试。

[实机范围](../../rebuild-zero/verification/0.2.12/runtime-verification.json) · [全部循环帧](../../rebuild-zero/verification/0.2.12/compiled-low-sprint-validation.json) · [修正记录](../../rebuild-zero/verification/0.2.12/重建记录.md)

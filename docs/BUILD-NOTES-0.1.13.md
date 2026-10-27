# Prowler CAR 0.1.13 — 2026-10-27

User feedback: both first-person invisibility and third-person grip problems persisted in 0.1.12. Earlier descriptor/source checks did not establish the actual displayed pose.

## Reproduced first-person defect

Crowbar 0.74 is used headlessly through its native .NET model reader in 32-bit SysWOW64 Windows PowerShell. Reader classes are loaded directly; no application initialization or game access is needed. Reflection arguments must be unwrapped with PSObject.BaseObject.

The actual original idle and ADS-idle delta roots are identity. The 0.1.12 native-decoded roots rotate -90 degrees about Z. Crowbar's AdjustPositionAndRotation exports that coordinate correction even for raw delta SMDs; 0.1.12 incorrectly rebased it as actual motion. gen_qc.py now reverses the root export basis for byte-identical copied Crowbar sources before bind-pose rebasing. Authored fire/spinner deltas are not corrected.

Before repair, all six sampled native idle-root checks failed. After repair they pass. A fixed-camera projection of final VVD vertices skinned with native-decoded draw-end and idle-autoplay yields visible fractions: original CAR 0.8785768, 0.1.12 0, 0.1.13 0.8653570. The view frustum uses 70-degree horizontal FOV and the original CAR camera held fixed. This is offline model evidence; gameplay remains untested.

## World model

The +3 translation displaced the trigger grip. Fit world-only geometry to both original CAR hand anchors instead: preserve the trigger grip, fit the front support to the original left hand, and compress rear clearance from -11.878 to the stock -7.493 extent (scale 0.55507 behind the grip). Apply the fit consistently to all LODs, normals, child bones and attachments. Both hand IK frames retain their original position and orientation. First-person geometry and audio are preserved.

Native decoding also showed the actual stock world animations have 24 frames, while the old third-party template had 61. All 96 original world frames were decoded and stored under stock/native-world.json; stock/world/world_idle.smd is generated in SMD export coordinates. Root pose, actual frame count and both hands are checked against that baseline.

## Validation and retained materials

- Full build 0.1.13 exited zero; 8 artifact regressions passed.
- WORLD_ANIM_OK, RUI_FIX_OK, SEQ_FIX_OK, MDL_INTEGRITY_OK, DEEP_COMPARE_OK for view/world.
- Native decoder output and tests gate build_all.ps1. The obsolete assertion proving a chosen +3 translation was replaced by native hand/timing/rear-clearance checks.
- Sources backed up at D:\CodexStorage\Workspaces\2026-10-26\s\work\baseline-0.1.12; old releases remain intact.
- Investigation evidence and offline projection helpers remain in that task work/ directory. Diagnostic failures from architecture/dependency/reflection setup are recorded in the chat/progress; no missing tools were installed.
- No game/mods/CFG/launcher management, game control or global memory/skill writes.

Build with a fresh version: scripts\build_all.ps1 -Version x.y.z. Package separately with scripts\package_release.ps1. A successful build still needs user game validation.

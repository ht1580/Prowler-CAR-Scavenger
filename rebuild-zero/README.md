# Prowler CAR Scavenger 0.2.4

Independent rebuild from the extracted Apex Scavenger CAST model/native animation clips and original Titanfall 2 CAR contracts. The installed candidate is under real-game validation; passing asset checks is not full visual acceptance.

## Reference work

Compared downloaded packages from HK560 (Malorian Arms 3516 0.1.0), Creamy_jpg (CAR Pastel Perfection 1.3.1), and CNS144 (Mythic R301 apex R201 0.1.2). Their model headers, sequence tables, animation flags and bodyparts were inspected. CNS144 ReactiveEvo Volt 1.0.1 was downloaded but its VPK contents have not been inspected. No reference model, texture or audio is redistributed here.

All three inspected ports retain the original weapon sequence interface and only idle_seq_autoplay. Their animation descriptors encode explicit offset poses, with DELTA on the consuming sequence. Bone counts differ (85, 118 and 163), so count alone cannot identify unnecessary bones. HK560 and Creamy's full animation decode fails in the current Crowbar reader; no recovered default poses were accepted as motion evidence.

## Repairs in this candidate

- Fixed MDLShit's omitted-position conversion: v49 delta tracks without position data were being filled with bind positions in v53. Firing wrists consequently contained about +/-10 units and the rotor about 6 units instead of zero. The targeted converter post-pass checks original track flags; intentional animation is retained.
- Made embedded RUI finishing repeatable: positions are always derived from the unmodified stock template, never re-scaled from already modified data.
- Fixed the validation reader: strict decode failures are no longer swallowed, and stored RAWPOS values are read literally. Crowbar's RAWPOS+DELTA shortcut otherwise masks the converter defect.
- Generate explicit offset SMD tracks, preserving the original CAR sequence flags, activities, events, indices and masks. Compensate the absolute root axis conversion. Canonicalize truly constant zero position channels to exact zero without loosening the rotor tolerance.
- Use the original native right-hand sprint_onehanded_0 for the normal sprint loop. Native sprint_0 places the gun behind the fixed original eye halfway through; the chosen variant keeps the weapon in front while preserving native grip.
- Seat the external CAR ProScreen on the receiver side, with shared 0.65 housing/RUI scale and a surface-derived backplate clearance. This changes the accessory mount only; it does not move the gun, camera or hands. The external kill counter is separate from the ammo display. The world-model screen uses the same receiver seat and 0.65 scale through the world grip fit. All three world optics use the corresponding viewmodel gun-relative seats. The world iron bodygroup now contains the native Prowler rear sight, replacing the detached stock CAR mesh.

## Skeleton and validation

Viewmodel: original 85-bone CAR prefix plus 33 source-weighted mechanism bones, 118 total. Parent dependencies, vertex influences, native animation channels and existing attachments are audited rather than deleting unweighted compatibility bones. World model retains 14 bones and original world sequence interface.

0.2.4 also aligns full reload magazine cues to CAR milestones, distinguishes insertion from empty-reload bolt filling, and derives all late segments from the same complete timeline using READYTOFIRE offsets (34/55 frames). Restore authoritative constant body channels before Vector48 compression to avoid full/resume quantization seams.

Current asset checks: 2 raw-delta tests, 7 placement/screen checks, 1 sprint check, 2 world-accessory/native-iron checks, 9 artifact checks, 1 repeated-finish stability check, plus compiled native-motion/contact/inverse-bind checks. Source sampling covers 2,093 absolute frames; native mechanism comparisons cover 5,412 samples; compiled firing and idle grip checks cover 1,772 hand samples. Reload validation adds 3 source-timeline tests, 2 compiled-timeline tests covering 968 frames, and a model-hash check in the artifact tests (27 unit tests total). These numbers describe offline validation, not every possible game state.

Real-game observations, unresolved items and the exact installed ZIP hash are recorded separately in runtime-verification.json and the delivery report. Earlier 0.2.0/0.2.1 reference-root explanations were superseded; do not reuse those reports as current evidence. In particular, a reference animation is not required to equal the bind-pose root.

## Build

Edit src/config.json to point at the original extracted inputs and installed tools. Run src/rebuild.ps1 for all assets, or src/validate_view.ps1 when reusing the verified world/material/audio build. Blender 5.2, StudioMDL, the local MDLShit build, x86 PowerShell/Crowbar and the workbench RUI/RPAK tools are required. Original Apex assets and reference packages are not bundled in the source archive. All generated intermediates stay in this D: task directory.

The build scripts do not install or launch the game. Diagnostic game-input tools are not packaged in the mod. The mod contains no CFG, DLL or production NUT script. Existing user CFG and loadouts must be preserved.

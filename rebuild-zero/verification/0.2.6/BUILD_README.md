# Prowler CAR Scavenger 0.2.6

Independent Prowler Scavenger rebuild for Titanfall 2/R2Vanilla. This candidate addresses user-reported idle jitter, continuous drum rotation, missing crouch stance, sprint posture and harsh audio. Actual observations and unresolved combinations are recorded in the hash-keyed runtime-verification.json; a successful build is not complete visual acceptance.

## Motion

The standing/ADS autoplay entries contain exact zero offsets. Every effective nonattack rotor channel retains its local pivot/orientation; source-native reactive animation is confined to attack clips. Native grip and coherent full/late reload timelines are retained.

Normal sprint uses regular Apex sprint_0 gun motion with a restrained cycle swing, blended from native held grip. The complete weapon/accessory/hand target set moves together before sleeve IK. It no longer substitutes sprint_onehanded_0. Visibility checks project actual gun body geometry as well as checking gun-origin depth. Actual sprint/stop samples are required because origin checks previously missed a below-viewport weapon.

R2's original viewmodel code drives only sprintfrac, velocity and ads_blend. A minimal CLIENT controller drives the new prowler_crouch parameter while quietly crouched and fades it out for firing/reloading/fast movement; the ADS row stays neutral. The fixed crouch offset derives from original CAR crouch cant/offset applied coherently to native gun and both hands. Extracted Apex crouch aliases contain breathing with identity endpoints; they are not falsely described as a recovered distinct crouch hold.

The original124 animation-descriptor prefix and all97 sequence IDs, activities, events and flags remain. Two crouch offsets append at124/125 and one pose parameter appends after the original three. Only idle_seq_autoplay expands to a2x2 ads/crouch grid. motion_contract.py checks exactly these intentional differences. The controller never forces sequences, changes bodygroups, emits sounds or sends console/CFG commands.

## RUI

The original Scavenger RMDL was exported in native format and its22 UI panels decoded independently of CAST. The central ammo display in prowler_smg_reticle is parented to def_c_base. CAR's numeric canvas now uses the exact native central display corners, retaining TF2 UI/UV/ammo binding. The external CAR ProScreen remains a separate accessory and kill counter.

Edit src/assets/prowler_ammo_panel.json and run src/finish_models.py. It writes build/prowler_car101.rui, an editable standalone geometry RUI accepted by MDLShit. Immutable original stock templates make repeated finishing idempotent. The separate Apex compiled UI drawing program was not decompiled or blindly transplanted. Source RMDL/package provenance is in the preset.

## Audio

Stop events, including suppressed-end variants, use tails rather than restarting the full firing loop. Original low-ammo warning behavior is preserved instead of substituting a two-second third-person gun report. PCM endpoints are faded, with overlap headroom. Runtime output is checked with bounded speaker-loopback capture, never a physical microphone. Zero clipping does not prove subjective timbre quality or remove normal map battle ambience.

## Existing repairs and references

The omitted-position DELTA conversion defect and Crowbar RAWPOS masking are corrected using original track provenance and strict decoding. Constant zero translations remain exact; rotor tolerances are not loosened. Reload cues align to CAR milestones, and late segments slice the same full timeline at34/55 frames. Empty insertion is distinct from later bolt/ammo filling.

View rig: original85-bone prefix plus33 weighted mechanism/dependency bones. World model: original14 bones and4 animations/sequences. World optics and ProScreen share corresponding gun-relative mounts. All255 original view/world events remain.

Structural references: HK560 Malorian0.1.0, Creamy CAR1.3.1 and CNS144 Mythic R3010.1.2. HK/Creamy full animation decode fails in the current reader; fallback poses were not accepted as recovered motion. No reference assets are redistributed. CNS Volt was downloaded but its VPK animation content was not inspected.

## Build

Set src/config.json to the original extracted assets and existing tools. Run src/rebuild.ps1 for all assets. src/validate_view.ps1 reuses world/material/audio outputs; after audio changes run src/build_audio.py with Blender's bundled Python first. Required tools include Blender5.2, StudioMDL, MDLShit, x86 PowerShell/Crowbar and workbench readers.

Checks cover raw deltas, repeat finishing, native RUI corners/UVs, screen placement, projected sprint geometry, controller/autoplay contracts, active nonattack rotor channels, audio routing, inverse binds/native contacts and968 compiled reload frames. Script-load logs are insufficient: verify visible crouch and movement transitions in game.

Build scripts do not install or launch the game. The package contains one production client stance controller, with no CFG, DLL, executable or diagnostic script. Existing user configuration/loadouts remain preserved. All work artifacts stay on D:.

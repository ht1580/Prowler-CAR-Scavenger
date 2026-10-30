# Prowler CAR Scavenger 0.2.7

Independent Prowler Scavenger rebuild for Titanfall 2/R2Vanilla. This candidate addresses user-reported idle jitter, continuous drum rotation, missing crouch stance, sprint posture and harsh audio. Actual observations and unresolved combinations are recorded in the hash-keyed runtime-verification.json; a successful build is not complete visual acceptance.

## Motion

The standing/ADS autoplay entries contain exact zero offsets. Base nonattack clips do not spin the drum; a separate shot-index phase holds the last chamber position. Other native reactive animation is confined to attack clips. Native grip and coherent full/late reload timelines are retained.

Sprint uses the full original sprint_althand_anim_0 raised, single-hand cycle, following the user's Wraith/Bangalore reference direction. It includes the free hand motion. Entry/exit blends hierarchy locals so attachments remain rigid. Fixed-eye geometry and actual sprint/stop observations are required. Wraith and Bangalore character settings resolve to pilot_survival_closer and pilot_survival_firesupport; those exported settings do not by themselves prove the complete native first-person animation selection graph.

R2's original viewmodel code drives only sprintfrac, velocity and ads_blend. A minimal CLIENT controller drives prowler_crouch: canted hip hold persists through firing, and fades out for reload/fast movement; ADS stays neutral. The offset derives from original CAR crouch cant/translation, applied coherently to gun and both hands. Extracted Apex crouch aliases contain breathing with identity endpoints, not a distinct recovered hold.

The original124 descriptor and97 sequence prefixes, activities, events and flags remain. Two crouch offsets and seven drum index poses append, for133 descriptors/98 sequences. One dedicated phase sequence appends; two pose parameters append after the original three. Only the original idle_seq_autoplay grid expands for crouch. All non-rotor channels in the new drum layer explicitly encode identity offsets: a masked first trial had bind-pose fallbacks and failed in game, so it was rejected. The controller never forces sequences, changes bodygroups, emits sounds or sends console/CFG commands.

Each ammo decrement advances one of six drum chambers (60degrees); phase persists after firing and does not rewind on reload. Rotor attack tracks are neutral, replacing native multiple-turn overtravel. Other reactive firing channels remain native. Reload ammo increases do not count as shots. The trigger shoulder is fitted independently of support-arm reach, reducing neutral right-wrist bend from40.04 to25.23degrees while preserving source-native gun/wrist/finger contacts.

External ProScreen moves2units forward on the receiver and uses two small stand-offs anchored to static body geometry, not a rotor. View/world housing and RUI share the same mount. Ray tests require the entire numeric canvas to remain clear of the gun, including the original ammo window.

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

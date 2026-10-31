# Prowler CAR Scavenger 0.2.11

Independent Prowler Scavenger rebuild for Titanfall2/R2Vanilla. Candidate0.2.11 addresses quiet fire, absent reload feedback, airborne cant, sideways shot roll, grip drift and the external counter seat. Fifteen stock movement/air/regrip additive entries and visual recoil now use one existing shared arm/weapon branch. Source and compiled tests include fractional weights. Real output-only audio and windowed game recordings remain required; user visual/audio acceptance stays open.

## Motion

The standing/ADS autoplay entries contain exact zero offsets. Base nonattack clips do not spin the drum; a separate shot-index phase holds the last chamber position. Other native reactive animation is confined to attack clips. Native grip and coherent full/late reload timelines are retained.

Sprint uses the full native RIGHT-hand sprint_onehanded_0 cycle, including free-hand movement. 0.2.7 mistakenly used its LEFT-hand counterpart sprint_althand_anim_0. Native sprint equip/holster clips keep their original hidden endpoints; a fading rigid transform aligns only their sprint ends. Normal sprint raise uses sprintraise_0 or sprintraise_regrip_0 and restores two-handed grip. True one-handed raise remains separate. The original camera and gun/hand contacts stay intact. Wraith/Bangalore settings identify closer/firesupport but do not prove their full animation selection graphs; this is a native right-hand style adaptation.

The two absolute crouch2idle_seq rows retain the native crouch_to_idle_0 transition. The iron/ADS row now uses the ADS anchor instead of the hip anchor. Stock roots/camera tracks are preserved. Fifteen active held-motion additive entries are retargeted as coherent_stock_motion; other masked/neutral stock deltas remain stock_delta. All absolute descriptors, including masked wind layers, author the same rigid screen seat.

R2's original viewmodel code drives only sprintfrac, velocity and ads_blend. A minimal CLIENT controller drives prowler_crouch: canted hip hold persists through firing, and fades out for reload; ADS stays neutral. Actual IN_DUCK input also works while airborne, without a vertical-speed gate. The controlled25degree view-axis cant preserves view depth through fractional blends, keeping the long rear housing from sweeping through the fixed eye; gun and hands move together. Extracted Apex crouch aliases contain breathing with identity endpoints, not a distinct recovered hold.

The original124 descriptor and97 sequence prefixes, activities, events and flags remain. Two crouch offsets and seven drum index poses append, for133 descriptors/98 sequences. One dedicated phase sequence appends; two pose parameters append after the original three. Only the original idle_seq_autoplay grid expands for crouch. All non-rotor channels in the new drum layer explicitly encode identity offsets: a masked first trial had bind-pose fallbacks and failed in game, so it was rejected. The controller never forces sequences, changes bodygroups, emits sounds or sends console/CFG commands.

Each ammo decrement advances one of six drum chambers (60degrees); phase persists after firing and does not rewind on reload. Rotor attack tracks are neutral, replacing native multiple-turn overtravel. Other reactive firing channels remain native. Reload ammo increases do not count as shots. The0.2.8 solver preserved wrist contacts but moved the right elbow inward and straightened the forearm. Raw local wrist-angle thresholds were not anatomical acceptance: even the stockCAR positive control exceeds that old threshold.0.2.9 retains the original right elbow matrix and forearm motion, keeping native wrist/fingers and weapon targets. The upper-arm hinge/clavicle adapts to put the shoulder behind the fixed eye. Elbow crease helpers follow the changed upper-arm bend. Actual TF2 distal sleeve/glove skinning is checked against native motion across draw,ADS,sprint,reload,holster and one-handed transitions.

External ProScreen now sits at native bind(.65,48.5,14), raised1.5 and advanced3 from0.2.10's(1.047551,47,11), with a closer lateral seat and two short static-body contacts. Native axes are X=side,Y=height,Z=forward. Housing/RUI share the mount in both view and world models. Projection, canvas occlusion, contact and support winding checks remain.

## Surfaces and materials

The full native body26733 and magazine2082 faces are retained. Their converted winding agrees with the original TF2 renderer; reversing the whole body would be wrong. Only the24 added support faces had opposite winding, fixed in view and world. Native open mechanical gaps remain; sampled views are not proof of every possible angle.

All7 maps remain. Base-color RGBA and colored ILM RGBA now survive conversion, rather than forcing base alpha and grayscaling ILM. The R2 material stays opaque and no-glow. Original and converted rasterizer/depth state were compared; sampler flags match. In-game queries show mat_depthtest_force_disabled and mat_bumpmap from the old CFG are unrecognized and mat_fullbright is0; no CFG change was made and those text entries were not assumed to be active causes.

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

Set src/config.json to the original extracted assets and existing tools. Run src/rebuild.ps1 for all assets. src/validate_view.ps1 rebuilds view and world, reusing material/audio outputs; after material changes run src/build_materials.py and src/tools/rpak_segments.py --fix, and after audio changes run src/build_audio.py with Blender's bundled Python first. Required tools include Blender5.2, StudioMDL, MDLShit, x86 PowerShell/Crowbar and workbench readers.

Checks cover raw deltas, repeat finishing, native RUI corners/UVs, screen placement, projected sprint geometry, controller/autoplay contracts, active nonattack rotor channels, audio routing, inverse binds/native contacts and968 compiled reload frames. Every frame of all absolute descriptors is decoded separately:2476 frames across80 absolute descriptors including reference, with hip-relative gun error<0.02, grip error<0.02, gun angle error<0.1degree and screen relative error<0.01. The absolute position compression bound is0.05: Vector48 truncation of fixed hip37.312496 to37.28125 contributes0.031246units, recorded separately from motion/contact error. 65 unit tests plus structural/native checks are required. Script-load logs are insufficient: verify visible crouch and movement transitions in game.

Evidence export additionally uses existing ffmpeg to encode original timed window captures as MP4. Explicitly labeled with-audio clips additionally mux bounded WASAPI output-only recordings; physical microphones are never selected. Build scripts do not install or launch the game. The package contains one production client stance controller, with no CFG, DLL, executable or diagnostic script. Existing user configuration/loadouts remain preserved. All work artifacts stay on D:.

## Right-hand acceptance correction

The old wrist/gun-only checks did not establish visible correctness. New regression tests first failed against0.2.8: draw-start elbow displacement7.807 units and distal sleeve shape deviation9.985 units despite preserved grip. The new candidate restores native elbow and forearm targets while fitting upper arm only. Existing right-hand closeups from0.2.8 were partly obscured by the left hand; new diagnostic views isolate the actual right arm. Neither offline geometry nor script-load logs replace runtime visual review.

Validation uses both stock medium_stalker_m and the Jester_f arm mesh corresponding to the observed world player model. The actual predicted first-person proxy was read in game23868 and confirms models/weapons/arms/pov_pilot_light_jester_f.mdl. Config validation_arms points to original extracted meshes and bone JSON. Jester source is models/weapons/arms/pov_pilot_light_jester_f.mdl from englishclient_mp_common.bsp.pak000_dir.vpk, extracted with existing Harmony and CRC verified; use tools/decode_native_pose.ps1 with Names not-an-animation to export its bone data. Those original arm assets are not included in source archives.

## Additive blend checks in0.2.10

`test_attack_blending.py` rejects non-neutral right-arm attack endpoints and large distal sleeve reposing, then checks25 fractional crouch/fire weight combinations across28 hip attack frames. Both source SMD and decoded compiled v53 locals are checked, including actual autoplay mask weight on spineC. The _1/_3 native variants are retained as research inputs, not used as repeated recoil overlays. Original attack descriptor lengths, sequence activities/events and drum policy remain stable. This investigation does not establish legend-specific animation graphs from clip names alone.

## 0.2.11 visual and audio policy

visual_motion.py retains native held grip while applying cosmetic kick on existing spineC. View-forward roll is zero, pitch/translation scale35%,yaw15%; ballistic recoil unchanged. Fifteen walk/run,jump/land and regrip descriptors share this policy, preserving stock roots/camera and table contracts. decode_motion.ps1 decodes all362 motion frames; test_feedback_motion.py checks those plus164 attack frames on two held anchors at four weights,16,832 contact samples. Prior source-matching checks alone missed CAR additive overlays.

First-person shot peak targets are0.65/0.55 instead of0.20. Ten native Apex reload foley/mechanical samples replace existing CAR reload events, preserving engine interrupt timing. Stop-tail and original warning policy remain. Runtime sound-event logging and recorded output are separate from source PCM tests.

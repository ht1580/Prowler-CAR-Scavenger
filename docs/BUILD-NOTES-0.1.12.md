# 0.1.12 build notes — 2026-10-27

Claude handoff: D:\TitanfallMods\02_说明与核对\2026-10-26-Prowler.CAR-交接给Codex.md.

## Problems and changes

1. Audio: the prior build silenced all SecondShot events while depending on the loop overrides. The recorded game log confirmed definitions and samples loaded; it did not prove playback. The stock CAR uses SecondShot per shot. Build now emits three audible Prowler single shots and explicitly disables looping in the minimal weapon patch. One-period 3P/NPC attacks use a separate decay instead of including subsequent loop attacks. Samples are PCM16/48kHz stereo, fmt/data only, with continuous 14.1 rps overlap headroom checked. Low-ammo event retained.
2. World: a +3 model-unit forward translation is composed before the grip matrix. Root/weapon/base and grip-hand IK remain fixed. Meshes, child bones, support-hand IK and muzzle move together. The new translation is removed from the intermediate Pro Screen shift because its mesh subsequently passes through the full transform.
3. First person: 33 original delta animations became absolute animation descriptors in SFM v49, before MDLShit conversion. Example: idle_anim_autoplay stock flags 0x5, 0.1.11 flags 0x1. A delta flag on a sequence alone did not preserve its underlying animation encoding. SFM rejects delta inside an $animation declaration; the verified compiler fix rebases raw delta SMDs to the bind pose and then uses subtract "ref" 0. Raw deltas remain unchanged; derived absolute SMDs go under anims/delta_absolute. Spinner blends use the same encoding and an explicit three-bone weightlist, with zero weight on camera/root/hand bones.
4. Compiler gameinfo and output now live under build/sfm_game on D:. Installed SFM assets are read-only search paths. Audio generation is included in build_all.ps1, and actual compiled-animation regressions gate staging.
5. Independent ZIP validation caught stale v49 core lengths in both combined v53 headers. Stock models declare their complete file length. mdl_integrity.py now checks/repairs offset 80 after conversion, without changing any data offset. The rejected pre-fix package and stage are retained under task work/rejected-0.1.12-before-length-fix.

## Verification

- Full build 0.1.12 exited 0.
- WORLD_ANIM_OK, RUI_FIX_OK, SEQ_FIX_OK, MDL_INTEGRITY_OK, DEEP_COMPARE_OK (view/world).
- unittest discover: all six tests pass against staged assets, with ResourceWarning treated as an error.
- Stock-indexed 124 animation descriptors, 97 sequences, attachment/bodygroup/pose tables retain their indices; extras append.
- Before fixes: 23 expected failures on the audio/world checks and 34 expected failures on the shipped animation checks.
- Old 0.1.11 zip hash retained: 72723CCA54F4D6BBF7F9D8C9D8112097863EBC254392F39A597739B7B3313AAA.
- Original sources and source-audio backup: D:\CodexStorage\Workspaces\2026-10-26\s\work\baseline-0.1.11 (87 files with hashes).

No game launch/control, mods management, cfg/startup edits or global memory/Claude skill updates were performed. Game validation remains user-owned; first-person visibility, sound playback and grip fit are not yet verified in game.

## References

- [Northstar sound guide](https://docs.northstar.tf/Modding/guides/tools/soundmodding/): sample format, event naming, directory layout and ns_print_played_sounds.
- [Northstar audio.cpp](https://github.com/R2Northstar/NorthstarLauncher/blob/main/primedev/client/audio.cpp): replaces sample buffers; EnableOnLoopedSounds parsing is commented out. The prior looping failure remains a playback inference, not a documented universal limitation.
- Actual SFM compiler experiments under the task work/ directory establish the DELTA behavior; no reliance on unavailable Valve source/wiki pages.

Rebuild: scripts\build_all.ps1 -Version <new version>. Existing staged versions are never overwritten. Package separately using scripts\package_release.ps1.

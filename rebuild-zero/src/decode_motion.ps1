$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
& "$PSScriptRoot/tools/decode_native_pose.ps1" -ModelPath "$root/build/compiler_game/models/weapons/car101/ptpov_car101_conv.mdl" -OutputPath "$root/build/native-motion.json" -Names @('run_*','walk_*','switch_to_jump*','switch_to_land*','idle_check_anim','idle_check_ads_anim') -AllFrames
if(!$?){throw 'Movement decode failed'}

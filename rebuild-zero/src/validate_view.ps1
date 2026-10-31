# View-only rebuild using existing verified world/material/audio assets.
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$settings=Get-Content "$PSScriptRoot\config.json" -Raw | ConvertFrom-Json
$x86="$env:WINDIR\SysWOW64\WindowsPowerShell\v1.0\powershell.exe"
$python='D:\python\python.exe'
$env:PYTHONIOENCODING='utf-8'
function BlenderStep([string]$name){
 & $settings.blender -b --factory-startup --python-exit-code 1 -P "$PSScriptRoot\$name" *> "$root\reference-structure\023-final-$name.log"
 if($LASTEXITCODE -ne 0){Get-Content "$root\reference-structure\023-final-$name.log" -Tail 20;throw "Failed $name"}
}
BlenderStep 'generate_view.py'
BlenderStep 'generate_world.py'
& "$PSScriptRoot\compile_models.ps1" *> "$root\reference-structure\023-final-compile.log"
if($LASTEXITCODE -ne 0){throw 'Compile failed'}
& $python "$PSScriptRoot\finish_models.py" >> "$root\reference-structure\023-final-compile.log"
if($LASTEXITCODE -ne 0){throw 'Finish failed'}
& $python "$PSScriptRoot\test_rui_native.py"
if($LASTEXITCODE -ne 0){throw 'Native RUI surface regression'}
& $python "$PSScriptRoot\test_finish_idempotent.py"
if($LASTEXITCODE -ne 0){throw 'Repeated finish changed model bytes'}
& $x86 -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\tools\mdl_engine_dump.ps1" -ModelPath "$root\build\compiler_game\models\weapons\car101\ptpov_car101_conv.mdl" -OutputPath "$root\build\engine-view.json"
if($LASTEXITCODE -ne 0){throw 'Bone dump failed'}
& $x86 -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\tools\decode_native_pose.ps1" -ModelPath "$root\build\compiler_game\models\weapons\car101\w_car101_conv.mdl" -OutputPath "$root\build\native-world.json" -Names '*'
if($LASTEXITCODE -ne 0){throw 'World decode failed'}
& $python "$PSScriptRoot\test_delta_defaults.py"
if($LASTEXITCODE -ne 0){throw 'Delta defaults regression'}
foreach($job in @(@{file='native-all.json';names='*';all=$false},@{file='native-idle.json';names='*_autoplay';all=$true},@{file='native-fire.json';names='attack_*';all=$true},@{file='native-view.json';names='@*';all=$false})){
 $a=@('-NoProfile','-ExecutionPolicy','Bypass','-File',"$PSScriptRoot\tools\decode_native_pose.ps1",'-ModelPath',"$root\build\compiler_game\models\weapons\car101\ptpov_car101_conv.mdl",'-OutputPath',"$root\build\$($job.file)",'-Names',$job.names)
 if($job.all){$a+='-AllFrames'}
 & $x86 @a
 if($LASTEXITCODE -ne 0){throw "Decode failed: $($job.file)"}
}
& $x86 -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\tools\decode_native_pose.ps1" -ModelPath "$root\build\compiler_game\models\weapons\car101\ptpov_car101_conv.mdl" -OutputPath "$root\build\native-reload.json" -Names '*reload*' -AllFrames
if($LASTEXITCODE -ne 0){throw 'Reload decoding failed'}
# Decode every frame of every absolute descriptor, including non-inline transitions.
& $x86 -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot/decode_motion.ps1"
if($LASTEXITCODE -ne 0){throw 'Movement decode failed'}
& $x86 -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot/decode_dynamic.ps1"
if($LASTEXITCODE -ne 0){throw 'Full dynamic decode failed'}
BlenderStep 'verify_dynamic.py'
foreach($script in 'verify_compiled.py','verify_firing_grip.py','test_view_placement.py','test_sprint_visibility.py','test_world_screen.py','test_reload_timing.py','test_compiled_reload.py'){BlenderStep $script}
BlenderStep 'test_refinements.py'
BlenderStep 'test_dynamic_integrity.py'
BlenderStep 'test_right_forearm.py'
BlenderStep 'test_attack_blending.py'
BlenderStep 'test_feedback_motion.py'
& $python "$PSScriptRoot/test_material_channels.py"
if($LASTEXITCODE -ne 0){throw 'Original material channels discarded'}
& $python "$PSScriptRoot\test_audio_policy.py"
if($LASTEXITCODE -ne 0){throw 'Audio event policy failed'}
& $python "$PSScriptRoot\audit_animation_order.py"
if($LASTEXITCODE -ne 0){throw 'Animation index/event audit failed'}
& $python "$PSScriptRoot\stage_package.py" --stage-only
if($LASTEXITCODE -ne 0){throw 'Stage failed'}
BlenderStep 'test_motion_policy.py'
& $python "$PSScriptRoot\test_rebuild.py"
if($LASTEXITCODE -ne 0){throw 'Artifact regression'}
& $python "$PSScriptRoot\stage_package.py"
if($LASTEXITCODE -ne 0){throw 'Package failed'}
Write-Output 'VIEW_REBUILD_VERIFIED; actual game acceptance is separate'

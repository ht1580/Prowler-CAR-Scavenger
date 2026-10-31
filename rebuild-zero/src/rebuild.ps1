# Reproducible independent asset build. Does not install, launch the game or edit user CFG files.
param([switch]$Render)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$settings=Get-Content "$PSScriptRoot\config.json" -Raw | ConvertFrom-Json
$utilities=Join-Path $PSScriptRoot 'tools'
$python='D:\python\python.exe'
$blenderPython=Join-Path (Split-Path $settings.blender -Parent) '5.2\python\bin\python.exe'
$x86="$env:WINDIR\SysWOW64\WindowsPowerShell\v1.0\powershell.exe"
$env:TEMP='D:\CodexStorage\Temp';$env:TMP='D:\CodexStorage\Temp';$env:PYTHONUTF8='1';$env:PYTHONIOENCODING='utf-8'
New-Item -ItemType Directory -Force "$taskRoot\build\logs" | Out-Null
function PythonStep([string]$Script,[string]$Exe=$python,[string[]]$Arguments=@()){
 & $Exe "$PSScriptRoot\$Script" @Arguments *> "$taskRoot\build\logs\$Script.log"
 if($LASTEXITCODE -ne 0){throw "Failed $Script"}
}
function BlenderStep([string]$Script){
 & $settings.blender -b --factory-startup --python-exit-code 1 -P "$PSScriptRoot\$Script" *> "$taskRoot\build\logs\$Script.log"
 if($LASTEXITCODE -ne 0){throw "Failed $Script"}
}
PythonStep 'inventory.py'
& $x86 -NoProfile -ExecutionPolicy Bypass -File "$utilities\mdl_engine_dump.ps1" -ModelPath "$($settings.stock_root)\models\weapons\car101\w_car101.mdl" -OutputPath "$taskRoot\stock-world.json"
if($LASTEXITCODE -ne 0){throw 'Stock extraction failed'}
BlenderStep 'generate_view.py'
BlenderStep 'generate_world.py'
& "$PSScriptRoot\compile_models.ps1"
PythonStep 'finish_models.py'
PythonStep 'test_rui_native.py'
PythonStep 'test_finish_idempotent.py'
PythonStep 'test_delta_defaults.py'
PythonStep 'build_materials.py'
PythonStep 'test_material_channels.py'
& $python "$utilities\rpak_segments.py" "$taskRoot\build\materials\paks\prowler_zero.rpak" --fix
if($LASTEXITCODE -ne 0){throw 'RPAK segment check failed'}
PythonStep 'build_audio.py' $blenderPython
PythonStep 'test_audio_policy.py'
$view="$taskRoot\build\compiler_game\models\weapons\car101\ptpov_car101_conv.mdl"
& $x86 -NoProfile -ExecutionPolicy Bypass -File "$utilities\mdl_engine_dump.ps1" -ModelPath $view -OutputPath "$taskRoot\build\engine-view.json"
if($LASTEXITCODE -ne 0){throw 'Bone dump failed'}
& $x86 -NoProfile -ExecutionPolicy Bypass -File "$utilities\decode_native_pose.ps1" -ModelPath $view -OutputPath "$taskRoot\build\native-view.json"
if($LASTEXITCODE -ne 0){throw 'Native decoding failed'}
& $x86 -NoProfile -ExecutionPolicy Bypass -File "$utilities\decode_native_pose.ps1" -ModelPath $view -OutputPath "$taskRoot\build\native-fire.json" -Names 'attack_*' -AllFrames
if($LASTEXITCODE -ne 0){throw 'Firing decoding failed'}
& $x86 -NoProfile -ExecutionPolicy Bypass -File "$utilities\decode_native_pose.ps1" -ModelPath $view -OutputPath "$taskRoot\build\native-idle.json" -Names '*_autoplay' -AllFrames
if($LASTEXITCODE -ne 0){throw 'Idle decoding failed'}
& $x86 -NoProfile -ExecutionPolicy Bypass -File "$utilities\decode_native_pose.ps1" -ModelPath $view -OutputPath "$taskRoot\build\native-reload.json" -Names '*reload*' -AllFrames
if($LASTEXITCODE -ne 0){throw 'Reload decoding failed'}
foreach($job in @(@{path=$view;file='native-all.json'},@{path="$($settings.stock_root)\models\weapons\car101\ptpov_car101.mdl";file='native-stock-all.json'})){
 & $x86 -NoProfile -ExecutionPolicy Bypass -File "$utilities\decode_native_pose.ps1" -ModelPath $job.path -OutputPath "$taskRoot\build\$($job.file)" -Names '*'
 if($LASTEXITCODE -ne 0){throw 'All-layer decoding failed'}
}
foreach($world in @(@{path="$taskRoot\build\compiler_game\models\weapons\car101\w_car101_conv.mdl";file='native-world.json'},@{path="$($settings.stock_root)\models\weapons\car101\w_car101.mdl";file='native-world-original.json'})){
 & $x86 -NoProfile -ExecutionPolicy Bypass -File "$utilities\decode_native_pose.ps1" -ModelPath $world.path -OutputPath "$taskRoot\build\$($world.file)" -Names '*'
 if($LASTEXITCODE -ne 0){throw 'World decoding failed'}
}
# Decode every frame of every absolute descriptor, including non-inline transitions.
& $x86 -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot/decode_motion.ps1"
if($LASTEXITCODE -ne 0){throw 'Movement decode failed'}
& $x86 -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot/decode_dynamic.ps1"
if($LASTEXITCODE -ne 0){throw 'Full dynamic decode failed'}
BlenderStep 'verify_dynamic.py'
BlenderStep 'verify_compiled.py'
BlenderStep 'verify_firing_grip.py'
BlenderStep 'test_view_placement.py'
BlenderStep 'test_sprint_visibility.py'
BlenderStep 'test_world_screen.py'
BlenderStep 'test_reload_timing.py'
BlenderStep 'test_compiled_reload.py'
PythonStep 'audit_animation_order.py'
PythonStep 'stage_package.py' -Arguments @('--stage-only')
BlenderStep 'test_motion_policy.py'
BlenderStep 'test_refinements.py'
BlenderStep 'test_dynamic_integrity.py'
BlenderStep 'test_right_forearm.py'
BlenderStep 'test_attack_blending.py'
BlenderStep 'test_feedback_motion.py'
PythonStep 'test_rebuild.py'
PythonStep 'stage_package.py'
if($Render){
 & $x86 -NoProfile -ExecutionPolicy Bypass -Command "& '$utilities\decode_native_pose.ps1' -ModelPath '$view' -OutputPath '$taskRoot\build\native-visual.json' -AllFrames -Names @('@draw_seq','ads_in_anim','@reload_seq','@reload_empty_seq','@sprint_seq','@draw_onehanded_seq')"
 if($LASTEXITCODE -ne 0){throw 'Visual pose extraction failed'}
 BlenderStep 'render_validation.py'
}
Write-Output 'INDEPENDENT_REBUILD_OK; runtime validation is separate'

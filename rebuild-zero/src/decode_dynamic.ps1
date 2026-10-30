$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$absoluteNames=@((Get-Content "$taskRoot/build/rig.json" -Raw | ConvertFrom-Json).animations.PSObject.Properties | Where-Object {-not $_.Value.delta} | ForEach-Object {$_.Name})
& "$PSScriptRoot/tools/decode_native_pose.ps1" -ModelPath "$taskRoot/build/compiler_game/models/weapons/car101/ptpov_car101_conv.mdl" -OutputPath "$taskRoot/build/native-dynamic.json" -Names $absoluteNames -AllFrames

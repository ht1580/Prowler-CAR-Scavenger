# Prowler -> CAR full build: sources -> StudioMDL -> MDLShit(v53, RUI) -> RePak -> staged mod folder.
# Does not install anything and does not start the game.
param([string]$Version = '0.1.0')
$ErrorActionPreference = 'Stop'
$P = 'D:\TitanfallMods\35_ProwlerCAR'
$Blender = 'E:\SteamLibrary\steamapps\common\Blender\blender.exe'
$BlenderPython = 'E:\SteamLibrary\steamapps\common\Blender\5.2\python\bin\python.exe'
$StudioMdl = 'E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\studiomdl.exe'
$Game = "$P\build\sfm_game"
$Compiled = "$Game\models\weapons\car101"
$MdlShit = 'D:\CodexStorage\Projects\2026-09-08\w-3\work\mdlshit_source\bin\Windows\mdlshit.exe'
$Rui = "$P\stock\stock_car101.rui"
$ModName = 'Prowler.CAR.Scavenger'
$Stage = "$P\release\$ModName-$Version\$ModName"
$Log = "$P\build\logs"
if (Test-Path $Stage) { throw "Refusing to overwrite existing staged version: $Stage (bump -Version)" }
New-Item -ItemType Directory -Force $Log, "$P\build\view\anims", $Game | Out-Null
# Keep compiler outputs on D:, with read-only search paths into the installed SFM assets.
$gameInfo = @'
"GameInfo"
{
    game "Prowler CAR build workspace"
    FileSystem
    {
        SteamAppId 1840
        SearchPaths
        {
            Game "|gameinfo_path|."
            Game "E:/SteamLibrary/steamapps/common/SourceFilmmaker/game/usermod"
            Game "E:/SteamLibrary/steamapps/common/SourceFilmmaker/game/tf"
            Game "E:/SteamLibrary/steamapps/common/SourceFilmmaker/game/hl2"
        }
    }
}
'@
[IO.File]::WriteAllText("$Game\gameinfo.txt", $gameInfo, (New-Object Text.UTF8Encoding($false)))

function Run-Blender($script, [switch]$Factory) {
    $a = @('-b', '--python-exit-code', '1'); if ($Factory) { $a += '--factory-startup' }; $a += @('-P', $script)
    $out = & $Blender @a 2>&1
    $out | Out-File "$Log\$(Split-Path $script -Leaf).log" -Encoding utf8
    if ($LASTEXITCODE -ne 0 -or -not ($out | Select-String '_OK')) { throw "Blender step failed: $script" }
}

# 1) sources
Copy-Item "$P\stock\view\ptpov_car101_anims\*.smd" "$P\build\view\anims\" -Force
Run-Blender "$P\scripts\build_view.py"
# Apex body -> TF2 pilot arms (stock body, IK elbows, gun + hands unchanged); must run before gen_qc
Run-Blender "$P\scripts\retarget_arms.py" -Factory
Run-Blender "$P\scripts\gen_qc.py" -Factory
Run-Blender "$P\scripts\grip_delta.py" -Factory
Run-Blender "$P\scripts\build_world.py"
$ErrorActionPreference = 'Continue'
& $BlenderPython -I "$P\scripts\build_audio.py" *> "$Log\build_audio.log"
$audioExit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($audioExit -ne 0 -or -not (Select-String -Path "$Log\build_audio.log" -Pattern 'AUDIO_OK' -Quiet)) { throw 'Audio build failed' }
$ErrorActionPreference = 'Continue'
& 'D:\python\python.exe' -I "$P\scripts\check_world_anim.py" *> "$Log\world_anim.log"
$ErrorActionPreference = 'Stop'
if (-not (Select-String -Path "$Log\world_anim.log" -Pattern 'WORLD_ANIM_OK' -Quiet)) { throw "world animation root pose differs from stock (see $Log\world_anim.log)" }

# 2) compile + convert
foreach ($m in @(@{qc = "$P\build\view\ptpov_car101.qc"; name = 'ptpov_car101'; rui = $true },
                 @{qc = "$P\build\world\w_car101.qc"; name = 'w_car101'; rui = $false })) {
    Push-Location (Split-Path $m.qc)
    & $StudioMdl -game $Game -nop4 -verbose (Split-Path $m.qc -Leaf) *> "$Log\$($m.name)-studiomdl.log"
    Pop-Location
    if (-not (Select-String -Path "$Log\$($m.name)-studiomdl.log" -Pattern 'Completed' -Quiet)) { throw "StudioMDL failed: $($m.name)" }
    if (Select-String -Path "$Log\$($m.name)-studiomdl.log" -Pattern '^ERROR' -Quiet) { throw "StudioMDL errors: $($m.name)" }
    Copy-Item "$Compiled\$($m.name).dx90.vtx" "$Compiled\$($m.name).vtx" -Force
    $msArgs = "--noui `"$Compiled\$($m.name).mdl`""
    if ($m.rui) { $msArgs += " `"$Rui`"" }
    $proc = Start-Process $MdlShit -ArgumentList $msArgs -WindowStyle Hidden -Wait -PassThru `
        -RedirectStandardOutput "$Log\$($m.name)-mdlshit.log" -RedirectStandardError "$Log\$($m.name)-mdlshit.err"
    if ($proc.ExitCode -ne 0) { throw "MDLShit failed: $($m.name)" }
}
$ErrorActionPreference = 'Continue'
& 'D:\python\python.exe' -I "$P\scripts\rui_fix.py" "$Compiled\ptpov_car101_conv.mdl" *> "$Log\rui_fix.log"
if (-not (Select-String -Path "$Log\rui_fix.log" -Pattern 'RUI_FIX_OK' -Quiet)) { throw 'RUI fix failed' }
# seq flags/bboxes back to the stock CAR values (the compile chain rewrites idle "noanimation" 0x80000 -> 0x100000)
& 'D:\python\python.exe' -I "$P\scripts\seq_fix.py" "$P\stock\models\weapons\car101\ptpov_car101.mdl" "$Compiled\ptpov_car101_conv.mdl" *> "$Log\seq_fix.log"
if (-not (Select-String -Path "$Log\seq_fix.log" -Pattern 'SEQ_FIX_OK' -Quiet)) { throw "seq fix failed (see $Log\seq_fix.log)" }
& 'D:\python\python.exe' -I "$P\scripts\mdl_integrity.py" "$Compiled\ptpov_car101_conv.mdl" "$Compiled\w_car101_conv.mdl" --fix-length *> "$Log\mdl_integrity.log"
if ($LASTEXITCODE -ne 0 -or -not (Select-String -Path "$Log\mdl_integrity.log" -Pattern 'MDL_INTEGRITY_OK' -Quiet)) { throw 'Combined MDL integrity check failed' }
# index-sensitive tables (sequences / attachments / bodyparts) must match the stock CAR prefix-for-prefix
foreach ($n in 'ptpov_car101', 'w_car101') {
    & 'D:\python\python.exe' -I "$P\scripts\mdl_deep_compare.py" "$P\stock\models\weapons\car101\$n.mdl" "$Compiled\${n}_conv.mdl" *> "$Log\$n-compare.log"
    if (-not (Select-String -Path "$Log\$n-compare.log" -Pattern 'DEEP_COMPARE_OK' -Quiet)) { throw "Index tables differ from stock: $n (see $Log\$n-compare.log)" }
}
# Verify the actual compiled DELTA payloads and the spinner's bone mask.
$env:PROWLER_VIEW_MDL = "$Compiled\ptpov_car101_conv.mdl"
$env:PROWLER_WORLD_MDL = "$Compiled\w_car101_conv.mdl"
$env:PROWLER_STAGE = "$P\mod_src"
foreach ($nativeModel in @(@{name='ptpov_car101'; json='native-view'; env='PROWLER_NATIVE_POSES'},
                          @{name='w_car101'; json='native-world'; env='PROWLER_NATIVE_WORLD'})) {
    & "$env:WINDIR\SysWOW64\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass `
        -File "$P\scripts\decode_native_pose.ps1" -ModelPath "$Compiled\$($nativeModel.name)_conv.mdl" `
        -OutputPath "$P\build\$($nativeModel.json).json" *> "$Log\$($nativeModel.json).log"
    if ($LASTEXITCODE -ne 0 -or -not (Select-String -LiteralPath "$Log\$($nativeModel.json).log" -Pattern 'NATIVE_POSES_OK' -Quiet)) { throw 'Native pose decoding failed' }
    [Environment]::SetEnvironmentVariable($nativeModel.env, "$P\build\$($nativeModel.json).json", 'Process')
}
# every animation (all decoded descriptors) must keep the reactive drum parts seated on the gun
& "$env:WINDIR\SysWOW64\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass `
    -File "$P\scripts\decode_native_pose.ps1" -ModelPath "$Compiled\ptpov_car101_conv.mdl" `
    -OutputPath "$P\build\native-view-all.json" -Names '*' *> "$Log\native-view-all.log"
& $BlenderPython -I "$P\scripts\check_drum_seat.py" "$P\build\native-view-all.json" *> "$Log\drum_seat.log"
if (-not (Select-String -LiteralPath "$Log\drum_seat.log" -Pattern 'DRUM_SEAT_OK' -Quiet)) { throw "drum parts leave their seat (see $Log\drum_seat.log)" }
Push-Location $P
& $BlenderPython -m unittest discover -s tests -v *> "$Log\regressions.log"
$testExit = $LASTEXITCODE
Pop-Location
if ($testExit -ne 0) { throw "Artifact regression failed (see $Log\regressions.log)" }
$ErrorActionPreference = 'Stop'

# 3) materials
$ErrorActionPreference = 'Continue'
& 'D:\python\python.exe' "$P\scripts\build_rpak.py" *> "$Log\build_rpak.log"
if ($LASTEXITCODE -ne 0) { throw 'RePak build failed' }
& 'D:\python\python.exe' -I "$P\scripts\rpak_segments.py" "$P\repak\build\prowler_car.rpak" --fix *> "$Log\rpak_segments.log"
$ErrorActionPreference = 'Stop'

# 4) stage mod
if (Test-Path $Stage) { throw "Refusing to overwrite existing staged version: $Stage (bump -Version)" }
New-Item -ItemType Directory -Force "$Stage\mod\models\weapons\car101", "$Stage\paks" | Out-Null
Copy-Item "$Compiled\ptpov_car101_conv.mdl" "$Stage\mod\models\weapons\car101\ptpov_car101.mdl"
Copy-Item "$Compiled\w_car101_conv.mdl" "$Stage\mod\models\weapons\car101\w_car101.mdl"
# models replace the stock car101 paths only (same as published Apex ports); the mod's minimal
# mp_weapon_car keyvalues pins viewmodel/playermodel/holstermodel to these same stock paths
Copy-Item "$P\repak\build\prowler_car.rpak", "$P\repak\build\prowler_car.starpak" "$Stage\paks\"
'{ "Postload": { "prowler_car.rpak": "common.rpak" } }' | Set-Content "$Stage\paks\rpak.json" -Encoding ascii
if (Test-Path "$P\mod_src") { Copy-Item "$P\mod_src\*" $Stage -Recurse -Force }
# NOTE: PowerShell 5.1 "Set-Content -Encoding utf8" writes a BOM, and Northstar then rejects mod.json
# ("parse error Invalid value at offset 0") and silently skips the whole mod -> write BOM-less UTF-8.
$modJson = (Get-Content "$Stage\mod.json" -Raw) -replace '"Version": "[^"]*"', "`"Version`": `"$Version`""
[IO.File]::WriteAllText("$Stage\mod.json", $modJson, (New-Object Text.UTF8Encoding($false)))
$bom = Get-ChildItem $Stage -Recurse -File -Include *.json, *.txt, *.nut, *.gnut | Where-Object {
    $b = [IO.File]::ReadAllBytes($_.FullName); $b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF }
if ($bom) { throw "UTF-8 BOM in packaged text files (Northstar rejects them): $($bom.FullName -join ', ')" }
Write-Host "STAGED $Stage"



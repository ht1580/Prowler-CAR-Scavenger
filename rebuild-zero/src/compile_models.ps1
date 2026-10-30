param([switch]$ViewOnly,[switch]$WorldOnly)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$settings=Get-Content "$PSScriptRoot\config.json" -Raw | ConvertFrom-Json
$game="$taskRoot\build\compiler_game"
$logs="$taskRoot\build\logs"
New-Item -ItemType Directory -Force $game,$logs | Out-Null
$gameInfo=@'
"GameInfo"
{
 game "Prowler independent rebuild"
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
[IO.File]::WriteAllText("$game\gameinfo.txt",$gameInfo)
$models=@(@{folder='view';name='ptpov_car101';rui=$true})
if(-not $ViewOnly){$models+=@{folder='world';name='w_car101';rui=$false}}
if($WorldOnly){$models=@(@{folder='world';name='w_car101';rui=$false})}
foreach($model in $models){
 Push-Location "$taskRoot\build\$($model.folder)"
 try { & $settings.studio_mdl -game $game -nop4 -verbose "$($model.name).qc" *> "$logs\$($model.name)-compiler.log"; $compileExit=$LASTEXITCODE } finally {Pop-Location}
 if($compileExit -ne 0 -or -not (Select-String -Path "$logs\$($model.name)-compiler.log" -Pattern 'Completed' -Quiet)){throw "Compiler failed: $($model.name)"}
 $mdl="$game\models\weapons\car101\$($model.name).mdl"
 Copy-Item ($mdl -replace '\.mdl$','.dx90.vtx') ($mdl -replace '\.mdl$','.vtx') -Force
 $arguments="--noui `"$mdl`""
 if($model.rui){$arguments+=" `"$($settings.stock_root)\stock_car101.rui`""}
 $process=Start-Process $settings.mdl_converter -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput "$logs\$($model.name)-convert.log" -RedirectStandardError "$logs\$($model.name)-convert.err"
 if($process.ExitCode -ne 0){throw "Converter failed: $($model.name)"}
}
Write-Output 'MODELS_COMPILED_OK'

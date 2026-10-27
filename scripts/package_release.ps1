param([string]$Version = '0.1.12')
$ErrorActionPreference = 'Stop'
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw 'Version must be x.y.z' }
$project = 'D:\TitanfallMods\35_ProwlerCAR'
$modName = 'Prowler.CAR.Scavenger'
$stage = Join-Path $project "release\$modName-$Version\$modName"
$archive = "D:\TitanfallMods\01_最新安装包\$modName-$Version.zip"
if (-not (Test-Path -LiteralPath "$stage\mod.json")) { throw 'Staged mod.json missing' }
if (Test-Path -LiteralPath $archive) { throw "Refusing to overwrite $archive" }
$manifest = Get-Content -LiteralPath "$stage\mod.json" -Raw | ConvertFrom-Json
if ($manifest.Version -ne $Version -or $manifest.LoadPriority -ne 0) { throw 'Staged manifest mismatch' }
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::Open($archive, [IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($file in (Get-ChildItem -LiteralPath $stage -Recurse -File | Sort-Object FullName)) {
        $relative = $file.FullName.Substring($stage.Length + 1).Replace('\', '/')
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $file.FullName, "$modName/$relative", [IO.Compression.CompressionLevel]::Optimal) | Out-Null
    }
} finally {
    $zip.Dispose()
}
Get-FileHash -LiteralPath $archive -Algorithm SHA256 | Select-Object Path, Hash
Write-Host "PACKAGE_OK $archive"

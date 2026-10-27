$a=[Reflection.Assembly]::LoadFrom('D:\CodexStorage\Projects\2026-09-08\w-3\work\tools\Crowbar_0.74\Crowbar.exe')
$t=$a.GetType('Crowbar.SourceMdlBone53',$false); if(-not $t){ $a.GetTypes() | Where-Object { $_.Name -match 'Bone' } | ForEach-Object { $_.FullName } } else { $t.GetFields() | ForEach-Object { "$($_.Name) : $($_.FieldType.Name)" } }

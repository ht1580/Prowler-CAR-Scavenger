param([string]$ModelPath)
$a=[Reflection.Assembly]::LoadFrom('D:\CodexStorage\Projects\2026-09-08\w-3\work\tools\Crowbar_0.74\Crowbar.exe')
$dt=$a.GetType('Crowbar.SourceMdlFileData53',$true); $rt=$a.GetType('Crowbar.SourceMdlFile53',$true); $d=[Activator]::CreateInstance($dt)
$s=[IO.File]::OpenRead($ModelPath); $br=New-Object IO.BinaryReader($s)
$r=$rt.GetConstructor([type[]]@([IO.BinaryReader],$dt)).Invoke([object[]]@($br.PSObject.BaseObject,$d.PSObject.BaseObject)); $r.ReadMdlHeader00(''); $r.ReadMdlHeader01(''); $r.ReadBones(); $r.ReadLocalAnimationDescs(); $r.ReadSequenceDescs()
$names = @($d.theSequenceDescs | ForEach-Object { $_.theName })
$i=0; foreach($q in $d.theSequenceDescs){ if ($q.theAutoLayers -and $q.theAutoLayers.Count -gt 0) { $ls = @($q.theAutoLayers | ForEach-Object { $n = if ($_.sequenceIndex -ge 0 -and $_.sequenceIndex -lt $names.Count) { $names[$_.sequenceIndex] } else { $_.sequenceIndex }; "$n(flags $($_.flags) start $($_.start) peak $($_.peak) tail $($_.tail) end $($_.end))" }) -join '; '; "{0,-32} -> {1}" -f $q.theName, $ls }; $i++ }
$s.Dispose()

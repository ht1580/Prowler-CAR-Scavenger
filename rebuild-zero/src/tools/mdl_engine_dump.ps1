# Run with 32-bit PowerShell (Crowbar is x86): dumps the engine-side data of a v53 MDL that animation
# decoding does not show: header counts (IK chains, include models, bone controllers, autoplay locks),
# per-bone flags / procedural type / parent, so stock and ported models can be compared bone by bone.
param([string]$ModelPath, [string]$OutputPath)
$ErrorActionPreference = 'Stop'
$assembly = [Reflection.Assembly]::LoadFrom('D:\CodexStorage\Projects\2026-09-08\w-3\work\tools\Crowbar_0.74\Crowbar.exe')
$dataType = $assembly.GetType('Crowbar.SourceMdlFileData53', $true)
$readerType = $assembly.GetType('Crowbar.SourceMdlFile53', $true)
$data = [Activator]::CreateInstance($dataType)
$stream = [IO.File]::OpenRead($ModelPath)
try {
    $binary = New-Object IO.BinaryReader($stream)
    $reader = $readerType.GetConstructor([type[]]@([IO.BinaryReader], $dataType)).Invoke([object[]]@($binary.PSObject.BaseObject, $data.PSObject.BaseObject))
    $reader.ReadMdlHeader00('')
    $reader.ReadMdlHeader01('')
    $reader.ReadBones()
    $out = [ordered]@{}
    foreach ($f in $dataType.GetFields()) {
        $n = $f.Name
        if ($n -match '(?i)(count|flags)$' -and $f.FieldType.IsPrimitive) { $out[$n] = $f.GetValue($data.PSObject.BaseObject) }
    }
    $bones = @()
    foreach ($b in $data.theBones) {
        $v = { param($s) @($s.x, $s.y, $s.z) }
        $row = [ordered]@{ name = $b.theName; parent = $b.parentBoneIndex; flags = $b.flags; procType = $b.proceduralRuleType;
                           procOffset = $b.proceduralRuleOffset; contents = $b.contents; physicsBone = $b.physicsBoneIndex;
                           pos = (& $v $b.position); quat = @($b.quat.x, $b.quat.y, $b.quat.z, $b.quat.w); rot = (& $v $b.rotation);
                           posScale = (& $v $b.positionScale); rotScale = (& $v $b.rotationScale);
                           p2b = @((& $v $b.poseToBoneColumn0), (& $v $b.poseToBoneColumn1), (& $v $b.poseToBoneColumn2), (& $v $b.poseToBoneColumn3)) }
        $bones += $row
    }
    $out['bones'] = $bones
    [IO.File]::WriteAllText($OutputPath, ($out | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding($false)))
    'MDL_ENGINE_DUMP_OK ' + $data.theBones.Count + ' bones'
} finally { $stream.Dispose() }

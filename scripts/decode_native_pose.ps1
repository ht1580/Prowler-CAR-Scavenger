param([string]$ModelPath,[string]$OutputPath,[switch]$AllFrames,[string[]]$Names)
$ErrorActionPreference='Stop'
$assembly=[Reflection.Assembly]::LoadFrom('D:\CodexStorage\Projects\2026-09-08\w-3\work\tools\Crowbar_0.74\Crowbar.exe')
$dataType=$assembly.GetType('Crowbar.SourceMdlFileData53',$true)
$readerType=$assembly.GetType('Crowbar.SourceMdlFile53',$true)
$writerType=$assembly.GetType('Crowbar.SourceSmdFile53',$true)
$data=[Activator]::CreateInstance($dataType)
$stream=[IO.File]::OpenRead($ModelPath)
try {
    $binary=New-Object IO.BinaryReader($stream)
    $reader=$readerType.GetConstructor([type[]]@([IO.BinaryReader],$dataType)).Invoke([object[]]@($binary.PSObject.BaseObject,$data.PSObject.BaseObject))
    $reader.ReadMdlHeader00('')
    $reader.ReadMdlHeader01('')
    $reader.ReadBones()
    $reader.ReadLocalAnimationDescs()
    $reader.ReadAnimationSections()
    $reader.ReadAnimationMdlBlocks()
    $reader.ReadSequenceDescs()
    $buffer=New-Object IO.MemoryStream
    $textWriter=New-Object IO.StreamWriter($buffer)
    $writer=$writerType.GetConstructor([type[]]@([IO.StreamWriter],$dataType)).Invoke([object[]]@($textWriter.PSObject.BaseObject,$data.PSObject.BaseObject))
    $private=[Reflection.BindingFlags]'NonPublic,Instance'
    $frameField=$writerType.GetField('theAnimationFrameLines',$private)
    $calc=$writerType.GetMethod('CalcAnimation',$private)
    $bones=@($data.theBones | ForEach-Object {
        @{name=$_.theName;parent=$_.parentBoneIndex;pos=@($_.position.x,$_.position.y,$_.position.z);rot=@($_.rotation.x,$_.rotation.y,$_.rotation.z)}
    })
    $poses=@()
    $index=0
    foreach($anim in $data.theAnimationDescs) {
        $wanted = if($Names){ $Names } else { @('@ref','@draw_seq','idle_anim_autoplay','idle_ads_anim_autoplay','ads_in_anim','@reload_seq','attack_anim','attack_ads_anim','attack_slide_anim','attack_onehanded_anim','attack_onehanded_ads_anim','@idle_seq','@attack_seq','@attack_seq_alt1','@attack_seq_alt2') }
        if($wanted[0] -ne '*' -and $anim.theName -notin $wanted){ $index++;continue }
        $frames=@(0,[int][Math]::Floor(($anim.frameCount-1)/2),[int]($anim.frameCount-1)) | Select-Object -Unique
        if($AllFrames){ $frames=0..([int]$anim.frameCount-1) }
        foreach($frame in $frames) {
            $dict=[Activator]::CreateInstance($frameField.FieldType)
            $frameField.SetValue($writer.PSObject.BaseObject,$dict.PSObject.BaseObject)
            $calc.Invoke($writer.PSObject.BaseObject,[object[]]@($null,$anim.PSObject.BaseObject,[int]$frame)) | Out-Null
            $locals=@()
            for($k=0;$k -lt $data.theBones.Count;$k++) {
                if($dict.ContainsKey($k)) {
                    $line=$dict[$k]
                    $locals+=@{index=$k;pos=@($line.position.x,$line.position.y,$line.position.z);rot=@($line.rotation.x,$line.rotation.y,$line.rotation.z)}
                }
            }
            $poses+=@{name=$anim.theName;index=$index;frame=$frame;frames=$anim.frameCount;flags=$anim.flags;locals=$locals}
        }
        $index++
    }
    $result=@{model=$ModelPath;bone_count=$data.theBones.Count;animation_count=$data.theAnimationDescs.Count;bones=$bones;poses=$poses}
    [IO.File]::WriteAllText($OutputPath,($result | ConvertTo-Json -Depth 10),(New-Object Text.UTF8Encoding($false)))
    'NATIVE_POSES_OK bones='+$data.theBones.Count+' animations='+$data.theAnimationDescs.Count+' poses='+$poses.Count
} finally {
    $stream.Dispose()
}

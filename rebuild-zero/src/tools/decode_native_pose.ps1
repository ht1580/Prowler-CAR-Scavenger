param([string]$ModelPath,[string]$OutputPath,[switch]$AllFrames,[string[]]$Names)
$ErrorActionPreference='Stop'
$assembly=[Reflection.Assembly]::LoadFrom('D:\CodexStorage\Projects\2026-09-08\w-3\work\tools\Crowbar_0.74\Crowbar.exe')
$dataType=$assembly.GetType('Crowbar.SourceMdlFileData53',$true)
$readerType=$assembly.GetType('Crowbar.SourceMdlFile53',$true)
$writerType=$assembly.GetType('Crowbar.SourceSmdFile53',$true)
$modelBytes=[IO.File]::ReadAllBytes($ModelPath)
$deltaAnimations=New-Object 'Collections.Generic.HashSet[int]'
$sequenceCount=[BitConverter]::ToInt32($modelBytes,192)
$sequenceStart=[BitConverter]::ToInt32($modelBytes,196)
for($si=0;$si -lt $sequenceCount;$si++){
    $sr=$sequenceStart+232*$si
    if(([BitConverter]::ToInt32($modelBytes,$sr+12) -band 4) -eq 0){continue}
    $table=$sr+[BitConverter]::ToInt32($modelBytes,$sr+60)
    $blends=[BitConverter]::ToInt32($modelBytes,$sr+68)*[BitConverter]::ToInt32($modelBytes,$sr+72)
    for($bi=0;$bi -lt $blends;$bi++){$deltaAnimations.Add([int][BitConverter]::ToInt16($modelBytes,$table+2*$bi)) | Out-Null}
}
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
    $reader.ReadAnimationMdlBlocks() # Fail explicitly; never report default bind poses as decoded animation.
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
        $matchesName = @($wanted | Where-Object { $anim.theName -like $_ }).Count -gt 0
        if(-not $matchesName){ $index++;continue }
        $frames=@(0,[int][Math]::Floor(($anim.frameCount-1)/2),[int]($anim.frameCount-1)) | Select-Object -Unique
        if($AllFrames){ $frames=0..([int]$anim.frameCount-1) }
        foreach($frame in $frames) {
            $dict=[Activator]::CreateInstance($frameField.FieldType)
            $frameField.SetValue($writer.PSObject.BaseObject,$dict.PSObject.BaseObject)
            $calc.Invoke($writer.PSObject.BaseObject,[object[]]@($null,$anim.PSObject.BaseObject,[int]$frame)) | Out-Null
            # Crowbar 0.74 CalcBonePosition unconditionally substitutes ZERO for
            # RAWPOS+DELTA. The engine reads the stored Vector48 unchanged.
            # Restore these raw values so corrupt converter defaults cannot hide
            # behind apparently correct zero translations in offline checks.
            $rawPositions=@{}
            $sectionIndex=if($anim.sectionFrameCount -gt 0){[int][Math]::Floor($frame/$anim.sectionFrameCount)}else{0}
            if($anim.theSectionsOfAnimations -and $sectionIndex -lt $anim.theSectionsOfAnimations.Count){
                foreach($track in $anim.theSectionsOfAnimations[$sectionIndex]){
                    if(($track.flags -band 2) -ne 0){
                        $rawPositions[[int]$track.boneIndex]=@($track.PosX.TheFloatValue,$track.PosY.TheFloatValue,$track.PosZ.TheFloatValue)
                    }
                }
            }
            $locals=@()
            for($k=0;$k -lt $data.theBones.Count;$k++) {
                if($dict.ContainsKey($k)) {
                    $line=$dict[$k]
                    $position=if($rawPositions.ContainsKey($k)){$rawPositions[$k]}else{@($line.position.x,$line.position.y,$line.position.z)}
                    $locals+=@{index=$k;pos=@($position);rot=@($line.rotation.x,$line.rotation.y,$line.rotation.z)}
                }
            }
            $poses+=@{name=$anim.theName;index=$index;frame=$frame;frames=$anim.frameCount;flags=$anim.flags;delta_sequence=$deltaAnimations.Contains($index);locals=$locals}
        }
        $index++
    }
    $result=@{model=$ModelPath;source_sha256=(Get-FileHash -LiteralPath $ModelPath -Algorithm SHA256).Hash.ToLowerInvariant();bone_count=$data.theBones.Count;animation_count=$data.theAnimationDescs.Count;bones=$bones;poses=$poses}
    [IO.File]::WriteAllText($OutputPath,($result | ConvertTo-Json -Depth 10),(New-Object Text.UTF8Encoding($false)))
    'NATIVE_POSES_OK bones='+$data.theBones.Count+' animations='+$data.theAnimationDescs.Count+' poses='+$poses.Count
} finally {
    $stream.Dispose()
}

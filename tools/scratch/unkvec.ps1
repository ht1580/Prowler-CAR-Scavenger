param([string]$ModelPath)
$a=[Reflection.Assembly]::LoadFrom('D:\CodexStorage\Projects\2026-09-08\w-3\work\tools\Crowbar_0.74\Crowbar.exe')
$dt=$a.GetType('Crowbar.SourceMdlFileData53',$true); $rt=$a.GetType('Crowbar.SourceMdlFile53',$true); $d=[Activator]::CreateInstance($dt)
$s=[IO.File]::OpenRead($ModelPath); $br=New-Object IO.BinaryReader($s)
$r=$rt.GetConstructor([type[]]@([IO.BinaryReader],$dt)).Invoke([object[]]@($br.PSObject.BaseObject,$d.PSObject.BaseObject)); $r.ReadMdlHeader00(''); $r.ReadMdlHeader01(''); $r.ReadBones()
$f = { param($v) '({0:0.###},{1:0.###},{2:0.###})' -f $v.x,$v.y,$v.z }
foreach($b in $d.theBones){ if($b.theName -match 'jx_c_delta|def_c_base|weapon_bone|def_l_wrist|def_l_elbow|def_c_hip|spinner_coils|spinner_1|reactive_tube_top|def_c_bolt$|ja_c_propGun|def_l_shoulder$') { '{0,-30} unk {1,-22} posScale {2,-26} rotScale {3,-30} unk1 {4}' -f $b.theName,(& $f $b.unkVector),(& $f $b.positionScale),(& $f $b.rotationScale),(& $f $b.unkVector1) } }
$s.Dispose()

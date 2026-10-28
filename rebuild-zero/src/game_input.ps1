param([string]$Text,[int]$KeyCode=0,[switch]$ToggleConsole)
$ErrorActionPreference='Stop'
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class ProwlerGameInput {
 [StructLayout(LayoutKind.Sequential)] public struct KEYBDINPUT {public ushort vk;public ushort scan;public uint flags;public uint time;public UIntPtr extra;}
 [StructLayout(LayoutKind.Explicit,Size=32)] public struct UNION{[FieldOffset(0)] public KEYBDINPUT key;}
 [StructLayout(LayoutKind.Sequential)] public struct INPUT{public uint type;public UNION data;}
 [DllImport("user32.dll")] public static extern uint SendInput(uint count,INPUT[] input,int size);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 public static void Key(ushort vk){var a=new INPUT[2];a[0].type=a[1].type=1;a[0].data.key.vk=a[1].data.key.vk=vk;a[1].data.key.flags=2;SendInput(2,a,Marshal.SizeOf(typeof(INPUT)));}
 public static void Text(string text){foreach(char c in text){var a=new INPUT[2];a[0].type=a[1].type=1;a[0].data.key.scan=a[1].data.key.scan=c;a[0].data.key.flags=4;a[1].data.key.flags=6;SendInput(2,a,Marshal.SizeOf(typeof(INPUT)));}}
}
'@
$testPid=[int](Get-Content (Join-Path (Split-Path $PSScriptRoot -Parent) 'current-test-pid.txt'))
$game=Get-Process -Id $testPid
if($game.MainWindowTitle -ne 'Titanfall 2' -or [ProwlerGameInput]::GetForegroundWindow() -ne $game.MainWindowHandle){throw 'Only the foreground diagnostic game may receive input'}
if($ToggleConsole){[ProwlerGameInput]::Key(192);Start-Sleep -Milliseconds 250}
if($Text){[ProwlerGameInput]::Text($Text);[ProwlerGameInput]::Key(13)}
if($KeyCode){[ProwlerGameInput]::Key([ushort]$KeyCode)}
Write-Output 'TEST_GAME_INPUT_SENT'
